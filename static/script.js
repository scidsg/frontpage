function hideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flashes');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.classList.add('fadeOut');
        }, 5000); // Delay before starting the fade out
    });
}

document.addEventListener('DOMContentLoaded', function() {
    hideFlashMessages();
});

