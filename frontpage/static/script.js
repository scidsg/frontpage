document.addEventListener('DOMContentLoaded', function() {
    const defaultOpenTab = document.getElementById("defaultOpen");
    if (defaultOpenTab) {
        defaultOpenTab.click();
    }

    hideFlashMessages();
    setupMobileNav();
    setupPromoBlock();
    setupDeleteButtons();
    initializeUserPageLogic();
    displayRandomQuote();
    toggleAdminTools();
    setupUIInteractions();

});

function setupUIInteractions() {
    const searchButton = document.getElementById('searchButton');
    const searchModal = document.getElementById('searchModal');
    const closeModalButton = document.getElementsByClassName('close')[0];

    if (searchButton && searchModal && closeModalButton) {
        searchButton.onclick = function() {
            searchModal.style.display = 'block';
        };

        closeModalButton.onclick = function() {
            searchModal.style.display = 'none';
        };

        window.onclick = function(event) {
            if (event.target === searchModal) {
                searchModal.style.display = 'none';
            }
        };
    } else {
        console.error('Search modal elements are missing.');
    }
}


function displayRandomQuote() {
    fetch('/static/quotes.json')
        .then(response => response.json())
        .then(quotes => {
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
        }, 5000);
    });
}

function setupMobileNav() {
    const mobileNavButton = document.querySelector('.btnIcon');
    const navMenu = document.querySelector('header nav ul');

    if (mobileNavButton && navMenu) {
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
    const deleteArticleButtons = document.querySelectorAll('.delete-article-button');
    const deleteUserButtons = document.querySelectorAll('.btn.destruct');

    deleteArticleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this article?')) {
                event.preventDefault();
            }
        });
    });

    deleteUserButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const username = button.getAttribute('data-username');
            if (!confirm('Are you sure you want to delete the user: ' + username + '?')) {
                event.preventDefault();
            }
        });
    });
}

function initializeUserPageLogic() {
    const adminCheckboxes = document.querySelectorAll('.admin-checkbox');

    adminCheckboxes.forEach(adminCheckbox => {
        toggleApprovalCheckbox(adminCheckbox);

        adminCheckbox.addEventListener('change', function() {
            toggleApprovalCheckbox(this);
        });
    });
}

function toggleApprovalCheckbox(adminCheckbox) {
    const userId = adminCheckbox.name.split('_')[1];
    const approvalCheckbox = document.getElementById('approval_' + userId);

    if (approvalCheckbox) {
        if (adminCheckbox.checked) {
            approvalCheckbox.checked = false;
            approvalCheckbox.disabled = true;
        } else {
            approvalCheckbox.disabled = false;
        }
    }
}

function openSection(evt, sectionName) {
    const tabcontent = document.getElementsByClassName("tabcontent");
    for (let i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    const tablinks = document.getElementsByClassName("tablinks");
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    const section = document.getElementById(sectionName);
    if (section) {
        section.style.display = "block";
    }

    evt.currentTarget.className += " active";
}

function toggleAdminTools() {
    const adminHeader = document.querySelector('h2[onclick="toggleAdminTools()"]');
    const toolsContent = document.querySelector('.tools-content');
    const arrow = document.querySelector('.arrow');

    if (adminHeader && toolsContent && arrow) {
        adminHeader.onclick = function() {
            const isDisplayed = toolsContent.style.display === 'none';
            toolsContent.style.display = isDisplayed ? 'block' : 'none';
            arrow.style.transform = isDisplayed ? 'rotate(-180deg)' : 'rotate(0deg)';
        };
    }
}
