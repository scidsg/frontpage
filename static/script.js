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

    // Handle mobile navigation toggle
    const mobileNavButton = document.querySelector('.btnIcon');
    const navMenu = document.querySelector('header nav ul');

    mobileNavButton.addEventListener('click', function() {
        const isExpanded = this.getAttribute('aria-expanded') === 'true' || false;
        this.setAttribute('aria-expanded', !isExpanded);
        navMenu.classList.toggle('show');
    });

    // Handle closing the promo block
    const closePromoButton = document.getElementById('close_promo');
    const promoBlock = document.getElementById('promo');

    closePromoButton.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default anchor action
        promoBlock.classList.toggle('hide');
    });
    
    var deleteButtons = document.querySelectorAll('.delete-article-button');

    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this article?')) {
                event.preventDefault();
            }
        });
    });

    initializeUserPageLogic();
});

function initializeUserPageLogic() {
    const adminCheckboxes = document.querySelectorAll('.admin-checkbox');
    adminCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const userId = this.getAttribute('name').split('_')[1];
            updateApprovalStatus(this, userId);
        });
    });
}

function updateApprovalStatus(adminCheckbox, userId) {
    const approvalCheckbox = document.getElementById('approval_' + userId);
    if (adminCheckbox.checked) {
        approvalCheckbox.checked = false;
        approvalCheckbox.disabled = true;
    } else {
        approvalCheckbox.disabled = false;
    }
}
