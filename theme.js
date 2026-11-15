(function () {
    var STORAGE_KEY = 'color-scheme';

    function getSavedPref() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            if (v === 'light' || v === 'dark' || v === 'system') return v;
        } catch (e) {}
        return 'dark';
    }

    function applyColorScheme(pref) {
        var meta = document.querySelector('meta[name="color-scheme"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.name = 'color-scheme';
            document.head.prepend(meta);
        }
        if (pref === 'light' || pref === 'dark') {
            meta.content = pref;
            document.documentElement.dataset.theme = pref;
        } else {
            meta.content = 'light dark';
            delete document.documentElement.dataset.theme;
        }
        try {
            window.dispatchEvent(new CustomEvent('heuristics:themechange', { detail: { pref: pref } }));
        } catch (e) {}
    }

    var currentPref = getSavedPref();
    applyColorScheme(currentPref);

    function createSwitchMarkup() {
        var wrap = document.createElement('div');
        wrap.className = 'theme-switch';
        wrap.setAttribute('role', 'group');
        wrap.setAttribute('aria-label', 'Режим отображения сайта');
        wrap.innerHTML =
            '<button type="button" class="theme-switch-btn" data-theme-btn="light" title="Светлый режим"><span aria-hidden="true">☀</span><span class="sr-only">Светлый режим</span></button>' +
            '<button type="button" class="theme-switch-btn" data-theme-btn="dark" title="Ночной режим"><span aria-hidden="true">☾</span><span class="sr-only">Ночной режим</span></button>' +
            '<button type="button" class="theme-switch-btn auto" data-theme-btn="system" title="Автоматически как в системе"><span>Авто</span></button>';
        return wrap;
    }

    function mountSwitch() {
        var headerInner = document.querySelector('.header-inner');
        var nav = document.querySelector('.nav');
        if (!nav || !headerInner) return;

        // 1. Desktop theme switch inside .nav (.desk-theme-toggle)
        var deskHolder = nav.querySelector('.desk-theme-toggle');
        if (!deskHolder) {
            deskHolder = document.createElement('span');
            deskHolder.className = 'desk-theme-toggle';
            var existing = nav.querySelector('.theme-switch');
            if (existing) {
                deskHolder.appendChild(existing);
            } else {
                deskHolder.appendChild(createSwitchMarkup());
            }
            nav.appendChild(deskHolder);
        }

        // 2. Mobile controls (.mob-nav-controls) before .nav inside .header-inner
        var mobControls = headerInner.querySelector('.mob-nav-controls');
        if (!mobControls) {
            mobControls = document.createElement('div');
            mobControls.className = 'mob-nav-controls';
            mobControls.appendChild(createSwitchMarkup());

            var menuBtn = document.createElement('button');
            menuBtn.type = 'button';
            menuBtn.className = 'mob-menu-btn';
            menuBtn.setAttribute('aria-expanded', 'false');
            menuBtn.setAttribute('aria-label', 'Меню навигации');
            menuBtn.textContent = '☰ Меню';
            mobControls.appendChild(menuBtn);

            headerInner.insertBefore(mobControls, nav);

            function setMenuOpen(open) {
                nav.classList.toggle('mob-open', open);
                menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
                menuBtn.textContent = open ? '✕' : '☰ Меню';
            }

            menuBtn.addEventListener('click', function () {
                setMenuOpen(!nav.classList.contains('mob-open'));
            });

            nav.addEventListener('click', function (e) {
                if (e.target.closest('a')) {
                    setMenuOpen(false);
                }
            });

            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && nav.classList.contains('mob-open')) {
                    setMenuOpen(false);
                }
            });
        }

        function updateAllSwitches(pref) {
            var btns = headerInner.querySelectorAll('[data-theme-btn]');
            btns.forEach(function (b) {
                var mode = b.getAttribute('data-theme-btn');
                var isActive = mode === pref;
                b.classList.toggle('active', isActive);
                b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });
        }

        headerInner.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-theme-btn]');
            if (!btn) return;
            var next = btn.getAttribute('data-theme-btn');
            currentPref = next;
            applyColorScheme(next);
            updateAllSwitches(next);
            try {
                localStorage.setItem(STORAGE_KEY, next);
            } catch (err) {}
        });

        updateAllSwitches(currentPref);

        window.addEventListener('storage', function (e) {
            if (e.key !== STORAGE_KEY) return;
            var next = (e.newValue === 'light' || e.newValue === 'dark' || e.newValue === 'system') ? e.newValue : 'dark';
            currentPref = next;
            applyColorScheme(next);
            updateAllSwitches(next);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountSwitch);
    } else {
        mountSwitch();
    }
})();
