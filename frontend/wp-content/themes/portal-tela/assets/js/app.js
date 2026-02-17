/**
 * Portal Tela Theme - Main JavaScript
 */

// Bootstrap JS
import * as bootstrap from 'bootstrap';

// Copy Link functionality
document.addEventListener('DOMContentLoaded', () => {
    // Copy link to clipboard
    const copyButtons = document.querySelectorAll('.copy-link-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const url = button.dataset.url;
            
            try {
                await navigator.clipboard.writeText(url);
                
                // Visual feedback
                const originalHtml = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i>';
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-success');
                
                setTimeout(() => {
                    button.innerHTML = originalHtml;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-outline-secondary');
                }, 2000);
                
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Reading progress indicator (optional)
    const progressBar = document.querySelector('.reading-progress');
    
    if (progressBar) {
        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        });
    }
});

// Export Bootstrap for global access if needed
window.bootstrap = bootstrap;
