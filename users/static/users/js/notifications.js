// Notifications Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const notificationItems = document.querySelectorAll('.notification-item');
    const searchInput = document.getElementById('notification-search');
    const filterForm = document.getElementById('notification-filter-form');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const markAllReadBtn = document.getElementById('mark-all-read');
    const refreshBtn = document.getElementById('refresh-notifications');
    const mobileRefreshBtn = document.getElementById('mobile-refresh');
    const refreshEmptyBtn = document.getElementById('refresh-notifications-empty');
    
    // Modal logic
    const notificationModal = document.getElementById('notification-modal');
    const closeModalBtn = document.getElementById('close-notification-modal');
    const modalTitle = document.getElementById('modal-notification-title');
    const modalType = document.getElementById('modal-notification-type');
    const modalDate = document.getElementById('modal-notification-date');
    const modalMessage = document.getElementById('modal-notification-message');
    const modalMarkReadBtn = document.getElementById('modal-mark-read');
    let currentModalNotificationId = null;

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            
            notificationItems.forEach(item => {
                const title = item.querySelector('.notification-title')?.textContent.toLowerCase() || '';
                const message = item.querySelector('.notification-message')?.textContent.toLowerCase() || '';
                
                if (title.includes(searchTerm) || message.includes(searchTerm)) {
                    item.style.display = 'block';
                    if (searchTerm) {
                        highlightText(item.querySelector('.notification-title'), searchTerm);
                        highlightText(item.querySelector('.notification-message'), searchTerm);
                    } else {
                        removeHighlighting(item.querySelector('.notification-title'));
                        removeHighlighting(item.querySelector('.notification-message'));
                    }
                } else {
                    item.style.display = 'none';
                }
            });
            
            updateResultsCount();
        });
    }
    
    // Clear filters
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            filterForm.reset();
            notificationItems.forEach(item => {
                item.style.display = 'block';
                removeHighlighting(item.querySelector('.notification-title'));
                removeHighlighting(item.querySelector('.notification-message'));
            });
            updateResultsCount();
        });
    }
    
    // Apply filters
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            applyAdvancedFilters();
        });
    }
    
    // Quick filter buttons
    document.querySelectorAll('[data-quick-filter]').forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.getAttribute('data-quick-filter');
            applyQuickFilter(filterType);
        });
    });
    
    // Mark all as read
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            const unreadItems = document.querySelectorAll('.unread-notification');
            if (unreadItems.length > 0) {
                unreadItems.forEach(item => {
                    const notificationId = item.getAttribute('data-id');
                    markAsRead(notificationId);
                });
            }
        });
    }
    
    // Refresh notifications
    [refreshBtn, mobileRefreshBtn, refreshEmptyBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', function() {
                location.reload();
            });
        }
    });
    
    // Advanced filter function
    function applyAdvancedFilters() {
        const formData = new FormData(filterForm);
        const searchTerm = formData.get('search')?.toLowerCase() || '';
        const notificationType = formData.get('notification_type') || '';
        const status = formData.get('status') || '';
        const sortBy = formData.get('sort_by') || '';
        const dateFrom = formData.get('date_from') || '';
        const dateTo = formData.get('date_to') || '';
        const learner = formData.get('learner') || '';
        const priority = formData.get('priority') || '';
        
        notificationItems.forEach(item => {
            const title = item.querySelector('.notification-title')?.textContent.toLowerCase() || '';
            const message = item.querySelector('.notification-message')?.textContent.toLowerCase() || '';
            const itemType = item.getAttribute('data-type') || '';
            const itemRead = item.getAttribute('data-read') === 'true';
            const itemDate = item.getAttribute('data-date') || '';
            const itemLearner = item.getAttribute('data-learner') || '';
            
            let shouldShow = true;
            
            // Search filter
            if (searchTerm && !title.includes(searchTerm) && !message.includes(searchTerm)) {
                shouldShow = false;
            }
            
            // Type filter
            if (notificationType && itemType !== notificationType) {
                shouldShow = false;
            }
            
            // Status filter
            if (status === 'unread' && itemRead) {
                shouldShow = false;
            } else if (status === 'read' && !itemRead) {
                shouldShow = false;
            }
            
            // Date range filter
            if (dateFrom && itemDate < dateFrom) {
                shouldShow = false;
            }
            if (dateTo && itemDate > dateTo) {
                shouldShow = false;
            }
            // Learner filter
            if (learner && itemLearner !== learner) {
                shouldShow = false;
            }
            
            if (shouldShow) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
        
        updateResultsCount();
    }
    
    // Quick filter function
    function applyQuickFilter(filterType) {
        const today = new Date().toISOString().split('T')[0];
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        
        notificationItems.forEach(item => {
            const itemType = item.getAttribute('data-type') || '';
            const itemRead = item.getAttribute('data-read') === 'true';
            const itemDate = item.getAttribute('data-date') || '';
            
            let shouldShow = true;
            
            switch (filterType) {
                case 'today':
                    shouldShow = itemDate === today;
                    break;
                case 'week':
                    shouldShow = itemDate >= weekAgo;
                    break;
                case 'unread':
                    shouldShow = !itemRead;
                    break;
                case 'achievement':
                    shouldShow = itemType === 'achievement';
                    break;
                case 'quiz':
                    shouldShow = itemType === 'quiz';
                    break;
            }
            
            if (shouldShow) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
        
        updateResultsCount();
    }
    
    // Mark as read function
    function markAsRead(notificationId) {
        // Send AJAX request to mark as read
        fetch(`/accounts/notifications/${notificationId}/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const item = document.querySelector(`[data-id="${notificationId}"]`);
                if (item) {
                    item.classList.remove('unread-notification');
                    item.setAttribute('data-read', 'true');
                    
                    // Update unread count
                    updateUnreadCount();
                }
            }
        })
        .catch(error => {
            console.error('Error marking notification as read:', error);
        });
    }
    
    // Update results count
    function updateResultsCount() {
        const visibleItems = document.querySelectorAll('.notification-item:not([style*="display: none"])');
        const totalItems = notificationItems.length;
        
        // You could add a results counter element to show "Showing X of Y notifications"
        console.log(`Showing ${visibleItems.length} of ${totalItems} notifications`);
    }
    
    // Update unread count
    function updateUnreadCount() {
        const unreadItems = document.querySelectorAll('.unread-notification');
        const unreadCountElement = document.querySelector('.text-yellow-200 + .text-3xl');
        if (unreadCountElement) {
            unreadCountElement.textContent = unreadItems.length;
        }
    }
    
    // Text highlighting function
    function highlightText(element, searchTerm) {
        if (!element) return;
        
        const text = element.textContent;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        const highlightedText = text.replace(regex, '<mark class="bg-yellow-500/50 text-yellow-100 px-1 rounded">$1</mark>');
        element.innerHTML = highlightedText;
    }
    
    // Remove highlighting function
    function removeHighlighting(element) {
        if (!element) return;
        
        const text = element.textContent;
        element.innerHTML = text;
    }
    
    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Form submission prevention
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyAdvancedFilters();
        });
        // Auto-apply filters on change
        filterForm.querySelectorAll('input, select').forEach(function(input) {
            input.addEventListener('change', function() {
                applyAdvancedFilters();
            });
        });
    }
    
    // Notification item hover effects
    notificationItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Auto-refresh notifications every 30 seconds
    setInterval(() => {
        // You could implement a more sophisticated auto-refresh here
        // For now, we'll just update the timestamps
        updateTimestamps();
    }, 30000);
    
    // Update timestamps
    function updateTimestamps() {
        document.querySelectorAll('.notification-item').forEach(item => {
            const timestampElement = item.querySelector('.text-slate-400');
            if (timestampElement) {
                const createdAt = item.getAttribute('data-date');
                if (createdAt) {
                    const date = new Date(createdAt);
                    const now = new Date();
                    const diffInSeconds = Math.floor((now - date) / 1000);
                    
                    let timeAgo;
                    if (diffInSeconds < 60) {
                        timeAgo = `${diffInSeconds} seconds ago`;
                    } else if (diffInSeconds < 3600) {
                        timeAgo = `${Math.floor(diffInSeconds / 60)} minutes ago`;
                    } else if (diffInSeconds < 86400) {
                        timeAgo = `${Math.floor(diffInSeconds / 3600)} hours ago`;
                    } else {
                        timeAgo = `${Math.floor(diffInSeconds / 86400)} days ago`;
                    }
                    
                    timestampElement.textContent = timeAgo;
                }
            }
        });
    }
    
    // Initialize
    updateResultsCount();
    updateUnreadCount();

    // Modal logic
    notificationItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Prevent click on mark as read or view details buttons from triggering modal
            if (e.target.closest('button') || e.target.closest('a')) return;
            const notificationId = item.getAttribute('data-id');
            const title = item.querySelector('.notification-title')?.textContent || '';
            const message = item.querySelector('.notification-message')?.textContent || '';
            const type = item.getAttribute('data-type') || '';
            const typeDisplay = item.querySelector('.notification-title + div span')?.textContent || type;
            const date = item.getAttribute('data-date') || '';
            const read = item.getAttribute('data-read') === 'true';
            // Populate modal
            modalTitle.textContent = title;
            modalType.textContent = typeDisplay;
            modalDate.textContent = date;
            modalMessage.textContent = message;
            notificationModal.classList.remove('hidden');
            currentModalNotificationId = notificationId;
            // Mark as read if not already
            if (!read) {
                markAsRead(notificationId);
            }
        });
    });
    // Close modal logic
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            notificationModal.classList.add('hidden');
        });
    }
    // Close modal on outside click
    if (notificationModal) {
        notificationModal.addEventListener('click', function(e) {
            if (e.target === notificationModal) {
                notificationModal.classList.add('hidden');
            }
        });
    }
    // Mark as read button in modal
    if (modalMarkReadBtn) {
        modalMarkReadBtn.addEventListener('click', function() {
            if (currentModalNotificationId) {
                markAsRead(currentModalNotificationId);
            }
            notificationModal.classList.add('hidden');
        });
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
    
    .notification-item {
        transition: all 0.3s ease;
    }
    
    .notification-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }
    
    .notification-icon {
        transition: all 0.3s ease;
    }
    
    .notification-item:hover .notification-icon {
        transform: scale(1.1);
    }
    
    .unread-notification {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .filter-button {
        transition: all 0.2s ease;
    }
    
    .filter-button:hover {
        transform: translateY(-1px);
    }
    
    mark {
        animation: highlight 0.5s ease-in-out;
    }
    
    @keyframes highlight {
        0% { background-color: rgba(251, 191, 36, 0.3); }
        50% { background-color: rgba(251, 191, 36, 0.7); }
        100% { background-color: rgba(251, 191, 36, 0.5); }
    }
`;
document.head.appendChild(style); 