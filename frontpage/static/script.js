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
    initializeSearch();

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
});

function initializeSearch() {
    let articles = [];

    // Load articles data from the generated JSON file
    fetch('/static/articles.json')
        .then(response => response.json())
        .then(data => {
            articles = data;
            console.log('Articles data loaded successfully');
        })
        .catch(error => console.error('Error loading articles:', error));

    const searchInput = document.getElementById('searchInput'); // Make sure this ID matches your HTML
    const searchResultsContainer = document.getElementById('searchResults'); // Ensure this container exists in your HTML

    // Listen for user input on the search field
    if (searchInput) { // Adding a check to prevent errors if the element is missing
        searchInput.addEventListener('input', function() {
            const query = searchInput.value.toLowerCase();
            const filteredArticles = articles.filter(article =>
                article.title.toLowerCase().includes(query) ||
                article.content.toLowerCase().includes(query) ||
                JSON.stringify(article.metadata).toLowerCase().includes(query)
            );

            // Display the search results
            searchResultsContainer.innerHTML = filteredArticles.map(article => `
                <div class="search-result">
                    <h3>${article.title}</h3>
                    <p>${article.content.slice(0, 100)}...</p>
                    <p><em>Author: ${article.metadata.author}</em></p>
                    <a href="/articles/${article.metadata.slug}">Read More</a>
                </div>
            `).join('');
        });
    } else {
        console.error('Search input not found');
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
