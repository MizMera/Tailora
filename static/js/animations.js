/**
 * Tailora Animation Controller
 * Handles scroll animations, counters, and ripple effects
 */

(function () {
    'use strict';

    // ========================================
    // SCROLL-TRIGGERED ANIMATIONS
    // ========================================

    const animateOnScroll = () => {
        const elements = document.querySelectorAll('[data-animate]:not(.animated)');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const delay = entry.target.dataset.animateDelay || 0;
                    setTimeout(() => {
                        entry.target.classList.add('animated');
                    }, delay);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        elements.forEach(el => observer.observe(el));
    };

    // ========================================
    // COUNTER ANIMATION
    // ========================================

    const animateCounters = () => {
        const counters = document.querySelectorAll('[data-counter]');

        counters.forEach(counter => {
            const rawValue = counter.getAttribute('data-counter');
            const target = parseInt(rawValue, 10);

            // Safety check for valid number
            if (isNaN(target)) {
                // If invalid, ensure originally rendered content stays (or 0)
                if (!counter.textContent.trim()) counter.textContent = "0";
                return;
            }

            const duration = parseInt(counter.dataset.counterDuration, 10) || 1500;
            const start = 0;

            const startAnimation = () => {
                let startTime = null;

                const step = (currentTime) => {
                    if (!startTime) startTime = currentTime;
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);

                    // Easing function (ease-out-expo)
                    const easeOutExpo = 1 - Math.pow(2, -10 * progress);
                    const current = Math.floor(start + (target - start) * easeOutExpo);

                    counter.textContent = current.toLocaleString();

                    if (progress < 1) {
                        requestAnimationFrame(step);
                    } else {
                        counter.textContent = target.toLocaleString();
                    }
                };

                requestAnimationFrame(step);
            };

            // Start when element is visible
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        startAnimation();
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 }); // Lower threshold to ensure it starts easily

            observer.observe(counter);
        });
    };

    // ========================================
    // BUTTON RIPPLE EFFECT
    // ========================================

    const initRippleEffect = () => {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.btn-ripple');
            if (!button) return;

            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');

            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            button.appendChild(ripple);

            ripple.addEventListener('animationend', () => ripple.remove());
        });
    };

    // ========================================
    // STAGGER ANIMATION FOR GRIDS
    // ========================================

    const initStaggerAnimation = () => {
        const staggerContainers = document.querySelectorAll('.stagger-on-load');

        staggerContainers.forEach(container => {
            const children = container.children;
            Array.from(children).forEach((child, index) => {
                child.style.animationDelay = `${index * 50}ms`;
                child.classList.add('animate-fade-in-up');
            });
        });
    };

    // ========================================
    // SMOOTH PAGE TRANSITIONS
    // ========================================

    const initPageTransitions = () => {
        // Add fade-out effect when navigating away
        document.querySelectorAll('a[href]:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');

                // Skip for form submits, external links, or same page
                if (link.closest('form') || href.startsWith('http') || href.startsWith('//')) return;

                e.preventDefault();

                document.body.classList.add('page-exit');

                setTimeout(() => {
                    window.location.href = href;
                }, 200);
            });
        });
    };

    // ========================================
    // HOVER 3D TILT EFFECT
    // ========================================

    const initTiltEffect = () => {
        const tiltElements = document.querySelectorAll('.hover-tilt-3d');

        tiltElements.forEach(el => {
            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const tiltX = (y - centerY) / 20;
                const tiltY = (centerX - x) / 20;

                el.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.02, 1.02, 1.02)`;
            });

            el.addEventListener('mouseleave', () => {
                el.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
            });
        });
    };

    // ========================================
    // LIKE HEART ANIMATION
    // ========================================

    const initLikeAnimation = () => {
        document.querySelectorAll('.like-heart').forEach(heart => {
            heart.addEventListener('click', function () {
                this.classList.toggle('liked');

                // Create burst particles
                if (this.classList.contains('liked')) {
                    createBurstParticles(this);
                }
            });
        });
    };

    const createBurstParticles = (element) => {
        const colors = ['#e74c3c', '#f39c12', '#e91e63', '#ff5722'];
        const rect = element.getBoundingClientRect();

        for (let i = 0; i < 8; i++) {
            const particle = document.createElement('span');
            particle.style.cssText = `
        position: fixed;
        width: 6px;
        height: 6px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        border-radius: 50%;
        left: ${rect.left + rect.width / 2}px;
        top: ${rect.top + rect.height / 2}px;
        pointer-events: none;
        z-index: 9999;
      `;

            document.body.appendChild(particle);

            const angle = (i / 8) * Math.PI * 2;
            const velocity = 50 + Math.random() * 30;
            const tx = Math.cos(angle) * velocity;
            const ty = Math.sin(angle) * velocity;

            particle.animate([
                { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                { transform: `translate(${tx}px, ${ty}px) scale(0)`, opacity: 0 }
            ], {
                duration: 600,
                easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)'
            }).onfinish = () => particle.remove();
        }
    };

    // ========================================
    // LOADING SKELETON REPLACER
    // ========================================

    const replaceSkeleton = (skeletonId, content) => {
        const skeleton = document.getElementById(skeletonId);
        if (!skeleton) return;

        skeleton.classList.add('animate-fade-out');
        setTimeout(() => {
            skeleton.innerHTML = content;
            skeleton.classList.remove('skeleton', 'animate-fade-out');
            skeleton.classList.add('animate-fade-in');
        }, 200);
    };

    // ========================================
    // TOAST NOTIFICATIONS
    // ========================================

    const showToast = (message, type = 'info', duration = 3000) => {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 10px;
      `;
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} toast-enter`;
        toast.style.cssText = `
      padding: 12px 24px;
      background: ${type === 'error' ? '#c62828' : type === 'success' ? '#2e7d32' : '#2c2c2c'};
      color: #fff;
      border-radius: 0;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      font-family: 'Inter', sans-serif;
      font-size: 14px;
    `;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');
            toast.addEventListener('animationend', () => toast.remove());
        }, duration);
    };

    // Expose to global scope
    window.TailoraAnimations = {
        replaceSkeleton,
        showToast,
        createBurstParticles
    };

    // ========================================
    // INITIALIZE ON DOM READY
    // ========================================

    const init = () => {
        animateOnScroll();
        animateCounters();
        initRippleEffect();
        initStaggerAnimation();
        initTiltEffect();
        initLikeAnimation();
        // initPageTransitions(); // Uncomment for page transitions
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
