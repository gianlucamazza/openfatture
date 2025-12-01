// Main entry point
import './style.css'

console.log('OpenFatture Landing Page Loaded');

// Add any interactive logic here
// For example, smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href')).scrollIntoView({
      behavior: 'smooth'
    });
  });
});
