const menuBtn = document.getElementById('menuBtn');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const closeBtn = document.getElementById('sidebarClose');
const weatherBackground = document.getElementById('weatherBackground');

const startWeatherEffects = () => {
    if (!weatherBackground || !window.WeatherEffectsJS) {
        return;
    }

    const effect = weatherBackground.dataset.weatherEffect;

    if (effect === 'none') {
        return;
    }

    const options = {
        container: weatherBackground,
        intensity: Number(weatherBackground.dataset.weatherIntensity),
        density: Number(weatherBackground.dataset.weatherDensity),
        mode: weatherBackground.dataset.weatherMode === 'night' ? 'night' : 'day',
    };

    if (effect === 'thunderstorm') {
        window.WeatherEffectsJS.mountRain(options);
        window.WeatherEffectsJS.mountLightning(options);
        return;
    }

    window.WeatherEffectsJS.createWeatherEffect(effect, options);
};

if (window.lucide) {
    window.lucide.createIcons();
}

startWeatherEffects();

if (menuBtn && sidebar && overlay && closeBtn) {
    let isOpen = false;

    const setMenuOpen = (open, restoreFocus = false) => {
        isOpen = open;
        sidebar.classList.toggle('open', open);
        overlay.classList.toggle('open', open);
        document.body.classList.toggle('menu-open', open);
        menuBtn.setAttribute('aria-expanded', String(open));
        sidebar.setAttribute('aria-hidden', String(!open));

        if (open) {
            closeBtn.focus();
        } else if (restoreFocus) {
            menuBtn.focus();
        }
    };

    menuBtn.addEventListener('click', () => {
        setMenuOpen(!isOpen);
    });

    overlay.addEventListener('click', () => {
        setMenuOpen(false, true);
    });

    closeBtn.addEventListener('click', () => {
        setMenuOpen(false, true);
    });

    sidebar.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => setMenuOpen(false));
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && isOpen) {
            setMenuOpen(false, true);
        }
    });
}
