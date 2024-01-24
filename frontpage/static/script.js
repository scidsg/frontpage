document.addEventListener('DOMContentLoaded', function() {
    hideFlashMessages();
    setupMobileNav();
    setupPromoBlock();
    setupDeleteButtons();
    initializeUserPageLogic();
    displayRandomQuote(); 
});

function displayRandomQuote() {
    fetch('/static/quotes.json') 
        .then(response => response.json())
        .then(quotes => {
            console.log(quotes); // Add this line for debugging
            const quoteElement = document.getElementById('quote');
            if (quoteElement && quotes.length) {
                const randomIndex = Math.floor(Math.random() * quotes.length);
                const quote = quotes[randomIndex];
                quoteElement.innerHTML = `<p>"${quote.text}"</p><p>- ${quote.author}</p>`;
            }
        })
        .catch(error => console.error('Error loading quotes:', error));
}

function hideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flashes');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.classList.add('fadeOut');
        }, 5000); // Delay before starting the fade out
    });
}

function setupMobileNav() {
    const mobileNavButton = document.querySelector('.btnIcon');
    const navMenu = document.querySelector('header nav ul');

    if (mobileNavButton) {
        mobileNavButton.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true' || false;
            this.setAttribute('aria-expanded', !isExpanded);
            navMenu.classList.toggle('show');
        });
    }
}

function setupPromoBlock() {
    const closePromoButton = document.getElementById('close_promo');
    if (closePromoButton) {
        closePromoButton.addEventListener('click', function(event) {
            event.preventDefault();
            const promoBlock = document.getElementById('promo');
            if (promoBlock) {
                promoBlock.classList.toggle('hide');
            }
        });
    }
}

function setupDeleteButtons() {
    var deleteArticleButtons = document.querySelectorAll('.delete-article-button');
    var deleteUserButtons = document.querySelectorAll('.btn.destruct');

    deleteArticleButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this article?')) {
                event.preventDefault();
            }
        });
    });

    deleteUserButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            var username = button.getAttribute('data-username');
            if (!confirm('Are you sure you want to delete the user: ' + username + '?')) {
                event.preventDefault();
            }
        });
    });
}


function initializeUserPageLogic() {
    const adminCheckboxes = document.querySelectorAll('.admin-checkbox');

    adminCheckboxes.forEach(function(adminCheckbox) {
        toggleApprovalCheckbox(adminCheckbox);

        adminCheckbox.addEventListener('change', function() {
            toggleApprovalCheckbox(this);
        });
    });
}

function toggleApprovalCheckbox(adminCheckbox) {
    const userId = adminCheckbox.name.split('_')[1];
    const approvalCheckbox = document.getElementById('approval_' + userId);

    if (adminCheckbox.checked) {
        approvalCheckbox.checked = false;
        approvalCheckbox.disabled = true;
    } else {
        approvalCheckbox.disabled = false;
    }
}
