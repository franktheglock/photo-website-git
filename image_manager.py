import os
import sqlite3
from PIL import Image
from datetime import datetime
import glob

class ImageManager:
    def __init__(self, db_path="gallery.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Define directory structure
        self.dirs = {
            'sports': {
                'basketball': {
                    'full': 'images/sports/basketball/full',
                    'thumb': 'images/sports/basketball/thumb'
                },
                'football': {
                    'full': 'images/sports/football/full',
                    'thumb': 'images/sports/football/thumb'
                }
            },
            'events': {
                'full': 'images/events/full',
                'thumb': 'images/events/thumb'
            }
        }
        
        self._create_directories()

        # Scan for existing images if database is empty
        self.scan_existing_images()

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Drop existing table if it exists
            cursor.execute('DROP TABLE IF EXISTS images')
            
            # Create new table with updated schema
            cursor.execute('''
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    main_category TEXT NOT NULL,
                    sub_category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def _create_directories(self):
        for sport in self.dirs['sports']:
            for dir_type in ['full', 'thumb']:
                os.makedirs(self.dirs['sports'][sport][dir_type], exist_ok=True)
        
        for dir_type in ['full', 'thumb']:
            os.makedirs(self.dirs['events'][dir_type], exist_ok=True)

    def scan_existing_images(self):
        # Check if database is empty
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM images")
            if cursor.fetchone()[0] > 0:
                return  # Database already has entries
        
        # Scan sports directories
        for sport in ['basketball', 'football']:
            full_path = f"images/sports/{sport}/full"
            if os.path.exists(full_path):
                for img_path in glob.glob(os.path.join(full_path, "*")):
                    filename = os.path.basename(img_path)
                    # Skip if thumbnail doesn't exist
                    thumb_path = os.path.join(f"images/sports/{sport}/thumb", filename)
                    if not os.path.exists(thumb_path):
                        continue
                    
                    # Add to database
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO images (filename, main_category, sub_category, title) VALUES (?, ?, ?, ?)",
                            (filename, 'sports', sport, os.path.splitext(filename)[0])
                        )

        # Scan events directory
        events_path = "images/events/full"
        if os.path.exists(events_path):
            for img_path in glob.glob(os.path.join(events_path, "*")):
                filename = os.path.basename(img_path)
                # Skip if thumbnail doesn't exist
                thumb_path = os.path.join("images/events/thumb", filename)
                if not os.path.exists(thumb_path):
                    continue
                
                # Add to database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO images (filename, main_category, sub_category, title) VALUES (?, ?, ?, ?)",
                        (filename, 'events', 'general', os.path.splitext(filename)[0])
                    )

    def add_image(self, image_path, main_category, sub_category, title, quality=85):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{os.path.basename(image_path)}"
        
        # Get correct paths based on category
        if main_category == 'sports':
            full_path = os.path.join(self.dirs['sports'][sub_category]['full'], filename)
            thumb_path = os.path.join(self.dirs['sports'][sub_category]['thumb'], filename)
        else:
            full_path = os.path.join(self.dirs['events']['full'], filename)
            thumb_path = os.path.join(self.dirs['events']['thumb'], filename)

        # Process and save images
        self.compress_image(image_path, full_path, quality)
        self.compress_image(image_path, thumb_path, quality, is_thumb=True)
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO images (filename, main_category, sub_category, title) VALUES (?, ?, ?, ?)",
                (filename, main_category, sub_category, title)
            )
        
        self.update_gallery_html(main_category)

    def compress_image(self, image_path, output_path, quality, is_thumb=False):
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            if is_thumb:
                img.thumbnail((300, 300))
            
            img.save(output_path, 'JPEG', quality=quality, optimize=True)

    def get_save_paths(self, main_category, sub_category):
        if main_category == 'sports':
            return (
                self.dirs['sports'][sub_category]['full'],
                self.dirs['sports'][sub_category]['thumb']
            )
        else:  # events
            return (
                self.dirs['events']['full'],
                self.dirs['events']['thumb']
            )

    def update_gallery_html(self, main_category):
        template_file = f"{main_category}.html"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            images = cursor.execute("""
                SELECT filename, sub_category, title 
                FROM images 
                WHERE main_category = ?
                ORDER BY date_added DESC
            """, (main_category,)).fetchall()

        gallery_html = []
        for image in images:
            filename, category, title = image
            if main_category == 'sports':
                full_path = f"images/sports/{category}/full/{filename}"
                thumb_path = f"images/sports/{category}/thumb/{filename}"
                gallery_html.append(f'''
                    <a href="{full_path}" data-lightbox="sports" data-title="{title}">
                        <img src="{thumb_path}" alt="{title}" data-category="{category}">
                    </a>'''.strip())
            else:  # events
                full_path = f"images/events/full/{filename}"
                thumb_path = f"images/events/thumb/{filename}"
                gallery_html.append(f'''
                    <a href="{full_path}" data-lightbox="events" data-title="{title}">
                        <img src="{thumb_path}" alt="{title}" data-category="{category}">
                    </a>'''.strip())

        try:
            # Read existing HTML file
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the gallery div
            start_marker = '<div class="grid">'
            end_marker = '</div>'
            
            start_idx = content.find(start_marker) + len(start_marker)
            remaining_content = content[start_idx:]
            end_idx = start_idx + remaining_content.find(end_marker)
            
            # Create new content with proper indentation
            new_content = (
                content[:start_idx] + 
                '\n                ' +  # Proper indentation
                '\n                '.join(gallery_html) + 
                '\n            ' +  # Proper closing indentation
                content[end_idx:]
            )

            # Write updated HTML
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        except Exception as e:
            print(f"Error updating gallery HTML: {e}")

    def get_images(self, main_category=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if (main_category and main_category != "all"):
                cursor.execute("""
                    SELECT id, filename, main_category, sub_category, title 
                    FROM images 
                    WHERE main_category = ?
                    ORDER BY date_added DESC
                """, (main_category,))
            else:
                cursor.execute("""
                    SELECT id, filename, main_category, sub_category, title 
                    FROM images 
                    ORDER BY date_added DESC
                """)
            return cursor.fetchall()

    def delete_image(self, image_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get image info before deleting
            cursor.execute("""
                SELECT filename, main_category, sub_category 
                FROM images 
                WHERE id = ?
            """, (image_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            filename, main_category, sub_category = result

            # Delete file paths
            if main_category == 'sports':
                full_path = os.path.join(self.dirs['sports'][sub_category]['full'], filename)
                thumb_path = os.path.join(self.dirs['sports'][sub_category]['thumb'], filename)
            else:
                full_path = os.path.join(self.dirs['events']['full'], filename)
                thumb_path = os.path.join(self.dirs['events']['thumb'], filename)

            # Delete physical files
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except OSError as e:
                print(f"Error deleting files: {e}")

            # Delete from database
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            
            # Update the HTML file
            template_file = f"{main_category}.html"
            
            # Get remaining images for this category
            images = cursor.execute("""
                SELECT filename, sub_category, title 
                FROM images 
                WHERE main_category = ?
                ORDER BY date_added DESC
            """, (main_category,)).fetchall()

            # Read the HTML file
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Use correct markers for the gallery div
                start_marker = '<div class="grid">'
                end_marker = '</div>'
                
                start_idx = content.find(start_marker) + len(start_marker)
                remaining_content = content[start_idx:]
                end_idx = start_idx + remaining_content.find(end_marker)

                # Generate HTML for remaining images
                gallery_html = []
                for img in images:
                    filename, category, title = img
                    if main_category == 'sports':
                        full_path = f"images/sports/{category}/full/{filename}"
                        thumb_path = f"images/sports/{category}/thumb/{filename}"
                        gallery_html.append(f'''
                    <a href="{full_path}" data-lightbox="sports" data-title="{title}">
                        <img src="{thumb_path}" alt="{title}" data-category="{category}">
                    </a>'''.strip())
                    else:
                        gallery_html.append(f'''
                    <a href="images/events/full/{filename}" data-lightbox="events" data-title="{title}">
                        <img src="images/events/thumb/{filename}" alt="{title}" data-category="{category}">
                    </a>'''.strip())

                # Create new content
                new_content = (
                    content[:start_idx] + 
                    '\n            ' + 
                    '\n            '.join(gallery_html) + 
                    '\n        ' + 
                    content[end_idx:]
                )

                # Write updated HTML
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            except Exception as e:
                print(f"Error updating HTML: {e}")
                return False

            return True