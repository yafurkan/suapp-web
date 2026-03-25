// Admin panel access - logo click counter
let logoClickCount = 0;
let logoClickTimer = null;

// Function to handle logo clicks for admin access
function handleLogoClick() {
    logoClickCount++;
    
    // Reset counter after 3 seconds of inactivity
    clearTimeout(logoClickTimer);
    logoClickTimer = setTimeout(() => {
        logoClickCount = 0;
    }, 3000);
    
    // Show subtle feedback for clicks
    if (logoClickCount >= 5 && logoClickCount < 10) {
        const logo = document.querySelector('.nav-logo');
        if (logo) {
            logo.style.transform = 'scale(1.1)';
            setTimeout(() => logo.style.transform = '', 200);
        }
    }
    
    // Open admin panel after 10 clicks
    if (logoClickCount >= 10) {
        logoClickCount = 0;
        showAdminAccessNotification();
    }
}

// Function to show admin access notification
function showAdminAccessNotification() {
    const notification = document.createElement('div');
    notification.innerHTML = `
        <div style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            z-index: 10000;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        ">
            <div style="font-size: 40px; margin-bottom: 15px;">🔐</div>
            <h3 style="margin-bottom: 15px;">Admin Paneline Erişim</h3>
            <p style="margin-bottom: 20px; opacity: 0.8;">Admin paneline yönlendiriliyorsunuz...</p>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="window.open('admin.html', '_blank'); this.parentElement.parentElement.parentElement.remove();" style="
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                ">Admin Panel</button>
                <button onclick="this.parentElement.parentElement.parentElement.remove();" style="
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                ">İptal</button>
            </div>
        </div>
    `;
    document.body.appendChild(notification);
    
    // Auto remove after 10 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 10000);
}

// Function to load news from localStorage and update the site
function loadNewsFromStorage() {
    const newsList = JSON.parse(localStorage.getItem('suu_news') || '[]');
    updateNewsSection(newsList);
}

// Function to update news section on the main site
function updateNewsSection(newsList) {
    const newsGrid = document.querySelector('.news-grid');
    if (!newsGrid || newsList.length === 0) return;
    
    // Take only the first 3 most recent news
    const recentNews = newsList.slice(0, 3);
    
    newsGrid.innerHTML = recentNews.map(news => `
        <div class="news-card">
            <div class="news-image">
                ${news.image ? 
                    `<img src="${news.image}" alt="${news.title}" style="width: 100%; height: 100%; object-fit: cover;">` :
                    `<div class="news-icon">
                        <i class="fas fa-newspaper"></i>
                    </div>`
                }
                <div class="news-badge">Yeni</div>
            </div>
            <div class="news-content">
                <h3>${news.title}</h3>
                <p class="news-date">${formatNewsDate(news.date)}</p>
                <p>${news.description.length > 150 ? news.description.substring(0, 150) + '...' : news.description}</p>
                <a href="#" class="news-link">Devamını Oku</a>
            </div>
        </div>
    `).join('');
}

// Function to format news date
function formatNewsDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Bugün';
    if (diffDays === 2) return 'Dün';
    if (diffDays <= 7) return `${diffDays - 1} gün önce`;
    return date.toLocaleDateString('tr-TR');
}

// DOM Elements
const loadingScreen = document.getElementById('loading-screen');
const navbar = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');
const navLinks = document.querySelectorAll('.nav-link');

// Loading Screen — handled by inline script for instant dismissal
// Fallback: ensure it's hidden if inline script didn't run
if (loadingScreen && !loadingScreen.classList.contains('hidden')) {
    loadingScreen.classList.add('hidden');
    document.body.style.overflow = 'visible';
}
setTimeout(showIOSPopup, 800);

// iOS Popup Functionality
function showIOSPopup() {
    const iosPopup = document.getElementById('ios-popup');
    if (iosPopup) {
        // Show only once (iOS is now live announcement)
        const alreadySeen = localStorage.getItem('ios-launch-popup-seen');

        if (!alreadySeen) {
            iosPopup.classList.add('show');
            document.body.style.overflow = 'hidden';

            // Add celebration animation
            addIOSCelebrationAnimation();

            // Save that popup was shown
            localStorage.setItem('ios-launch-popup-seen', 'true');
        }
    }
}

function hideIOSPopup() {
    const iosPopup = document.getElementById('ios-popup');
    if (iosPopup) {
        iosPopup.classList.remove('show');
        document.body.style.overflow = 'visible';
    }
}

