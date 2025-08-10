/**
 * Cart Management JavaScript
 * Handles floating cart functionality and cart badge updates
 */

// Cart badge element
let cartBadge = null;

// Initialize cart functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeCart();
    setupFloatingCart();
});

/**
 * Initialize cart functionality
 */
function initializeCart() {
    cartBadge = document.getElementById('cartBadge');
    if (cartBadge) {
        updateCartBadge();
    }
}

/**
 * Setup floating cart click handlers
 */
function setupFloatingCart() {
    const floatingCart = document.querySelector('.floating-cart');
    if (floatingCart) {
        // Add click handler for keyboard accessibility
        floatingCart.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const cartUrl = this.getAttribute('data-cart-url');
                if (cartUrl) {
                    window.location.href = cartUrl;
                }
            }
        });

        // Add click handler for mouse
        floatingCart.addEventListener('click', function() {
            const cartUrl = this.getAttribute('data-cart-url');
            if (cartUrl) {
                window.location.href = cartUrl;
            }
        });
    }
}

/**
 * Update cart badge with current cart count
 */
function updateCartBadge() {
    if (!cartBadge) return;

    // Fetch cart count from server
    fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const count = data.count || 0;
            cartBadge.textContent = count;
            
            // Show/hide badge based on count
            if (count > 0) {
                cartBadge.style.display = 'flex';
                // Add animation for new items
                cartBadge.style.animation = 'cartPulse 0.6s ease-in-out';
                setTimeout(() => {
                    cartBadge.style.animation = '';
                }, 600);
            } else {
                cartBadge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error fetching cart count:', error);
            cartBadge.textContent = '0';
        });
}

/**
 * Add item to cart with visual feedback
 */
function addToCart(itemId, itemName) {
    // Show loading state
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Adding...';
    button.disabled = true;

    // Make API call to add item
    fetch(`/add_to_cart/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'quantity=1'
    })
    .then(response => {
        if (response.ok) {
            // Success feedback
            button.innerHTML = '<i class="fa-solid fa-check"></i> Added!';
            button.style.background = 'var(--success)';
            
            // Update cart badge
            updateCartBadge();
            
            // Show success message
            showNotification(`${itemName} added to cart!`, 'success');
            
            // Reset button after delay
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.background = '';
                button.disabled = false;
            }, 2000);
        } else {
            throw new Error('Failed to add item');
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        button.innerHTML = originalText;
        button.disabled = false;
        showNotification('Failed to add item to cart', 'error');
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fa-solid ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--primary)'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after delay
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Add CSS for cart pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes cartPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .notification-content i {
        font-size: 16px;
    }
`;
document.head.appendChild(style);

// Export functions for global access
window.cartManager = {
    updateCartBadge,
    addToCart,
    showNotification
};
