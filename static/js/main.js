console.log('main.js loaded');
// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    

    console.log('DOM loaded, setting up event listeners');
    
    // Remote checkbox - handle all location fields
    const remoteCheckbox = document.getElementById('remoteRole');
    const stateInput = document.getElementById('stateInput');
    const cityInput = document.getElementById('cityInput');
    const zipCodeInput = document.getElementById('zipCode');

    console.log('Remote checkbox:', remoteCheckbox);
    console.log('Location inputs:', stateInput, cityInput, zipCodeInput);

    if (remoteCheckbox && stateInput && cityInput && zipCodeInput) {
        remoteCheckbox.addEventListener('change', function() {
            console.log('Remote checkbox changed:', this.checked);
            const disabledClasses = ['bg-gray-200', 'dark:bg-gray-600', 'cursor-not-allowed', 'opacity-50'];

            if (this.checked) {
                // Disable all location fields
                [stateInput, cityInput, zipCodeInput].forEach(input => {
                    input.disabled = true;
                    input.value = '';
                    input.required = false;
                    input.classList.add(...disabledClasses);
                });
            } else {
                // Re-enable all location fields
                [stateInput, cityInput, zipCodeInput].forEach(input => {
                    input.disabled = false;
                    input.classList.remove(...disabledClasses);
                });
            }
        });
    }

    // ==========================================
    // CONTACT FORM FUNCTIONALITY
    // ==========================================
    
    const contactUsBtn = document.getElementById('contactUsBtn');
    const contactModal = document.getElementById('contactModal');
    const closeContactModal = document.getElementById('closeContactModal');
    const cancelContact = document.getElementById('cancelContact');
    const closeSuccessModal = document.getElementById('closeSuccessModal');
    const contactForm = document.getElementById('contactForm');
    
    // Check if elements exist
    if (!contactUsBtn || !contactModal) {
        console.error('Contact form elements not found');
        return;
    }
    
    // Open contact modal
    contactUsBtn.addEventListener('click', function() {
        contactModal.classList.remove('hidden');
        contactForm.classList.remove('hidden');
        document.getElementById('contactSuccess').classList.add('hidden');
    });
    
    // Close contact modal (X button)
    closeContactModal.addEventListener('click', function() {
        contactModal.classList.add('hidden');
        resetContactForm();
    });
    
    // Close contact modal (Cancel button)
    cancelContact.addEventListener('click', function() {
        contactModal.classList.add('hidden');
        resetContactForm();
    });
    
    // Close success modal
    closeSuccessModal.addEventListener('click', function() {
        contactModal.classList.add('hidden');
        resetContactForm();
    });
    
    // Close modal when clicking outside
    contactModal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.add('hidden');
            resetContactForm();
        }
    });
    
    // Handle form submission
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('contactName').value.trim();
        const email = document.getElementById('contactEmail').value.trim();
        const message = document.getElementById('contactMessage').value.trim();
        
        // Use mailto link
        const subject = encodeURIComponent(`InterviewLuck Contact from ${name}`);
        const body = encodeURIComponent(`From: ${name}\nEmail: ${email}\n\nMessage:\n${message}`);
        
        window.location.href = `mailto:contact@interviewluck.io?subject=${subject}&body=${body}`;
        
        showContactSuccess();
    });
    
    function showContactSuccess() {
        document.getElementById('contactForm').classList.add('hidden');
        document.getElementById('contactSuccess').classList.remove('hidden');
    }
    
    function resetContactForm() {
        contactForm.reset();
        contactForm.classList.remove('hidden');
        document.getElementById('contactSuccess').classList.add('hidden');
        
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Message';
        }
    }

    // ========== DARK MODE TOGGLE ==========
    const toggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;
    
    // Check localStorage and set initial theme
    if (localStorage.getItem('theme') === 'dark') {
        htmlElement.classList.add('dark');
    }
    
    // Toggle click handler
    toggle.addEventListener('click', function() {
        if (htmlElement.classList.contains('dark')) {
            htmlElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        } else {
            htmlElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        }
    });
    
    
    // ========== DEBOUNCE UTILITY ==========
    function debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }
    
    
    // ========== AUTOCOMPLETE SEARCH ==========
    const jobTitleInput = document.getElementById('jobTitle');
    const dropdown = document.getElementById('jobTitleDropdown');
    
    
    if (!jobTitleInput || !dropdown) {
        console.error('Required elements not found');
        return;
    }
    
    // Search function with debounce
    const performSearch = debounce(async function(query) {
        
        if (query.length < 2) {
            dropdown.classList.add('hidden');
            return;
        }
        
        try {
            const url = `/api/autocomplete/job-title?q=${encodeURIComponent(query)}`;
            
            const response = await fetch(url);
            
            const results = await response.json();
            
            if (results.length === 0) {
                dropdown.classList.add('hidden');
                return;
            }
            
            // Build dropdown HTML
            dropdown.innerHTML = results
                .map(title => `
                    <div class="dropdown-item px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer text-gray-900 dark:text-white">
                        ${title}
                    </div>
                `)
                .join('');
            
            // Show dropdown
            dropdown.classList.remove('hidden');
            
            // Add click handlers to items
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => {
                item.addEventListener('click', function() {
                    const selectedValue = this.textContent.trim();
                    jobTitleInput.value = selectedValue;
                    dropdown.classList.add('hidden');
                });
            });
            
        } catch (error) {
            console.error('Search error:', error);
            console.error('Error stack:', error.stack);
            dropdown.classList.add('hidden');
        }
    }, 300);
    
    // Input event listener
    jobTitleInput.addEventListener('input', function(e) {
        performSearch(e.target.value);
    });
    
    // Click outside to close dropdown
    document.addEventListener('click', function(e) {
        if (!jobTitleInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });


    // ========== COMPANY AUTOCOMPLETE ==========
    const companyNameInput = document.getElementById('companyName');
    const companyDropdown = document.getElementById('companyNameDropdown');

    if (!companyNameInput || !companyDropdown) {
        console.error('Company autocomplete elements not found');
    } else {
        // Search function with debounce for company
        const performCompanySearch = debounce(async function(query) {
            if (query.length < 2) {
                companyDropdown.classList.add('hidden');
                return;
            }

            try {
                const url = `/api/autocomplete/company?q=${encodeURIComponent(query)}`;
                const response = await fetch(url);
                const results = await response.json();

                if (results.length === 0) {
                    companyDropdown.classList.add('hidden');
                    return;
                }

                // Build dropdown HTML
                companyDropdown.innerHTML = results
                    .map(company => `
                        <div class="dropdown-item px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer text-gray-900 dark:text-white">
                            ${company}
                        </div>
                    `)
                    .join('');

                // Show dropdown
                companyDropdown.classList.remove('hidden');

                // Add click handlers to items
                const items = companyDropdown.querySelectorAll('.dropdown-item');
                items.forEach(item => {
                    item.addEventListener('click', function() {
                        const selectedValue = this.textContent.trim();
                        companyNameInput.value = selectedValue;
                        companyDropdown.classList.add('hidden');
                    });
                });

            } catch (error) {
                console.error('Company search error:', error);
                companyDropdown.classList.add('hidden');
            }
        }, 300);

        // Input event listener for company
        companyNameInput.addEventListener('input', function(e) {
            performCompanySearch(e.target.value);
        });

        // Click outside to close company dropdown
        document.addEventListener('click', function(e) {
            if (!companyNameInput.contains(e.target) && !companyDropdown.contains(e.target)) {
                companyDropdown.classList.add('hidden');
            }
        });
    }


    // ========== API CALLS ==========
    async function fetchAllResults(jobTitle, company, location) {

        const baseParams = {
            company: company,
            job_title: jobTitle
        };

        // Build location parameters for API calls
        let locationParams = {};
        if (location.type === 'remote') {
            locationParams = { location: 'REMOTE' };
        } else {
            // Pass state, city, and zipcode separately
            if (location.state) locationParams.state = location.state;
            if (location.city) locationParams.city = location.city;
            if (location.zipcode) locationParams.zipcode = location.zipcode;
        }

        const baseParamsCompanyInfo = {
            company: company,
            job_title: jobTitle,
            ...locationParams
        }
        
        // Track progress
        let completed = 0;
        const total = 4;
        
        function updateProgress(itemId, itemName) {
            completed++;
            
            // Update progress counter
            document.getElementById('progressIndicator').textContent = `${completed}/${total} complete`;
            
            // Update loading text
            document.getElementById('loadingText').textContent = `${itemName} loaded`;
            
            // Mark item as completed
            const statusElement = document.getElementById(itemId);
            const dot = statusElement.querySelector('.loading-dot');
            dot.classList.add('completed');
            
            console.log(`%c[OK] ${itemName} loaded (${completed}/${total})`, 'color: green');
        }
        
        // Fire all 4 endpoints in parallel
        const [companyInfo, salaryBenefits, companyReviews, interviewPrep] = await Promise.all([
            fetch(`/api/company-info?${new URLSearchParams(baseParamsCompanyInfo)}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Company Info failed: ${r.status}`);
                    return r.json();
                })
                .then(data => { 
                    updateProgress('status-company-info', 'Company Information');
                    return data; 
                }),
            
            fetch(`/api/salary-benefits?${new URLSearchParams({...baseParams, ...locationParams})}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Salary & Benefits failed: ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    updateProgress('status-salary', 'Salary & Benefits');
                    return data;
                }),
            
            fetch(`/api/company-reviews?${new URLSearchParams({ company })}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Company Reviews failed: ${r.status}`);
                    return r.json();
                })
                .then(data => { 
                    updateProgress('status-reviews', 'Company Reviews');
                    return data; 
                }),
            
            fetch(`/api/interview-prep?${new URLSearchParams(baseParams)}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Interview Prep failed: ${r.status}`);
                    return r.json();
                })
                .then(data => { 
                    updateProgress('status-interview', 'Interview Preparation');
                    return data; 
                })
        ]);
        
        // Log full results
        console.log('%c[DATA] Company Info:', 'color: purple', companyInfo);
        console.log('%c[DATA] Salary & Benefits:', 'color: purple', salaryBenefits);
        console.log('%c[DATA] Company Reviews:', 'color: purple', companyReviews);
        console.log('%c[DATA] Interview Prep:', 'color: purple', interviewPrep);
        
        return { companyInfo, salaryBenefits, companyReviews, interviewPrep };
    }

    // ========== VIDEO HELPER FUNCTIONS ==========

    function toggleVideo(uniqueId) {
        const embedContainer = document.getElementById(uniqueId);
        const arrow = document.getElementById(`${uniqueId}-arrow`);

        if (embedContainer.classList.contains('hidden')) {
            embedContainer.classList.remove('hidden');
            arrow.style.transform = 'rotate(180deg)';
        } else {
            embedContainer.classList.add('hidden');
            arrow.style.transform = 'rotate(0deg)';
        }
    }

    function extractVideoId(url) {
        // YouTube patterns
        if (url.includes('youtube.com/watch?v=')) {
            const urlParams = new URLSearchParams(new URL(url).search);
            return urlParams.get('v');
        } else if (url.includes('youtu.be/')) {
            return url.split('youtu.be/')[1].split('?')[0];
        } else if (url.includes('youtube.com/embed/')) {
            return url.split('youtube.com/embed/')[1].split('?')[0];
        }

        // Vimeo patterns
        if (url.includes('vimeo.com/')) {
            const match = url.match(/vimeo\.com\/(\d+)/);
            return match ? match[1] : null;
        }

        return null;
    }

    function getEmbedUrl(url, videoId) {
        if (!videoId) return '';

        // YouTube embed
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            return `https://www.youtube.com/embed/${videoId}`;
        }

        // Vimeo embed
        if (url.includes('vimeo.com')) {
            return `https://player.vimeo.com/video/${videoId}`;
        }

        return '';
    }

    // Make toggleVideo available globally for onclick handlers
    window.toggleVideo = toggleVideo;

    // ========== CARD RENDERING ==========

    function renderResultsCards(results, viewMode, companyName) {
        const cards = [
            {
                title: `${companyName} Interview Prep`,
                emoji: '🎯',
                color: 'text-red-600 dark:text-red-400',
                links: results.interviewPrep.links || [],
                allLinks: results.interviewPrep.all_links || [],
                cardId: 'interview-prep'
            },
            {
                title: `${companyName} Overview`,
                emoji: '📋',
                color: 'text-blue-600 dark:text-blue-400',
                links: results.companyInfo.links || [],
                allLinks: results.companyInfo.all_links || [],
                cardId: 'company-info'
            },
            {
                title: `Total Rewards: Compensation, Benefits, and Perk at ${companyName}`,
                emoji: '💰',
                color: 'text-green-600 dark:text-green-400',
                links: results.salaryBenefits.links || [],
                allLinks: results.salaryBenefits.all_links || [],
                cardId: 'salary-benefits'
            },
            {
                title: `${companyName} 3 C's: Company, Culture, and Career`,
                emoji: '💬',
                color: 'text-purple-600 dark:text-purple-400',
                links: results.companyReviews.links || [],
                allLinks: results.companyReviews.all_links || [],
                cardId: 'company-reviews'
            }
        ];

        // Store all links globally for modal access
        window.allLinksData = {
            'interview-prep': results.interviewPrep.all_links || [],
            'company-info': results.companyInfo.all_links || [],
            'salary-benefits': results.salaryBenefits.all_links || [],
            'company-reviews': results.companyReviews.all_links || []
        };

        return cards.map(card => renderCard(card, viewMode)).join('');
    }

    function renderCard({ title, emoji, color, links, allLinks, cardId }, viewMode) {
        const isCompact = viewMode === 'compact';
        const hasMoreLinks = allLinks && allLinks.length > links.length;

        // Handle empty results
        if (!links || links.length === 0) {
            return `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg ${isCompact ? 'p-4' : 'p-6'} transition-colors duration-200">
                    <div class="mb-4">
                        <h3 class="${isCompact ? 'text-lg' : 'text-xl'} font-bold ${color}">
                            ${title}
                        </h3>
                    </div>
                    <p class="text-gray-500 dark:text-gray-400 text-center py-8">
                        No high-quality results found for this category
                    </p>
                    ${hasMoreLinks ? `
                        <div class="text-center">
                            <button onclick="showMoreLinksModal('${cardId}')" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                                View ${allLinks.length} lower-scored results
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Show first 5 links in compact, all in detailed
        const displayLinks = isCompact ? links.slice(0, 5) : links;

        return `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg ${isCompact ? 'p-4' : 'p-6'} transition-colors duration-200">
                <!-- Card Header -->
                <div class="mb-4 flex justify-between items-start">
                    <h3 class="${isCompact ? 'text-lg' : 'text-xl'} font-bold ${color}">
                        ${title}
                    </h3>
                    <span class="text-xs text-gray-400">${links.length} results</span>
                </div>

                <!-- Links List -->
                <div class="space-y-3 mb-4">
                    ${displayLinks.map((link, index) => renderLink(link, viewMode, index)).join('')}
                </div>

                <!-- More Links Button -->
                ${hasMoreLinks ? `
                    <div class="text-center pt-2 border-t border-gray-200 dark:border-gray-700">
                        <button onclick="showMoreLinksModal('${cardId}')" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                            View all ${allLinks.length} results (including lower-scored)
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function renderLink(link, viewMode, linkIndex) {
        const { url, title, description, category, type, score } = link;
        const isCompact = viewMode === 'compact';

        // Check if this is a video link
        if (type === 'video') {
            console.log('Video link detected:', url);
            return renderVideoLink(link, viewMode, linkIndex);
        }

        // Score badge color based on score (60/40/20 tiers)
        // Highly Relevant (60+) / Relevant (40-59) / Tangential (<40)
        const getScoreColor = (s) => {
            if (s >= 60) return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
            if (s >= 40) return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
            return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
        };

        // Regular link rendering
        return `
            <a href="${url}"
            target="_blank"
            rel="noopener noreferrer"
            class="group block ${isCompact ? 'p-3' : 'p-4'} bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors duration-200 border border-gray-200 dark:border-gray-700 relative">
                <div class="flex items-start justify-between">
                    <div class="flex-1 pr-4">
                        <div class="flex items-center gap-2 mb-1">
                            <h4 class="font-semibold text-gray-900 dark:text-white ${isCompact ? 'text-sm' : ''}">
                                ${title || 'Untitled'}
                            </h4>
                            ${score !== undefined ? `
                                <span class="inline-block text-xs px-1.5 py-0.5 rounded ${getScoreColor(score)} font-mono">
                                    ${score}
                                </span>
                            ` : ''}
                        </div>

                        ${isCompact && description ? `
                            <!-- Tooltip for compact view -->
                            <div class="hidden group-hover:block absolute left-0 right-0 top-full mt-2 z-20 bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-xl p-3 max-w-md">
                                <p class="text-sm text-gray-700 dark:text-gray-300">
                                    ${description}
                                </p>
                            </div>
                        ` : ''}

                        ${!isCompact && description ? `
                            <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                                ${description}
                            </p>
                        ` : ''}

                        ${category ? `
                            <span class="inline-block text-xs px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                                ${category}
                            </span>
                        ` : ''}
                    </div>
                    <svg class="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                </div>
            </a>
        `;
    }

    function renderVideoLink(link, viewMode, linkIndex) {
        const { url, title, description, category } = link;
        const isCompact = viewMode === 'compact';
        const videoId = extractVideoId(url);
        const uniqueId = `video-${linkIndex}-${Date.now()}`;

        return `
            <div class="${isCompact ? 'p-3' : 'p-4'} bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                <!-- Video Header (Clickable) -->
                <div class="cursor-pointer" onclick="toggleVideo('${uniqueId}')">
                    <div class="flex items-start justify-between">
                        <div class="flex items-start flex-1 pr-4">
                            <!-- Red YouTube Icon -->
                            <svg class="w-6 h-6 text-red-600 flex-shrink-0 mr-3 mt-1" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                            </svg>

                            <div class="flex-1">
                                <h4 class="font-semibold text-gray-900 dark:text-white mb-1 ${isCompact ? 'text-sm' : ''}">
                                    ${title || 'Video'}
                                </h4>

                                ${!isCompact && description ? `
                                    <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                                        ${description}
                                    </p>
                                ` : ''}

                                ${category ? `
                                    <span class="inline-block text-xs px-2 py-1 rounded-full bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">
                                        ${category}
                                    </span>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Dropdown Arrow -->
                        <svg id="${uniqueId}-arrow" class="w-5 h-5 text-gray-400 flex-shrink-0 mt-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                    </div>
                </div>

                <!-- Video Embed (Hidden by default) -->
                <div id="${uniqueId}" class="hidden mt-4">
                    <div class="relative" style="padding-bottom: 56.25%; height: 0; overflow: hidden;">
                        <iframe
                            class="absolute top-0 left-0 w-full h-full rounded-lg"
                            src="${getEmbedUrl(url, videoId)}"
                            frameborder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="inline-block mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline">
                        Watch on YouTube →
                    </a>
                </div>
            </div>
        `;
    }

    function updateViewToggleButton(viewMode) {
        const button = document.getElementById('viewToggle');
        if (button) {
            button.textContent = viewMode === 'compact' 
                ? 'Switch to Detailed View' 
                : 'Switch to Compact View';
        }
    }
    
    
    // ========== COMPANY CONFIRMATION MODAL ==========
    const companyConfirmModal = document.getElementById('companyConfirmModal');
    const closeCompanyConfirmModal = document.getElementById('closeCompanyConfirmModal');
    const cancelCompanyConfirm = document.getElementById('cancelCompanyConfirm');
    const confirmUserInput = document.getElementById('confirmUserInput');
    const userCompanyInput = document.getElementById('userCompanyInput');
    const companySuggestions = document.getElementById('companySuggestions');
    const suggestionsSection = document.getElementById('suggestionsSection');
    const acronymWarning = document.getElementById('acronymWarning');
    const exactMatchBadge = document.getElementById('exactMatchBadge');
    const customInputBadge = document.getElementById('customInputBadge');

    // Store pending search data
    let pendingSearchData = null;

    // Close modal handlers
    if (closeCompanyConfirmModal) {
        closeCompanyConfirmModal.addEventListener('click', () => {
            companyConfirmModal.classList.add('hidden');
            pendingSearchData = null;
        });
    }

    if (cancelCompanyConfirm) {
        cancelCompanyConfirm.addEventListener('click', () => {
            companyConfirmModal.classList.add('hidden');
            pendingSearchData = null;
        });
    }

    // Click outside to close
    if (companyConfirmModal) {
        companyConfirmModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
                pendingSearchData = null;
            }
        });
    }

    // Confirm user's original input
    if (confirmUserInput) {
        confirmUserInput.addEventListener('click', () => {
            if (pendingSearchData) {
                companyConfirmModal.classList.add('hidden');
                executeSearch(pendingSearchData.jobTitle, pendingSearchData.companyName, pendingSearchData.location);
            }
        });
    }

    // Function to show company confirmation modal
    async function showCompanyConfirmation(jobTitle, companyName, location) {
        pendingSearchData = { jobTitle, companyName, location };

        try {
            // Fetch company confirmation data
            const response = await fetch(`/api/autocomplete/company-confirm?q=${encodeURIComponent(companyName)}`);
            const data = await response.json();

            console.log('%c[INFO] Company confirmation data:', 'color: blue', data);

            // Update modal content
            userCompanyInput.textContent = data.query;

            // Show full name and description if available
            const fullNameEl = document.getElementById('exactMatchFullName');
            const descriptionEl = document.getElementById('exactMatchDescription');

            if (data.exact_match_full_name) {
                fullNameEl.textContent = data.exact_match_full_name;
                fullNameEl.classList.remove('hidden');
            } else {
                fullNameEl.classList.add('hidden');
            }

            if (data.exact_match_description) {
                descriptionEl.textContent = data.exact_match_description;
                descriptionEl.classList.remove('hidden');
            } else {
                descriptionEl.classList.add('hidden');
            }

            // Show appropriate badge
            if (data.is_in_database) {
                exactMatchBadge.classList.remove('hidden');
                customInputBadge.classList.add('hidden');
            } else {
                exactMatchBadge.classList.add('hidden');
                customInputBadge.classList.remove('hidden');
            }

            // Show acronym warning if applicable
            const hasAcronymMatches = data.suggestions.some(s => s.reason === 'acronym');
            if (hasAcronymMatches) {
                acronymWarning.classList.remove('hidden');
            } else {
                acronymWarning.classList.add('hidden');
            }

            // Render suggestions
            if (data.suggestions.length > 0) {
                suggestionsSection.classList.remove('hidden');
                companySuggestions.innerHTML = data.suggestions.map(suggestion => {
                    const reasonBadges = {
                        'acronym': '<span class="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200">Acronym</span>',
                        'related': '<span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200">Related</span>',
                        'similar': '',
                        'partial': ''
                    };
                    const reasonBadge = reasonBadges[suggestion.reason] || '';

                    // Build description line
                    let infoLine = '';
                    if (suggestion.full_name && suggestion.full_name !== suggestion.name) {
                        infoLine = `<p class="text-sm text-gray-600 dark:text-gray-400 mt-0.5">${suggestion.full_name}</p>`;
                    }
                    if (suggestion.description) {
                        infoLine += `<p class="text-xs text-gray-500 dark:text-gray-500 mt-0.5">${suggestion.description}</p>`;
                    }

                    return `
                        <button class="company-suggestion-btn w-full text-left p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition group" data-company="${suggestion.name}">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <div class="flex items-center gap-2 flex-wrap">
                                        <span class="font-medium text-gray-900 dark:text-white">${suggestion.name}</span>
                                        ${reasonBadge}
                                    </div>
                                    ${infoLine}
                                </div>
                                <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 flex-shrink-0 ml-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                                </svg>
                            </div>
                        </button>
                    `;
                }).join('');

                // Add click handlers to suggestion buttons
                companySuggestions.querySelectorAll('.company-suggestion-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const selectedCompany = this.dataset.company;
                        companyConfirmModal.classList.add('hidden');
                        // Update the input field with selected company
                        document.getElementById('companyName').value = selectedCompany;
                        // Execute search with selected company
                        executeSearch(pendingSearchData.jobTitle, selectedCompany, pendingSearchData.location);
                    });
                });
            } else {
                suggestionsSection.classList.add('hidden');
            }

            // Show modal
            companyConfirmModal.classList.remove('hidden');

        } catch (error) {
            console.error('%c[ERROR] Company confirmation failed:', 'color: red', error);
            // On error, proceed with search anyway
            executeSearch(jobTitle, companyName, location);
        }
    }

    // Function to execute the actual search
    async function executeSearch(jobTitle, companyName, location) {
        console.log('%c[INFO] Starting search with confirmed company:', 'color: blue', { jobTitle, companyName, location });

        // Show results section and loading state
        const resultsSection = document.getElementById('resultsSection');
        const loadingState = document.getElementById('loadingState');
        const resultsContainer = document.getElementById('resultsContainer');

        resultsSection.classList.remove('hidden');
        loadingState.classList.remove('hidden');
        resultsContainer.classList.add('hidden');

        // Reset progress indicators
        document.getElementById('progressIndicator').textContent = '0/4 complete';
        document.getElementById('loadingText').textContent = 'Starting search...';

        // Reset all status dots
        ['status-company-info', 'status-salary', 'status-reviews', 'status-interview'].forEach(id => {
            const dot = document.getElementById(id).querySelector('.loading-dot');
            dot.classList.remove('completed');
        });

        // Disable button and show loading state
        const submitButton = searchForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Searching...';

        try {
            const results = await fetchAllResults(jobTitle, companyName, location);
            console.log('%c[OK] All results loaded successfully', 'color: green');

            // Get view mode from localStorage (default to compact)
            const viewMode = localStorage.getItem('viewMode') || 'compact';

            // Set container classes based on view mode
            if (viewMode === 'compact') {
                resultsContainer.className = 'grid grid-cols-1 md:grid-cols-2 gap-6';
            } else {
                resultsContainer.className = '';
            }

            // Render cards
            resultsContainer.innerHTML = renderResultsCards(results, viewMode, companyName);

            // Store results globally for view toggle
            window.currentResults = results;
            window.currentCompanyName = companyName;

            // Hide loading, show results
            loadingState.classList.add('hidden');
            resultsContainer.classList.remove('hidden');

            // Show view toggle button
            const viewToggleContainer = document.getElementById('viewToggleContainer');
            const viewToggle = document.getElementById('viewToggle');
            if (viewToggleContainer && viewToggle) {
                viewToggleContainer.classList.remove('hidden');
                viewToggle.classList.remove('hidden');
                updateViewToggleButton(viewMode);
            }

        } catch (error) {
            console.error('%c[ERROR] Search failed:', 'color: red', error);
            alert('Search failed. Check console for details.');

            // Hide everything on error
            resultsSection.classList.add('hidden');
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            pendingSearchData = null;
        }
    }

    // ========== FORM SUBMISSION ==========
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Extract form values
            const jobTitle = document.getElementById('jobTitle').value;
            const companyName = document.getElementById('companyName').value;
            const isRemote = document.getElementById('remoteRole').checked;
            const state = document.getElementById('stateInput').value.trim().toUpperCase();
            const city = document.getElementById('cityInput').value.trim();
            const zipCode = document.getElementById('zipCode').value.trim();

            // Build location object for API calls
            let location;
            if (isRemote) {
                location = { type: 'remote' };
            } else {
                location = {
                    type: 'location',
                    state: state,
                    city: city,
                    zipcode: zipCode
                };
            }

            // Show company confirmation modal
            await showCompanyConfirmation(jobTitle, companyName, location);
        });
    }

    // ========== VIEW TOGGLE ==========
    const viewToggle = document.getElementById('viewToggle');
    if (viewToggle) {
        viewToggle.addEventListener('click', function() {
            // Get current view mode
            const currentView = localStorage.getItem('viewMode') || 'compact';
            const newView = currentView === 'compact' ? 'detailed' : 'compact';

            // Save to localStorage
            localStorage.setItem('viewMode', newView);

            // Update button text
            updateViewToggleButton(newView);

            // Re-render cards if results exist
            if (window.currentResults && window.currentCompanyName) {
                const resultsContainer = document.getElementById('resultsContainer');

                // Update container classes
                if (newView === 'compact') {
                    resultsContainer.className = 'grid grid-cols-1 md:grid-cols-2 gap-6';
                } else {
                    resultsContainer.className = '';
                }

                // Re-render
                resultsContainer.innerHTML = renderResultsCards(window.currentResults, newView, window.currentCompanyName);
            }
        });
    }

    // ========== MORE LINKS MODAL ==========
    window.showMoreLinksModal = function(cardId) {
        const allLinks = window.allLinksData[cardId] || [];
        const modal = document.getElementById('moreLinksModal');
        const content = document.getElementById('moreLinksContent');
        const title = document.getElementById('moreLinksTitle');

        // Set title based on card
        const titles = {
            'interview-prep': 'All Interview Prep Links',
            'company-info': 'All Company Overview Links',
            'salary-benefits': 'All Salary & Benefits Links',
            'company-reviews': 'All Company Reviews Links'
        };
        title.textContent = titles[cardId] || 'All Links';

        // Score badge color (60/40/20 tiers)
        const getScoreColor = (s) => {
            if (s >= 60) return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
            if (s >= 40) return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
            return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
        };

        // Render all links
        content.innerHTML = allLinks.map(link => `
            <a href="${link.url}" target="_blank" rel="noopener noreferrer"
               class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors border border-gray-200 dark:border-gray-600">
                <div class="flex-1 pr-4">
                    <div class="font-medium text-gray-900 dark:text-white text-sm truncate">
                        ${link.title || 'Untitled'}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
                        ${new URL(link.url).hostname}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs px-2 py-1 rounded font-mono ${getScoreColor(link.score || 0)}">
                        ${link.score || 0}
                    </span>
                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                </div>
            </a>
        `).join('');

        modal.classList.remove('hidden');
    };

    window.closeMoreLinksModal = function() {
        document.getElementById('moreLinksModal').classList.add('hidden');
    };

    // Close modal on outside click
    const moreLinksModal = document.getElementById('moreLinksModal');
    if (moreLinksModal) {
        moreLinksModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    }
});