function addIOSCelebrationAnimation() {
    // Create floating iOS icons
    const celebrationContainer = document.createElement('div');
    celebrationContainer.className = 'ios-celebration';
    celebrationContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    `;
    
    document.body.appendChild(celebrationContainer);
    
    // Create multiple iOS icons
    const icons = ['fas fa-mobile-alt', 'fab fa-apple', 'fas fa-tablet-alt', 'fas fa-watch'];
    
    for (let i = 0; i < 6; i++) {
        const icon = document.createElement('div');
        const iconClass = icons[Math.floor(Math.random() * icons.length)];
        
        icon.innerHTML = `<i class="${iconClass}"></i>`;
        icon.style.cssText = `
            position: absolute;
            font-size: 24px;
            color: #007AFF;
            left: ${Math.random() * 100}%;
            top: -50px;
            animation: iosCelebrationFloat ${3 + Math.random() * 2}s ease-out forwards;
            animation-delay: ${i * 0.3}s;
        `;
        
        celebrationContainer.appendChild(icon);
    }
    
    // Add animation styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes iosCelebrationFloat {
            0% {
                transform: translateY(0) rotate(0deg) scale(1);
                opacity: 1;
            }
            50% {
                transform: translateY(50vh) rotate(180deg) scale(1.2);
                opacity: 0.8;
            }
            100% {
                transform: translateY(100vh) rotate(360deg) scale(0.5);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Remove celebration after animation
    setTimeout(() => {
        celebrationContainer.remove();
        style.remove();
    }, 8000);
}

// Event listeners for iOS popup
document.addEventListener('DOMContentLoaded', () => {
    const closeIosPopup = document.getElementById('closeIosPopup');
    const closePopupBtn = document.getElementById('closePopupBtn');
    const notifyMeBtn = document.getElementById('notifyMeBtn');
    const iosPopupOverlay = document.getElementById('ios-popup');
    
    // App Store buttons
    const appStoreBtn = document.getElementById('appStoreBtn');
    const heroAppStoreBtn = document.getElementById('heroAppStoreBtn');
    
    // Instagram links
    const instagramLinks = document.querySelectorAll('.instagram-link');
    
    // X (Twitter) links
    const xLinks = document.querySelectorAll('.x-link');
    
    // Facebook links
    const facebookLinks = document.querySelectorAll('.facebook-link');
    
    if (closeIosPopup) {
        closeIosPopup.addEventListener('click', hideIOSPopup);
    }
    
    if (closePopupBtn) {
        closePopupBtn.addEventListener('click', hideIOSPopup);
    }
    
    if (notifyMeBtn) {
        notifyMeBtn.addEventListener('click', () => {
            window.open('https://apps.apple.com/us/app/suu-su-takip/id6757619920', '_blank', 'noopener');
            hideIOSPopup();
        });
    }
    
    // App Store button functionality
    function handleAppStoreClick() {
        // href already points to App Store — this handler kept for analytics/tracking
    }
    
    if (appStoreBtn) {
        appStoreBtn.addEventListener('click', handleAppStoreClick);
    }
    
    if (heroAppStoreBtn) {
        heroAppStoreBtn.addEventListener('click', handleAppStoreClick);
    }
    
    // Instagram native app opening functionality
    instagramLinks.forEach(link => {
        link.addEventListener('click', handleInstagramClick);
    });
    
    // X (Twitter) native app opening functionality
    xLinks.forEach(link => {
        link.addEventListener('click', handleXClick);
    });
    
    // Facebook native app opening functionality
    facebookLinks.forEach(link => {
        link.addEventListener('click', handleFacebookClick);
    });
    
    // Close popup when clicking on overlay
    if (iosPopupOverlay) {
        iosPopupOverlay.addEventListener('click', (e) => {
            if (e.target === iosPopupOverlay) {
                hideIOSPopup();
            }
        });
    }
    
    // Close popup with ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideIOSPopup();
        }
    });
});

// Function to handle Facebook link clicks
function handleFacebookClick(e) {
    e.preventDefault();
    
    const facebookId = e.currentTarget.getAttribute('data-facebook-id');
    const webUrl = `https://www.facebook.com/people/SuuTakip/${facebookId}/`;
    const appUrl = `fb://profile/${facebookId}`; // Facebook app deep link
    
    // Detect if it's mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Try to open Facebook app first
        const startTime = Date.now();
        
        // Create a hidden iframe to attempt app opening
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = appUrl;
        document.body.appendChild(iframe);
        
        // Set a timeout to check if the app opened
        setTimeout(() => {
            document.body.removeChild(iframe);
            
            // If the app didn't open (user returned quickly), open web version
            const timeElapsed = Date.now() - startTime;
            if (timeElapsed < 2000) {
                // App probably not installed or didn't open, fallback to web
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 1500);
        
        // Also try with window.location as backup
        setTimeout(() => {
            try {
                window.location = appUrl;
            } catch (e) {
                // If error, open web version
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 100);
        
    } else {
        // Desktop - just open web version
        window.open(webUrl, '_blank', 'noopener,noreferrer');
    }
    
    // Show a nice feedback message
    showFacebookFeedback();
}

// Function to handle X (Twitter) link clicks
function handleXClick(e) {
    e.preventDefault();
    
    const username = e.currentTarget.getAttribute('data-x-username');
    const webUrl = `https://x.com/${username}`;
    const appUrl = `twitter://user?screen_name=${username}`; // X app still uses twitter:// protocol
    
    // Detect if it's mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Try to open X app first
        const startTime = Date.now();
        
        // Create a hidden iframe to attempt app opening
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = appUrl;
        document.body.appendChild(iframe);
        
        // Set a timeout to check if the app opened
        setTimeout(() => {
            document.body.removeChild(iframe);
            
            // If the app didn't open (user returned quickly), open web version
            const timeElapsed = Date.now() - startTime;
            if (timeElapsed < 2000) {
                // App probably not installed or didn't open, fallback to web
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 1500);
        
        // Also try with window.location as backup
        setTimeout(() => {
            try {
                window.location = appUrl;
            } catch (e) {
                // If error, open web version
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 100);
        
    } else {
        // Desktop - just open web version
        window.open(webUrl, '_blank', 'noopener,noreferrer');
    }
    
    // Show a nice feedback message
    showXFeedback();
}

// Function to handle Instagram link clicks
function handleInstagramClick(e) {
    e.preventDefault();
    
    const username = e.currentTarget.getAttribute('data-instagram');
    const webUrl = `https://www.instagram.com/${username}/`;
    const appUrl = `instagram://user?username=${username}`;
    
    // Detect if it's mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Try to open Instagram app first
        const startTime = Date.now();
        
        // Create a hidden iframe to attempt app opening
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = appUrl;
        document.body.appendChild(iframe);
        
        // Set a timeout to check if the app opened
        setTimeout(() => {
            document.body.removeChild(iframe);
            
            // If the app didn't open (user returned quickly), open web version
            const timeElapsed = Date.now() - startTime;
            if (timeElapsed < 2000) {
                // App probably not installed or didn't open, fallback to web
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 1500);
        
        // Also try with window.location as backup
        setTimeout(() => {
            try {
                window.location = appUrl;
            } catch (e) {
                // If error, open web version
                window.open(webUrl, '_blank', 'noopener,noreferrer');
            }
        }, 100);
        
    } else {
        // Desktop - just open web version
        window.open(webUrl, '_blank', 'noopener,noreferrer');
    }
    
    // Show a nice feedback message
    showInstagramFeedback();
}

// Function to show Instagram opening feedback
function showInstagramFeedback() {
    const notification = document.createElement('div');
    notification.className = 'instagram-feedback';
    notification.innerHTML = `
        <div class="instagram-feedback-content">
            <div class="instagram-feedback-icon">
                <i class="fab fa-instagram"></i>
            </div>
            <div class="instagram-feedback-text">
                <span>🚀 Instagram'da takip etmeyi unutmayın!</span>
            </div>
        </div>
    `;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        max-width: 300px;
        background: linear-gradient(135deg, #E4405F, #C13584);
        color: white;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(196, 53, 132, 0.3);
        z-index: 10001;
        transform: translateY(100px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateY(100px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 400);
    }, 3000);
}

// Function to show X (Twitter) opening feedback
function showXFeedback() {
    const notification = document.createElement('div');
    notification.className = 'x-feedback';
    notification.innerHTML = `
        <div class="x-feedback-content">
            <div class="x-feedback-icon">
                <i class="fab fa-x-twitter"></i>
            </div>
            <div class="x-feedback-text">
                <span>🚀 X'te takip etmeyi unutmayın!</span>
            </div>
        </div>
    `;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 20px;
        max-width: 300px;
        background: linear-gradient(135deg, #000000, #1DA1F2);
        color: white;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 10001;
        transform: translateY(100px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateY(100px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 400);
    }, 3000);
}

// Navbar Scroll Effect
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Mobile Menu Toggle
hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// Smooth Scrolling for Navigation Links (sadece # ile başlayanlar)
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        e.preventDefault();
        const targetSection = document.querySelector(href);
        if (targetSection) {
            window.scrollTo({
                top: targetSection.offsetTop - 70,
                behavior: 'smooth'
            });
        }
    });
});

// Phone Screen Animation
let currentScreen = 0;
const screens = document.querySelectorAll('.app-screen');
const totalScreens = screens.length;

function switchScreen() {
    screens[currentScreen].classList.remove('active');
    currentScreen = (currentScreen + 1) % totalScreens;
    screens[currentScreen].classList.add('active');
}

// Auto-switch phone screens every 4 seconds
setInterval(switchScreen, 4000);


// Intersection Observer for Animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, [data-aos]');
    animatedElements.forEach(el => {
        observer.observe(el);
    });
});

// Counter Animation for Statistics
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-target'));
        const increment = target / 100;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                if (target === 2.1) {
                    counter.textContent = current.toFixed(1);
                } else if (target === 4.9) {
                    counter.textContent = current.toFixed(1);
                } else {
                    counter.textContent = Math.ceil(current);
                }
                requestAnimationFrame(updateCounter);
            } else {
                if (target === 2.1) {
                    counter.textContent = '2.1';
                } else if (target === 4.9) {
                    counter.textContent = '4.9';
                } else {
                    counter.textContent = target;
                }
            }
        };
        
        updateCounter();
    });
}

