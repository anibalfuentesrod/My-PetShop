// main.js
document.addEventListener('DOMContentLoaded', function () {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.querySelector('.nav-links');

    // Toggle the 'active' class on the nav-links when the hamburger is clicked
    hamburger.addEventListener('click', function () {
        navLinks.classList.toggle('active');
    });
});
