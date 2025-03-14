// Gallery Filtering
document.querySelectorAll('.filters button').forEach(button => {
    button.addEventListener('click', () => {
      const category = button.dataset.filter;
      const images = document.querySelectorAll('.grid img');
      images.forEach(img => {
        const imgCategory = img.dataset.category;
        if (category === 'all' || imgCategory === category) {
          img.parentElement.style.display = 'block';
        } else {
          img.parentElement.style.display = 'none';
        }
      });
    });
  });
  


document.addEventListener('DOMContentLoaded', function() {
  const menuToggle = document.querySelector('.menu-toggle');
  const mobileNav = document.querySelector('.mobile-nav');

  console.log('menuToggle:', menuToggle); // Check if the button is being selected
  console.log('mobileNav:', mobileNav);   // Check if the nav is being selected

  if (menuToggle && mobileNav) {
    menuToggle.addEventListener('click', function() {
      mobileNav.classList.toggle('open');
      console.log('Menu toggled!'); // Check if the click event is firing
    });
  } else {
    console.log('One or both elements not found!'); // Check if the elements are missing
  }
});