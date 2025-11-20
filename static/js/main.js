// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    
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
    
    
    // ========== API CALLS ==========
    async function fetchAllResults(jobTitle, company, zipCode) {
        // TODO: Move API keys to backend/env vars - NEVER expose in production
        const BRAVE_API_KEY = 'BSApFpZ7xVDKfVzChxSgGk4s8TN2LwJ';
        const OPENAI_API_KEY = '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';
        
        const baseParams = {
            company: company,
            job_title: jobTitle,
            brave_api_key: BRAVE_API_KEY,
            openai_api_key: OPENAI_API_KEY
        };
        
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
            fetch(`/api/company-info?${new URLSearchParams(baseParams)}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Company Info failed: ${r.status}`);
                    return r.json();
                })
                .then(data => { 
                    updateProgress('status-company-info', 'Company Information');
                    return data; 
                }),
            
            fetch(`/api/salary-benefits?${new URLSearchParams({...baseParams, location: zipCode})}`)
                .then(r => {
                    if (!r.ok) throw new Error(`Salary & Benefits failed: ${r.status}`);
                    return r.json();
                })
                .then(data => { 
                    updateProgress('status-salary', 'Salary & Benefits');
                    return data; 
                }),
            
            fetch(`/api/company-reviews?${new URLSearchParams({ company, brave_api_key: BRAVE_API_KEY, openai_api_key: OPENAI_API_KEY })}`)
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

    // ========== CARD RENDERING ==========

    function renderResultsCards(results, viewMode) {
        const cards = [
            {
                title: 'Company Information',
                emoji: '📋',
                color: 'text-blue-600 dark:text-blue-400',
                links: results.companyInfo.links || []
            },
            {
                title: 'Salary & Benefits',
                emoji: '💰',
                color: 'text-green-600 dark:text-green-400',
                links: results.salaryBenefits.links || []
            },
            {
                title: 'Company Reviews',
                emoji: '💬',
                color: 'text-purple-600 dark:text-purple-400',
                links: results.companyReviews.links || []
            },
            {
                title: 'Interview Preparation',
                emoji: '🎯',
                color: 'text-red-600 dark:text-red-400',
                links: results.interviewPrep.links || []
            }
        ];
        
        return cards.map(card => renderCard(card, viewMode)).join('');
    }

    function renderCard({ title, emoji, color, links }, viewMode) {
        const isCompact = viewMode === 'compact';
        
        // Handle empty results
        if (!links || links.length === 0) {
            return `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg ${isCompact ? 'p-4' : 'p-6'} transition-colors duration-200">
                    <div class="mb-4">
                        <h3 class="${isCompact ? 'text-lg' : 'text-xl'} font-bold ${color}">
                            ${emoji} ${title}
                        </h3>
                    </div>
                    <p class="text-gray-500 dark:text-gray-400 text-center py-8">
                        No results found for this category
                    </p>
                </div>
            `;
        }
        
        // Show first 3 links in compact, all in detailed
        const displayLinks = isCompact ? links.slice(0, 3) : links;
        
        return `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg ${isCompact ? 'p-4' : 'p-6'} transition-colors duration-200">
                <!-- Card Header -->
                <div class="mb-4">
                    <h3 class="${isCompact ? 'text-lg' : 'text-xl'} font-bold ${color}">
                        ${emoji} ${title}
                    </h3>
                </div>
                
                <!-- Links List -->
                <div class="space-y-3 mb-4">
                    ${displayLinks.map(link => renderLink(link, viewMode)).join('')}
                </div>
                
                <!-- Read More Button -->
                <div class="text-center mt-6">
                    <button class="px-6 py-2 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 text-sm font-medium">
                        Read More (Coming Soon)
                    </button>
                </div>
            </div>
        `;
    }

    function renderLink(link, viewMode) {
        const { url, title, description, category } = link;
        const isCompact = viewMode === 'compact';
        
        return `
            <a href="${url}" 
            target="_blank" 
            rel="noopener noreferrer"
            class="group block ${isCompact ? 'p-3' : 'p-4'} bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors duration-200 border border-gray-200 dark:border-gray-700 relative">
                <div class="flex items-start justify-between">
                    <div class="flex-1 pr-4">
                        <h4 class="font-semibold text-gray-900 dark:text-white mb-1 ${isCompact ? 'text-sm' : ''}">
                            ${title || 'Untitled'}
                        </h4>
                        
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

    function updateViewToggleButton(viewMode) {
        const button = document.getElementById('viewToggle');
        if (button) {
            button.textContent = viewMode === 'compact' 
                ? 'Switch to Detailed View' 
                : 'Switch to Compact View';
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
            const zipCode = document.getElementById('zipCode').value;
            
            console.log('%c[INFO] Starting search with params:', 'color: blue', { jobTitle, companyName, zipCode });
            
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
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Searching...';
            
            try {
                const results = await fetchAllResults(jobTitle, companyName, zipCode);
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
                resultsContainer.innerHTML = renderResultsCards(results, viewMode);
                
                // Store results globally for view toggle
                window.currentResults = results;
                
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
            }
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
            if (window.currentResults) {
                const resultsContainer = document.getElementById('resultsContainer');
                
                // Update container classes
                if (newView === 'compact') {
                    resultsContainer.className = 'grid grid-cols-1 md:grid-cols-2 gap-6';
                } else {
                    resultsContainer.className = '';
                }
                
                // Re-render
                resultsContainer.innerHTML = renderResultsCards(window.currentResults, newView);
            }
        });
    }
});