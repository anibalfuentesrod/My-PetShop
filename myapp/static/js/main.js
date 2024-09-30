// this is for the hamburger on the right top for phone
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.querySelector('.nav-links');

    // Toggle the 'active' class when the hamburger is clicked
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            hamburger.classList.toggle('open'); // Add animation to hamburger
        });
    }
});