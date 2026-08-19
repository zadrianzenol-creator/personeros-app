(function() {
    'use strict';

    // ─── Sidebar drawer (mobile) ───
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.getElementById('mobileOverlay');
    var hamburger = document.getElementById('btnHamburger');

    function toggleSidebar() {
        sidebar.classList.toggle('drawer-open');
        if (overlay) overlay.classList.toggle('active');
        closeProfile();
    }

    function closeSidebar() {
        sidebar.classList.remove('drawer-open');
        if (overlay) overlay.classList.remove('active');
    }

    if (overlay) {
        overlay.addEventListener('click', function() {
            closeSidebar();
            closeProfile();
        });
    }

    document.querySelectorAll('.sidebar-menu a').forEach(function(a) {
        a.addEventListener('click', closeSidebar);
    });

    if (hamburger) {
        hamburger.addEventListener('click', toggleSidebar);
    }

    // ─── Profile dropdown (mobile) ───
    var profileBtn = document.getElementById('btnProfile');
    var profileDropdown = document.getElementById('profileDropdown');
    var profileOpen = false;

    function closeProfile() {
        if (profileDropdown) profileDropdown.classList.remove('open');
        profileOpen = false;
    }

    if (profileBtn && profileDropdown) {
        profileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            profileOpen = !profileOpen;
            profileDropdown.classList.toggle('open', profileOpen);
            if (profileOpen) closeSidebar();
        });

        document.addEventListener('click', function(e) {
            if (profileOpen && !profileDropdown.contains(e.target) && e.target !== profileBtn) {
                closeProfile();
            }
        });
    }

    // ─── Auto-dismiss flash messages ───
    document.querySelectorAll('.flash-message').forEach(function(msg) {
        setTimeout(function() {
            msg.style.opacity = '0';
            msg.style.transition = 'opacity 0.3s ease';
            setTimeout(function() { msg.remove(); }, 300);
        }, 5000);
    });

    // ─── Fix sidebar height on mobile Safari ───
    function fixSidebarH() {
        if (sidebar && window.innerWidth <= 768) {
            sidebar.style.height = window.innerHeight + 'px';
        }
    }
    fixSidebarH();
    window.addEventListener('resize', fixSidebarH);

})();