// Trigger counter animation when stats section is visible
const statsSection = document.querySelector('.stats');
if (statsSection) {
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    statsObserver.observe(statsSection);
}

// Screenshots Carousel
let currentSlide = 0;
const slides = document.querySelectorAll('.screenshot-item');
const dots = document.querySelectorAll('.dot');
const totalSlides = slides.length;

function showSlide(index) {
    // Hide all slides
    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));
    
    // Show current slide
    slides[index].classList.add('active');
    dots[index].classList.add('active');
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
}

// Auto-advance carousel
setInterval(nextSlide, 5000);

// Dot navigation
dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
        currentSlide = index;
        showSlide(currentSlide);
    });
});

// Feature Cards Hover Effect
const featureCards = document.querySelectorAll('.feature-card');
featureCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        const icon = card.querySelector('.feature-icon i');
        if (icon) {
            icon.style.animation = 'pulse 0.6s ease-in-out';
        }
    });
    
    card.addEventListener('mouseleave', () => {
        const icon = card.querySelector('.feature-icon i');
        if (icon) {
            icon.style.animation = '';
        }
    });
});

// Add Button Click Effects
const addButtons = document.querySelectorAll('.add-btn');
addButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Create ripple effect
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        button.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            ripple.remove();
        }, 600);
        
        // Animate water level increase
        const waterFill = document.querySelector('.water-fill');
        const levelText = document.querySelector('.level-text');
        if (waterFill && levelText) {
            const currentHeight = parseInt(waterFill.style.height) || 65;
            const newHeight = Math.min(currentHeight + 10, 100);
            waterFill.style.height = newHeight + '%';
            
            // Update text based on height
            const amount = (newHeight / 100 * 2.5).toFixed(1);
            levelText.textContent = `${amount}L / 2.5L`;
        }
    });
});

