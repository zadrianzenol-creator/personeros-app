// ============================================================
// IRONFORGE GYM — Main JavaScript
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // --- AOS Init ---
    AOS.init({
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 80
    });

    // --- Navbar Scroll ---
    const nav = document.getElementById('gymNav');
    let lastScroll = 0;

    window.addEventListener('scroll', function () {
        const scrollY = window.scrollY;
        if (scrollY > 80) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
        lastScroll = scrollY;
    });

    // --- Active Nav Link ---
    const navLinks = document.querySelectorAll('.gym-nav-links a');
    const sections = document.querySelectorAll('section[id]');

    window.addEventListener('scroll', function () {
        let current = '';
        sections.forEach(function (section) {
            const top = section.offsetTop - 150;
            if (window.scrollY >= top) {
                current = section.getAttribute('id');
            }
        });
        navLinks.forEach(function (link) {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });

    // --- Count Up Animation ---
    function animateCountUp(el) {
        const target = parseInt(el.getAttribute('data-target'));
        const duration = 2000;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);

            el.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = target.toLocaleString();
            }
        }

        requestAnimationFrame(update);
    }

    const countUpElements = document.querySelectorAll('.count-up');
    let counted = false;

    function checkCountUp() {
        if (counted) return;
        const hero = document.querySelector('.gym-hero');
        const rect = hero.getBoundingClientRect();
        if (rect.bottom > 0 && rect.top < window.innerHeight) {
            counted = true;
            countUpElements.forEach(animateCountUp);
        }
    }

    // Initial check
    setTimeout(checkCountUp, 500);
    window.addEventListener('scroll', checkCountUp);

    // --- Schedule Tabs ---
    const tabs = document.querySelectorAll('.schedule-tab');
    const cards = document.querySelectorAll('.schedule-card');

    function filterSchedule(day) {
        cards.forEach(function (card) {
            const days = card.getAttribute('data-day');
            if (days && days.includes(day)) {
                card.classList.add('visible');
            } else {
                card.classList.remove('visible');
            }
        });
        tabs.forEach(function (t) {
            t.classList.remove('active');
            if (t.getAttribute('data-day') === day) {
                t.classList.add('active');
            }
        });
    }

    if (tabs.length > 0) {
        // Set initial day
        const initialDay = document.querySelector('.schedule-tab.active');
        if (initialDay) {
            filterSchedule(initialDay.getAttribute('data-day'));
        } else {
            filterSchedule('lun');
        }

        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                filterSchedule(tab.getAttribute('data-day'));
            });
        });
    }

    // --- Testimonials Slider ---
    const track = document.getElementById('testimonialTrack');
    const dots = document.querySelectorAll('.testimonial-btn');
    let currentSlide = 0;
    const totalSlides = dots.length;

    function goToSlide(index) {
        if (!track) return;
        currentSlide = index;
        track.style.transform = 'translateX(-' + (index * 100) + '%)';
        dots.forEach(function (dot, i) {
            dot.classList.toggle('active', i === index);
        });
    }

    if (dots.length > 0) {
        dots.forEach(function (dot) {
            dot.addEventListener('click', function () {
                goToSlide(parseInt(dot.getAttribute('data-slide')));
            });
        });

        // Auto-advance
        setInterval(function () {
            goToSlide((currentSlide + 1) % totalSlides);
        }, 5000);
    }

    // --- Mobile Menu ---
    const hamburger = document.getElementById('gymHamburger');
    const mobileMenu = document.getElementById('gymMobileMenu');
    const mobileClose = document.getElementById('gymMobileClose');

    function createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'gym-overlay';
        overlay.id = 'gymOverlay';
        document.body.appendChild(overlay);

        overlay.addEventListener('click', function () {
            closeMobileMenu();
        });

        return overlay;
    }

    let overlay = document.getElementById('gymOverlay') || createOverlay();

    function openMobileMenu() {
        mobileMenu.classList.add('open');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileMenu() {
        mobileMenu.classList.remove('open');
        overlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (hamburger) {
        hamburger.addEventListener('click', openMobileMenu);
    }

    if (mobileClose) {
        mobileClose.addEventListener('click', closeMobileMenu);
    }

    // Close mobile menu on link click
    const mobileLinks = mobileMenu ? mobileMenu.querySelectorAll('a') : [];
    mobileLinks.forEach(function (link) {
        link.addEventListener('click', closeMobileMenu);
    });

    // --- Smooth scroll for nav links ---
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const href = anchor.getAttribute('href');
            if (href === '#') return;
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- Contact Form ---
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = contactForm.querySelector('.btn-submit');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
            btn.disabled = true;

            setTimeout(function () {
                btn.innerHTML = '<i class="fas fa-check"></i> Mensaje Enviado';
                btn.style.background = 'linear-gradient(135deg, #10b981, #059669)';

                setTimeout(function () {
                    btn.innerHTML = originalText;
                    btn.style.background = '';
                    btn.disabled = false;
                    contactForm.reset();
                }, 3000);
            }, 1500);
        });
    }

});
