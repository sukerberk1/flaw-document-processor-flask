// Add a simple animation when the page loads
document.addEventListener('DOMContentLoaded', function () {
    const featureCards = document.querySelectorAll('.card');

    // Add a fade-in effect to each card
    featureCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';

        // Stagger the animations
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });
}); 