// Contact Form Handling
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(contactForm);
        const name = contactForm.querySelector('input[type="text"]').value;
        const email = contactForm.querySelector('input[type="email"]').value;
        const message = contactForm.querySelector('textarea').value;
        
        // Simple validation
        if (!name || !email || !message) {
            showNotification('Lütfen tüm alanları doldurun.', 'error');
            return;
        }
        
        // Simulate form submission
        const submitButton = contactForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Gönderiliyor...';
        submitButton.disabled = true;
        
        setTimeout(() => {
            showNotification('Mesajınız başarıyla gönderildi!', 'success');
            contactForm.reset();
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }, 2000);
    });
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.background = '#4CAF50';
            break;
        case 'error':
            notification.style.background = '#f44336';
            break;
        default:
            notification.style.background = '#2196F3';
    }
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Parallax Effect for Hero Section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const parallaxElements = document.querySelectorAll('.wave');
    
    parallaxElements.forEach((element, index) => {
        const speed = 0.5 + (index * 0.1);
        element.style.transform = `translateX(-50%) rotate(${scrolled * speed * 0.1}deg)`;
    });
});

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: rippleAnimation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes rippleAnimation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .add-btn {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Lazy Loading for Images (if any images are added later)
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
lazyLoadImages();

// Smooth scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add scroll to top button (optional)
const scrollToTopBtn = document.createElement('button');
scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
scrollToTopBtn.className = 'scroll-to-top';
scrollToTopBtn.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: var(--gradient-water);
    border: none;
    color: white;
    font-size: 18px;
    cursor: pointer;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
`;

document.body.appendChild(scrollToTopBtn);

scrollToTopBtn.addEventListener('click', scrollToTop);

// Show/hide scroll to top button
window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        scrollToTopBtn.style.opacity = '1';
        scrollToTopBtn.style.visibility = 'visible';
    } else {
        scrollToTopBtn.style.opacity = '0';
        scrollToTopBtn.style.visibility = 'hidden';
    }
});

// Add hover effects to download buttons
const downloadButtons = document.querySelectorAll('.download-btn');
downloadButtons.forEach(button => {
    button.addEventListener('mouseenter', () => {
        button.style.transform = 'translateY(-3px) scale(1.02)';
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.transform = 'translateY(0) scale(1)';
    });
});

// Performance optimization: Debounce scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Apply debounce to scroll events
const debouncedScrollHandler = debounce(() => {
    // Navbar scroll effect
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    // Scroll to top button
    if (window.scrollY > 300) {
        scrollToTopBtn.style.opacity = '1';
        scrollToTopBtn.style.visibility = 'visible';
    } else {
        scrollToTopBtn.style.opacity = '0';
        scrollToTopBtn.style.visibility = 'hidden';
    }
}, 10);

window.addEventListener('scroll', debouncedScrollHandler);

// Add keyboard navigation support
document.addEventListener('keydown', (e) => {
    // ESC key closes mobile menu
    if (e.key === 'Escape' && navMenu.classList.contains('active')) {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    }
    
    // Arrow keys for carousel navigation
    if (e.key === 'ArrowLeft') {
        currentSlide = currentSlide > 0 ? currentSlide - 1 : totalSlides - 1;
        showSlide(currentSlide);
    } else if (e.key === 'ArrowRight') {
        currentSlide = (currentSlide + 1) % totalSlides;
        showSlide(currentSlide);
    }
});

// Add focus management for accessibility
const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

function trapFocus(element) {
    const focusableContent = element.querySelectorAll(focusableElements);
    const firstFocusableElement = focusableContent[0];
    const lastFocusableElement = focusableContent[focusableContent.length - 1];

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusableElement) {
                    lastFocusableElement.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusableElement) {
                    firstFocusableElement.focus();
                    e.preventDefault();
                }
            }
        }
    });
}

// Initialize focus trap for mobile menu when active
const mobileMenuObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            if (navMenu.classList.contains('active')) {
                trapFocus(navMenu);
            }
        }
    });
});

mobileMenuObserver.observe(navMenu, { attributes: true });

// Reviews Carousel
document.addEventListener('DOMContentLoaded', () => {
    const reviewsTrack = document.getElementById('reviewsTrack');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (reviewsTrack && prevBtn && nextBtn) {
        let currentIndex = 0;
        const reviewCards = reviewsTrack.querySelectorAll('.review-card');
        const totalCards = reviewCards.length;
        const cardsToShow = window.innerWidth <= 768 ? 1 : (window.innerWidth <= 1024 ? 2 : 3);
        const cardWidth = 350 + 30; // card width + gap
        
        // Auto scroll functionality
        let autoScrollInterval;
        
        function updateCarousel() {
            const translateX = -(currentIndex * cardWidth);
            reviewsTrack.style.transform = `translateX(${translateX}px)`;
            
            // Update button states
            prevBtn.disabled = currentIndex === 0;
            nextBtn.disabled = currentIndex >= totalCards - cardsToShow;
        }
        
        function nextSlide() {
            if (currentIndex < totalCards - cardsToShow) {
                currentIndex++;
            } else {
                currentIndex = 0; // Loop back to start
            }
            updateCarousel();
        }
        
        function prevSlide() {
            if (currentIndex > 0) {
                currentIndex--;
            } else {
                currentIndex = totalCards - cardsToShow; // Loop to end
            }
            updateCarousel();
        }
        
        function startAutoScroll() {
            autoScrollInterval = setInterval(nextSlide, 4000);
        }
        
        function stopAutoScroll() {
            clearInterval(autoScrollInterval);
        }
        
        // Event listeners
        nextBtn.addEventListener('click', () => {
            stopAutoScroll();
            nextSlide();
            startAutoScroll();
        });
        
        prevBtn.addEventListener('click', () => {
            stopAutoScroll();
            prevSlide();
            startAutoScroll();
        });
        
        // Pause auto-scroll on hover
        reviewsTrack.addEventListener('mouseenter', stopAutoScroll);
        reviewsTrack.addEventListener('mouseleave', startAutoScroll);
        
        // Touch/swipe support for mobile
        let startX = 0;
        let endX = 0;
        
        reviewsTrack.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            stopAutoScroll();
        });
        
        reviewsTrack.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diffX = startX - endX;
            
            if (Math.abs(diffX) > 50) { // Minimum swipe distance
                if (diffX > 0) {
                    nextSlide();
                } else {
                    prevSlide();
                }
            }
            startAutoScroll();
        });
        
        // Responsive updates
        window.addEventListener('resize', () => {
            const newCardsToShow = window.innerWidth <= 768 ? 1 : (window.innerWidth <= 1024 ? 2 : 3);
            if (currentIndex >= totalCards - newCardsToShow) {
                currentIndex = Math.max(0, totalCards - newCardsToShow);
            }
            updateCarousel();
        });
        
        // Initialize
        updateCarousel();
        startAutoScroll();
    }
});

// Water Calculator Functions
let currentStep = 1;
let calculatorData = {};

function nextStep() {
    // Validate current step
    if (!validateStep(currentStep)) {
        return;
    }
    
    // Collect data from current step
    collectStepData(currentStep);
    
    // Move to next step
    if (currentStep < 3) {
        const currentStepEl = document.querySelector(`.form-step[data-step="${currentStep}"]`);
        const nextStepEl = document.querySelector(`.form-step[data-step="${currentStep + 1}"]`);
        
        currentStepEl.classList.remove('active');
        nextStepEl.classList.add('active');
        
        currentStep++;
        
        // Update phone preview
        updatePhonePreview();
    }
}

function prevStep() {
    if (currentStep > 1) {
        const currentStepEl = document.querySelector(`.form-step[data-step="${currentStep}"]`);
        const prevStepEl = document.querySelector(`.form-step[data-step="${currentStep - 1}"]`);
        
        currentStepEl.classList.remove('active');
        prevStepEl.classList.add('active');
        
        currentStep--;
    }
}

function validateStep(step) {
    const ageInput = document.getElementById('age');
    const weightInput = document.getElementById('weight');
    const heightInput = document.getElementById('height');
    const genderInputs = document.querySelectorAll('input[name="gender"]');
    const activitySelect = document.getElementById('activity');
    
    if (step === 1) {
        // Validate age, weight, height
        if (!ageInput.value || ageInput.value < 1 || ageInput.value > 120) {
            showError('Lütfen geçerli bir yaş girin (1-120)');
            focusInputWithDelay(ageInput);
            return false;
        }
        
        if (!weightInput.value || weightInput.value < 1 || weightInput.value > 300) {
            showError('Lütfen geçerli bir kilo girin (1-300 kg)');
            focusInputWithDelay(weightInput);
            return false;
        }
        
        if (!heightInput.value || heightInput.value < 50 || heightInput.value > 250) {
            showError('Lütfen geçerli bir boy girin (50-250 cm)');
            focusInputWithDelay(heightInput);
            return false;
        }
    }
    
    if (step === 2) {
        // Validate gender and activity
        let genderSelected = false;
        genderInputs.forEach(input => {
            if (input.checked) genderSelected = true;
        });
        
        if (!genderSelected) {
            showError('Lütfen cinsiyetinizi seçin');
            return false;
        }
        
        if (!activitySelect.value) {
            showError('Lütfen aktivite seviyenizi seçin');
            focusInputWithDelay(activitySelect);
            return false;
        }
    }
    
    return true;
}

// Helper function for mobile input focus
function focusInputWithDelay(input) {
    setTimeout(() => {
        if (input) {
            input.focus();
            input.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'center' 
            });
            
            // Add visual highlight for mobile
            input.style.transform = 'scale(1.05)';
            input.style.borderColor = '#ff5252';
            input.style.boxShadow = '0 0 0 3px rgba(255, 82, 82, 0.3)';
            
            setTimeout(() => {
                input.style.transform = '';
                input.style.borderColor = '';
                input.style.boxShadow = '';
            }, 2000);
        }
    }, 300);
}

function collectStepData(step) {
    if (step === 1) {
        calculatorData.age = parseInt(document.getElementById('age').value);
        calculatorData.weight = parseFloat(document.getElementById('weight').value);
        calculatorData.height = parseInt(document.getElementById('height').value);
    }
    
    if (step === 2) {
        const genderInputs = document.querySelectorAll('input[name="gender"]');
        genderInputs.forEach(input => {
            if (input.checked) calculatorData.gender = input.value;
        });
        calculatorData.activity = document.getElementById('activity').value;
    }
}

function calculateWater() {
    // Validate step 2
    if (!validateStep(2)) {
        return;
    }
    
    // Collect final data
    collectStepData(2);
    
    // Calculate water intake
    const result = calculateDailyWaterIntake(calculatorData);
    
    // Show result
    showResult(result);
    
    // Move to result step
    const currentStepEl = document.querySelector(`.form-step[data-step="${currentStep}"]`);
    const resultStepEl = document.querySelector(`.form-step[data-step="3"]`);
    
    currentStepEl.classList.remove('active');
    resultStepEl.classList.add('active');
    
    currentStep = 3;
}

function calculateDailyWaterIntake(data) {
    const { age, weight, height, gender, activity } = data;
    
    // Base calculation: 35ml per kg body weight
    let baseWater = weight * 35;
    
    // Gender adjustment
    if (gender === 'male') {
        baseWater *= 1.05; // Men need slightly more
    } else {
        baseWater *= 1.0; // Base for women
    }
    
    // Age adjustment
    if (age < 18) {
        baseWater *= 1.1; // Growing teens need more
    } else if (age > 65) {
        baseWater *= 0.95; // Elderly need slightly less
    }
    
    // Activity level adjustment
    const activityMultipliers = {
        sedentary: 1.0,
        light: 1.1,
        moderate: 1.3,
        active: 1.5,
        extra: 1.7
    };
    
    baseWater *= activityMultipliers[activity] || 1.0;
    
    // Convert to liters and round to 1 decimal
    const dailyLiters = Math.round((baseWater / 1000) * 10) / 10;
    
    // Ensure reasonable range (1.5L - 5.0L)
    const finalAmount = Math.max(1.5, Math.min(5.0, dailyLiters));
    
    return {
        amount: finalAmount,
        cups: Math.round(finalAmount * 4), // ~250ml per cup
        message: getPersonalizedMessage(data, finalAmount)
    };
}

function getPersonalizedMessage(data, amount) {
    const { age, gender, activity, weight } = data;
    
    let message = `Harika! Senin için hesaplanan günlük su ihtiyacı ${amount} litre. `;
    
    if (activity === 'sedentary') {
        message += "Masa başında çalıştığın için düzenli aralıklarla su içmeyi unutma! ";
    } else if (activity === 'active' || activity === 'extra') {
        message += "Aktif yaşam tarzın nedeniyle daha fazla su içmen gerekiyor. ";
    }
    
    if (age < 25) {
        message += "Genç yaşta sağlıklı alışkanlıklar edinmek harika! ";
    } else if (age > 50) {
        message += "Yaşla birlikte hidrasyon daha da önemli hale geliyor. ";
    }
    
    message += "Bu hesaplama genel bir rehber - kişisel ihtiyaçların için uygulamada detaylı takip yapabilirsin!";
    
    return message;
}

function showResult(result) {
    // Update result display
    document.getElementById('dailyAmount').textContent = result.amount;
    document.getElementById('resultMessage').textContent = result.message;
    
    // Update phone preview target
    document.getElementById('targetAmount').textContent = result.amount + 'L';
    
    // Mobile-specific celebration animation
    if (window.innerWidth <= 768) {
        addMobileCelebration();
    }
    
    // Animate water fill with mobile optimization
    setTimeout(() => {
        const waterFill = document.getElementById('waterFill');
        if (waterFill) {
            waterFill.style.height = '80%';
            waterFill.style.animation = 'mobileWaterFill 2s cubic-bezier(0.4, 0, 0.2, 1)';
        }
        
        // Animate number count-up
        animateCountUp(result.amount);
        
        // Mobile haptic feedback for success
        if ('vibrate' in navigator) {
            navigator.vibrate([50, 30, 50, 30, 100]);
        }
    }, 500);
    
    // Update progress ring in phone preview
    const progressPercentage = Math.round((1.6 / result.amount) * 100);
    updateProgressRing(progressPercentage);
}

function addMobileCelebration() {
    // Create floating celebration elements
    const celebrationContainer = document.createElement('div');
    celebrationContainer.className = 'mobile-celebration';
    celebrationContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1000;
    `;
    
    document.body.appendChild(celebrationContainer);
    
    // Create water drops celebration
    for (let i = 0; i < 8; i++) {
        const drop = document.createElement('div');
        drop.style.cssText = `
            position: absolute;
            width: 15px;
            height: 15px;
            background: linear-gradient(45deg, #00bcd4, #4fc3f7);
            border-radius: 0 50% 50% 50%;
            transform: rotate(-45deg);
            left: ${Math.random() * 100}%;
            top: -20px;
            animation: mobileCelebrationDrop ${2 + Math.random() * 2}s ease-out forwards;
            animation-delay: ${i * 0.2}s;
        `;
        celebrationContainer.appendChild(drop);
    }
    
    // Add celebration styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes mobileCelebrationDrop {
            0% {
                transform: rotate(-45deg) translateY(0) scale(1);
                opacity: 1;
            }
            100% {
                transform: rotate(-45deg) translateY(100vh) scale(0.5);
                opacity: 0;
            }
        }
        
        @keyframes mobileWaterFill {
            0% {
                height: 0%;
                transform: scale(1);
            }
            50% {
                transform: scale(1.02);
            }
            100% {
                height: 80%;
                transform: scale(1);
            }
        }
    `;
    document.head.appendChild(style);
    
    // Remove celebration after animation
    setTimeout(() => {
        celebrationContainer.remove();
        style.remove();
    }, 6000);
}

function animateCountUp(targetAmount) {
    const amountEl = document.getElementById('dailyAmount');
    const startAmount = 0;
    const duration = 2000;
    const startTime = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentAmount = startAmount + (targetAmount - startAmount) * easeOut;
        
        amountEl.textContent = Math.round(currentAmount * 10) / 10;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

function updateProgressRing(percentage) {
    const progressRing = document.getElementById('previewProgress');
    if (progressRing) {
        const degrees = (percentage / 100) * 360;
        progressRing.parentElement.style.background = 
            `conic-gradient(#00bcd4 0deg, #00bcd4 ${degrees}deg, rgba(255,255,255,0.2) ${degrees}deg)`;
        
        const progressText = progressRing.parentElement.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = percentage + '%';
        }
    }
}

