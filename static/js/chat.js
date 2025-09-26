// Reusable Delete Menu JavaScript Component
// Add this to your base template or as a separate JS file

class ChatDeleteManager {
    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        // Individual chat deletion
        $(document).on('click', '.delete-thread-btn, .delete-current-chat', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const threadId = $(e.target).closest('[data-thread-id]').data('thread-id');
            const isCurrentChat = $(e.target).hasClass('delete-current-chat');
            
            this.deleteChat(threadId, isCurrentChat);
        });

        // Bulk delete all chats
        $(document).on('click', '#clear-all-btn', (e) => {
            e.preventDefault();
            this.clearAllChats();
        });

        // Keyboard shortcut for delete (Ctrl/Cmd + D)
        $(document).on('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'd' && $('.chat-item.active').length) {
                e.preventDefault();
                const threadId = $('.chat-item.active').data('thread-id');
                this.deleteChat(threadId, false);
            }
        });
    }

    deleteChat(threadId, isCurrentChat = false, customMessage = null) {
        const confirmMessage = customMessage || 'Delete this conversation? This cannot be undone.';
        
        if (!confirm(confirmMessage)) {
            return;
        }

        // Show loading state
        const $button = $(`.delete-thread-btn[data-thread-id="${threadId}"], .delete-current-chat[data-thread-id="${threadId}"]`);
        const originalContent = $button.html();
        $button.html('<i class="fas fa-spinner fa-spin"></i>').prop('disabled', true);

        $.post(`/chat/delete-thread/${threadId}/`, {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        })
        .done((response) => {
            if (response.success) {
                this.handleDeleteSuccess(threadId, isCurrentChat, response.message);
            } else {
                this.handleDeleteError(response.error || 'Unknown error occurred');
            }
        })
        .fail(() => {
            this.handleDeleteError('Network error. Please check your connection.');
        })
        .always(() => {
            $button.html(originalContent).prop('disabled', false);
        });
    }

    handleDeleteSuccess(threadId, isCurrentChat, message = null) {
        // Show success message
        this.showNotification(message || 'Chat deleted successfully', 'success');

        if (isCurrentChat) {
            // Redirect to dashboard if current chat was deleted
            window.location.href = '/chat/dashboard/';
        } else {
            // Remove chat item from UI
            const $chatItem = $(`.chat-item[data-thread-id="${threadId}"]`);
            $chatItem.fadeOut(300, function() {
                $(this).remove();
                
                // Update UI if no more chats
                if ($('.chat-item').length === 0) {
                    $('.overflow-auto').html(`
                        <div class="text-center text-muted py-4">
                            <i class="fas fa-comment-dots fa-2x mb-2"></i>
                            <p class="small">No conversations yet</p>
                        </div>
                    `);
                    $('#clear-all-btn').hide();
                }
            });
        }
    }

    handleDeleteError(error) {
        this.showNotification(`Error deleting chat: ${error}`, 'error');
    }

    clearAllChats() {
        const chatCount = $('.chat-item').length;
        
        if (chatCount === 0) {
            this.showNotification('No chats to delete', 'info');
            return;
        }

        if (!confirm(`Delete all ${chatCount} conversations? This cannot be undone.`)) {
            return;
        }

        // Show loading state
        const $button = $('#clear-all-btn');
        const originalContent = $button.html();
        $button.html('<i class="fas fa-spinner fa-spin"></i> Deleting...').prop('disabled', true);

        $.post('/chat/clear-chats/', {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        })
        .done((response) => {
            if (response.success) {
                this.showNotification(response.message || 'All conversations deleted', 'success');
                // Reload page to update UI
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.handleDeleteError(response.error || 'Unknown error occurred');
            }
        })
        .fail(() => {
            this.handleDeleteError('Network error. Please check your connection.');
        })
        .always(() => {
            $button.html(originalContent).prop('disabled', false);
        });
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toastId = 'toast-' + Date.now();
        const iconClass = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-exclamation-circle text-danger',
            'info': 'fas fa-info-circle text-info'
        }[type] || 'fas fa-info-circle text-info';

        const toast = `
            <div id="${toastId}" class="toast show position-fixed top-0 end-0 m-3" style="z-index: 1060;" role="alert">
                <div class="toast-header">
                    <i class="${iconClass} me-2"></i>
                    <strong class="me-auto">Chat Manager</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        $('body').append(toast);
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            $(`#${toastId}`).toast('hide');
        }, 4000);
    }

    // Batch operations
    selectMultipleChats() {
        $('.chat-item').each(function() {
            const $item = $(this);
            if (!$item.find('.chat-checkbox').length) {
                $item.prepend(`
                    <input type="checkbox" class="chat-checkbox form-check-input me-2" 
                           data-thread-id="${$item.data('thread-id')}">
                `);
            }
        });

        // Add batch action buttons
        if (!$('#batch-actions').length) {
            $('.chat-list-container').prepend(`
                <div id="batch-actions" class="mb-3 p-2 bg-light rounded d-none">
                    <button class="btn btn-sm btn-danger" id="delete-selected">
                        <i class="fas fa-trash me-1"></i>Delete Selected
                    </button>
                    <button class="btn btn-sm btn-secondary ms-2" id="cancel-batch">
                        Cancel
                    </button>
                </div>
            `);
        }

        // Show/hide batch actions based on selection
        $(document).on('change', '.chat-checkbox', () => {
            const selectedCount = $('.chat-checkbox:checked').length;
            $('#batch-actions').toggleClass('d-none', selectedCount === 0);
        });

        // Delete selected chats
        $(document).on('click', '#delete-selected', () => {
            const selectedIds = $('.chat-checkbox:checked').map(function() {
                return $(this).data('thread-id');
            }).get();

            if (selectedIds.length === 0) return;

            if (confirm(`Delete ${selectedIds.length} selected conversations?`)) {
                this.deleteMultipleChats(selectedIds);
            }
        });

        // Cancel batch mode
        $(document).on('click', '#cancel-batch', () => {
            $('.chat-checkbox').remove();
            $('#batch-actions').remove();
        });
    }

    deleteMultipleChats(threadIds) {
        let completed = 0;
        const total = threadIds.length;

        threadIds.forEach(threadId => {
            $.post(`/chat/delete-thread/${threadId}/`, {
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            })
            .always(() => {
                completed++;
                if (completed === total) {
                    location.reload();
                }
            });
        });
    }
}

// Initialize when document is ready
$(document).ready(function() {
    window.chatDeleteManager = new ChatDeleteManager();
});

// Usage Examples:
// 1. Basic delete button: <button class="delete-thread-btn" data-thread-id="123">Delete</button>
// 2. Current chat delete: <button class="delete-current-chat" data-thread-id="123">Delete This Chat</button>
// 3. Clear all button: <button id="clear-all-btn">Clear All Chats</button>
// 4. Enable batch selection: chatDeleteManager.selectMultipleChats();