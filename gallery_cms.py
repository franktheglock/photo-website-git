import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from image_manager import ImageManager
from PIL import Image, ImageTk
import os

class GalleryCMS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Photography Gallery CMS")
        self.geometry("900x600")  # Increased size for image preview
        
        self.image_manager = ImageManager()
        
        # Create main container
        self.main_container = ttk.PanedWindow(self, orient='horizontal')
        self.main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel for upload form
        self.left_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.left_panel)
        
        # Right panel for image management
        self.right_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.right_panel)
        
        self.create_widgets()
        self.create_image_manager_panel()

    def create_widgets(self):
        # File selection
        file_frame = ttk.LabelFrame(self.left_panel, text="Select Image", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side="left", padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side="left")

        # Image details
        details_frame = ttk.LabelFrame(self.left_panel, text="Image Details", padding=10)
        details_frame.pack(fill="x", padx=10, pady=5)

        # Main Category
        ttk.Label(details_frame, text="Main Category:").pack(anchor="w")
        self.main_category_var = tk.StringVar()
        main_category_combo = ttk.Combobox(
            details_frame,
            textvariable=self.main_category_var,
            values=["sports", "events"]
        )
        main_category_combo.pack(fill="x", pady=(0, 10))
        main_category_combo.bind('<<ComboboxSelected>>', self.on_main_category_change)

        # Sub Category
        ttk.Label(details_frame, text="Sub Category:").pack(anchor="w")
        self.sub_category_var = tk.StringVar()
        self.sub_category_combo = ttk.Combobox(
            details_frame,
            textvariable=self.sub_category_var
        )
        self.sub_category_combo.pack(fill="x", pady=(0, 10))

        # Title
        ttk.Label(details_frame, text="Title:").pack(anchor="w")
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(details_frame, textvariable=self.title_var)
        title_entry.pack(fill="x", pady=(0, 10))

        # Compression quality
        ttk.Label(details_frame, text="Compression Quality:").pack(anchor="w")
        self.quality_var = tk.IntVar(value=100)
        quality_scale = ttk.Scale(
            details_frame,
            from_=1, to=100,
            variable=self.quality_var,
            orient="horizontal"
        )
        quality_scale.pack(fill="x")
        
        # Upload button
        upload_btn = ttk.Button(
            self.left_panel,
            text="Upload Image",
            command=self.upload_image,
            style="Accent.TButton"
        )
        upload_btn.pack(pady=20)

    def create_image_manager_panel(self):
        # Create image management panel
        manager_frame = ttk.LabelFrame(self.right_panel, text="Manage Images", padding=10)
        manager_frame.pack(fill="both", expand=True)

        # Filter controls
        filter_frame = ttk.Frame(manager_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter Category:").pack(side="left")
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["all", "sports", "events"]
        )
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.refresh_image_list)

        # Add refresh button next to filter
        refresh_btn = ttk.Button(
            filter_frame,
            text="Rescan Images",
            command=self.rescan_images
        )
        refresh_btn.pack(side="left", padx=5)

        # Create treeview for images
        self.tree = ttk.Treeview(manager_frame, columns=("ID", "Category", "Subcategory", "Title"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Subcategory", text="Subcategory")
        self.tree.heading("Title", text="Title")
        self.tree.column("ID", width=50)
        self.tree.pack(fill="both", expand=True)

        # Thumbnail preview
        self.preview_label = ttk.Label(manager_frame)
        self.preview_label.pack(pady=10)

        # Delete button
        delete_btn = ttk.Button(
            manager_frame,
            text="Delete Selected",
            command=self.delete_selected_image,
            style="Accent.TButton"
        )
        delete_btn.pack(pady=10)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_select_image)
        
        # Initial population
        self.refresh_image_list()

    def refresh_image_list(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        category = self.filter_var.get()
        images = self.image_manager.get_images(None if category == "all" else category)
        
        for img in images:
            self.tree.insert("", "end", values=img)

    def on_select_image(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        image_data = item['values']
        if not image_data:
            return

        # Get thumbnail path
        _, filename, main_category, sub_category, _ = image_data
        if main_category == 'sports':
            thumb_path = os.path.join(self.image_manager.dirs['sports'][sub_category]['thumb'], filename)
        else:
            thumb_path = os.path.join(self.image_manager.dirs['events']['thumb'], filename)

        # Display thumbnail
        if os.path.exists(thumb_path):
            try:
                img = Image.open(thumb_path)
                img.thumbnail((150, 150))  # Resize for preview
                photo = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=photo)
                self.preview_label.image = photo  # Keep reference
            except Exception as e:
                print(f"Error loading thumbnail: {e}")

    def delete_selected_image(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an image to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this image?"):
            item = self.tree.item(selection[0])
            image_id = item['values'][0]
            
            if self.image_manager.delete_image(image_id):
                messagebox.showinfo("Success", "Image deleted successfully")
                self.refresh_image_list()
            else:
                messagebox.showerror("Error", "Failed to delete image")

    def on_main_category_change(self, event=None):
        category = self.main_category_var.get()
        if category == "sports":
            self.sub_category_combo['values'] = ["basketball", "football"]
        else:
            self.sub_category_combo['values'] = ["weddings", "corporate"]
        self.sub_category_var.set("")  # Clear current selection

    def upload_image(self):
        file_path = self.file_path.get()
        main_category = self.main_category_var.get()
        sub_category = self.sub_category_var.get()
        title = self.title_var.get()
        quality = self.quality_var.get()

        if not all([file_path, main_category, sub_category, title]):
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            self.image_manager.add_image(
                file_path,
                main_category,
                sub_category,
                title,
                quality
            )
            messagebox.showinfo("Success", "Image uploaded successfully!")
            
            # Clear form
            self.file_path.set("")
            self.title_var.set("")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload image: {str(e)}")

    def browse_file(self):
        filetypes = (
            ('Image files', '*.jpg *.jpeg *.png'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path.set(filename)

    def rescan_images(self):
        try:
            # Delete database
            if os.path.exists(self.image_manager.db_path):
                os.remove(self.image_manager.db_path)
            
            # Reinitialize image manager
            self.image_manager = ImageManager()
            
            # Refresh the list
            self.refresh_image_list()
            messagebox.showinfo("Success", "Image database has been rescanned")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rescan images: {str(e)}")

if __name__ == "__main__":
    app = GalleryCMS()
    app.mainloop()