function updatePhonePreview() {
    // Add subtle animation to phone preview when step changes
    const phonePreview = document.querySelector('.phone-preview');
    if (phonePreview) {
        phonePreview.style.transform = 'scale(0.95) rotateY(5deg)';
        setTimeout(() => {
            phonePreview.style.transform = 'scale(1) rotateY(0deg)';
        }, 300);
    }
}

function restartCalculator() {
    // Reset to step 1
    const allSteps = document.querySelectorAll('.form-step');
    allSteps.forEach(step => step.classList.remove('active'));
    
    const firstStep = document.querySelector('.form-step[data-step="1"]');
    firstStep.classList.add('active');
    
    currentStep = 1;
    calculatorData = {};
    
    // Clear form inputs
    document.getElementById('age').value = '';
    document.getElementById('weight').value = '';
    document.getElementById('height').value = '';
    
    const genderInputs = document.querySelectorAll('input[name="gender"]');
    genderInputs.forEach(input => input.checked = false);
    
    document.getElementById('activity').selectedIndex = 0;
    
    // Reset animations
    const waterFill = document.getElementById('waterFill');
    if (waterFill) {
        waterFill.style.height = '0%';
    }
    
    // Reset phone preview
    updateProgressRing(65);
    document.getElementById('targetAmount').textContent = '2.5L';
}

function showError(message) {
    // Create or update error message
    let errorEl = document.querySelector('.error-message');
    
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.style.cssText = `
            background: rgba(255, 82, 82, 0.9);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            font-size: 0.9rem;
            text-align: center;
            animation: shake 0.5s ease-in-out;
        `;
        
        const currentStep = document.querySelector('.form-step.active');
        currentStep.insertBefore(errorEl, currentStep.firstChild);
    }
    
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    // Auto hide after 4 seconds
    setTimeout(() => {
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }, 4000);
    
    // Add shake animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);
}

// Initialize calculator when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set initial state
    currentStep = 1;
    calculatorData = {};
    
    // Add input event listeners for better UX
    const inputs = document.querySelectorAll('#calculatorForm input, #calculatorForm select');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            // Hide error message when user starts typing
            const errorEl = document.querySelector('.error-message');
            if (errorEl) {
                errorEl.style.display = 'none';
            }
        });
    });
    
    // Add enter key support for form progression
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const activeStep = document.querySelector('.form-step.active');
            if (activeStep) {
                const stepNumber = parseInt(activeStep.dataset.step);
                if (stepNumber === 1) {
                    nextStep();
                } else if (stepNumber === 2) {
                    calculateWater();
                } else if (stepNumber === 3) {
                    restartCalculator();
                }
            }
        }
    });
    
    // Mobile-specific enhancements
    if (window.innerWidth <= 768) {
        initializeMobileEnhancements();
    }
    
    // Responsive adjustments on resize
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            initializeMobileEnhancements();
        }
    });
});

// Mobile-specific functions
function initializeMobileEnhancements() {
    // Add touch ripple effects
    addTouchRippleEffects();
    
    // Enhanced mobile animations
    addMobileAnimations();
    
    // Improve touch scrolling
    improveTouchScrolling();
    
    // Add mobile-specific gestures
    addMobileGestures();
}

function addTouchRippleEffects() {
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
    
    buttons.forEach(button => {
        button.addEventListener('touchstart', function(e) {
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.touches[0].clientX - rect.left - size / 2;
            const y = e.touches[0].clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: mobileRipple 0.6s linear;
                pointer-events: none;
            `;
            
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes mobileRipple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

function addMobileAnimations() {
    // Enhanced step transitions for mobile
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'mobileSlideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            }
        });
    }, { threshold: 0.1 });
    
    // Observe form groups
    const formGroups = document.querySelectorAll('.form-group');
    formGroups.forEach(group => observer.observe(group));
    
    // Add stagger animation to form elements
    const inputs = document.querySelectorAll('.form-input, .form-select');
    inputs.forEach((input, index) => {
        input.addEventListener('focus', function() {
            this.style.animation = `mobileFocusBounce 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)`;
            this.style.animationDelay = `${index * 0.05}s`;
        });
    });
    
    // Gender option animations
    const genderOptions = document.querySelectorAll('.gender-option');
    genderOptions.forEach((option, index) => {
        option.addEventListener('touchstart', function() {
            this.style.animation = `mobileGenderSelect 0.4s cubic-bezier(0.4, 0, 0.2, 1)`;
            this.style.animationDelay = `${index * 0.1}s`;
        });
    });
}

function improveTouchScrolling() {
    // Smooth scrolling for mobile
    const calculatorSection = document.querySelector('.water-calculator');
    if (calculatorSection) {
        calculatorSection.style.cssText += `
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
        `;
    }
    
    // Fix mobile input issues
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach((input, index) => {
        // Remove zoom prevention that might block touching
        input.removeAttribute('data-last-touch');
        
        // Ensure inputs are touchable
        input.style.pointerEvents = 'auto';
        input.style.touchAction = 'manipulation';
        input.style.position = 'relative';
        input.style.zIndex = '10';
        
        // Add touch events for better mobile interaction
        input.addEventListener('touchstart', function(e) {
            // Force focus on touch
            e.stopPropagation();
            this.focus();
        }, { passive: false });
        
        input.addEventListener('touchend', function(e) {
            e.stopPropagation();
        }, { passive: false });
        
        // Special handling for iOS
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            input.addEventListener('click', function(e) {
                e.stopPropagation();
                this.focus();
            });
        }
    });
    
    // Fix label clicking on mobile
    const labels = document.querySelectorAll('label');
    labels.forEach(label => {
        label.addEventListener('touchstart', function(e) {
            const forAttr = this.getAttribute('for');
            if (forAttr) {
                const input = document.getElementById(forAttr);
                if (input) {
                    e.preventDefault();
                    setTimeout(() => {
                        input.focus();
                        input.click();
                    }, 50);
                }
            }
        }, { passive: false });
    });
    
    // Ensure form doesn't interfere with input touching
    const formSteps = document.querySelectorAll('.form-step');
    formSteps.forEach(step => {
        step.style.pointerEvents = 'auto';
        step.style.position = 'relative';
        step.style.zIndex = '5';
    });
}

function addMobileGestures() {
    let startX = 0;
    let startY = 0;
    
    const calculatorForm = document.getElementById('calculatorForm');
    if (!calculatorForm) return;
    
    // Touch swipe gestures for step navigation
    calculatorForm.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    });
    
    calculatorForm.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;
        
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        
        const diffX = startX - endX;
        const diffY = startY - endY;
        
        // Only trigger if horizontal swipe is more significant than vertical
        if (Math.abs(diffX) > Math.abs(diffY)) {
            if (Math.abs(diffX) > 50) { // Minimum swipe distance
                if (diffX > 0 && currentStep < 3) {
                    // Swipe left - next step
                    nextStep();
                } else if (diffX < 0 && currentStep > 1) {
                    // Swipe right - previous step
                    prevStep();
                }
            }
        }
        
        startX = 0;
        startY = 0;
    });
}

// Enhanced mobile validation with haptic feedback
function showError(message) {
    // Create or update error message
    let errorEl = document.querySelector('.error-message');
    
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.style.cssText = `
            background: rgba(255, 82, 82, 0.9);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            font-size: 0.9rem;
            text-align: center;
            animation: mobileErrorSlide 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 20px rgba(255, 82, 82, 0.3);
        `;
        
        const currentStep = document.querySelector('.form-step.active');
        currentStep.insertBefore(errorEl, currentStep.firstChild);
    }
    
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    // Mobile haptic feedback
    if ('vibrate' in navigator) {
        navigator.vibrate([100, 50, 100]);
    }
    
    // Enhanced mobile shake animation
    const activeStep = document.querySelector('.form-step.active');
    activeStep.style.animation = 'mobileShakeError 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
    
    // Auto hide after 4 seconds
    setTimeout(() => {
        if (errorEl) {
            errorEl.style.animation = 'mobileErrorSlideOut 0.3s ease-in-out';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 300);
        }
    }, 4000);
    
    // Add mobile-specific error animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes mobileErrorSlide {
            0% {
                transform: translateY(-20px) scale(0.9);
                opacity: 0;
            }
            100% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
        }
        
        @keyframes mobileErrorSlideOut {
            0% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
            100% {
                transform: translateY(-20px) scale(0.9);
                opacity: 0;
            }
        }
        
        @keyframes mobileShakeError {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        
        @keyframes mobileFocusBounce {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes mobileGenderSelect {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

function showFacebookFeedback() {
    const notification = document.createElement('div');
    notification.className = 'facebook-feedback';
    notification.innerHTML = `
        <div class="facebook-feedback-content">
            <div class="facebook-feedback-icon">
                <i class="fab fa-facebook"></i>
            </div>
            <div class="facebook-feedback-text">
                <span>🚀 Facebook'ta takip etmeyi unutmayın!</span>
            </div>
        </div>
    `;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        max-width: 300px;
        background: linear-gradient(135deg, #1877F2, #4267B2);
        color: white;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(24, 119, 242, 0.3);
        z-index: 10001;
        transform: translateY(-100px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateY(-100px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 400);
    }, 3000);
}

console.log('Su Takip website loaded successfully! 💧');

// Initialize admin system and news loading
document.addEventListener('DOMContentLoaded', function() {
    // Add logo click event for admin access
    const navLogo = document.querySelector('.nav-logo');
    if (navLogo) {
        navLogo.addEventListener('click', handleLogoClick);
        navLogo.style.cursor = 'pointer';
        navLogo.title = 'Admin erişimi için 10 kere tıklayın';
    }

    // Load news from localStorage on page load
    setTimeout(() => {
        loadNewsFromStorage();
    }, 1000);

    // Announcement Ticker
    const ticker = document.getElementById('announcementTicker');
    const tickerClose = document.getElementById('tickerClose');
    if (ticker && tickerClose) {
        const closed = sessionStorage.getItem('ticker_closed');
        if (closed) {
            ticker.classList.add('hidden');
        } else {
            document.body.classList.add('ticker-active');
        }
        tickerClose.addEventListener('click', function() {
            ticker.classList.add('hidden');
            document.body.classList.remove('ticker-active');
            sessionStorage.setItem('ticker_closed', '1');
        });
    }
});
