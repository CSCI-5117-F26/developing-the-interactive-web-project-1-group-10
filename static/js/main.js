const menuBtn = document.getElementById('menuBtn');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const closeBtn = document.getElementById('sidebarClose');
const weatherBackground = document.getElementById('weatherBackground');
const currentWeather = document.getElementById('currentWeather');

const weatherForCode = (code) => {
    if ([0, 1].includes(code)) {
        return ['sun', 20, 0];
    }
    if ([2, 3].includes(code)) {
        return ['cloudy', 25, 0];
    }
    if ([45, 48].includes(code)) {
        return ['fog', 20, 0];
    }
    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) {
        return ['rain', [55, 57, 65, 67, 82].includes(code) ? 55 : 35, 5];
    }
    if ([71, 73, 75, 77, 85, 86].includes(code)) {
        return ['snow', [75, 86].includes(code) ? 50 : 30, 20];
    }
    if ([95, 96, 97, 99].includes(code)) {
        return ['thunderstorm', 45, 5];
    }
    return ['none', 0, 0];
};

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

const loadCurrentWeather = async () => {
    if (!weatherBackground || weatherBackground.dataset.weatherAuto !== 'true') {
        startWeatherEffects();
        return;
    }

    const query = new URLSearchParams({
        latitude: '44.9778',
        longitude: '-93.2650',
        current: 'weather_code,is_day',
        timezone: 'America/Chicago',
        forecast_days: '1',
    });

    try {
        const response = await fetch(`https://api.open-meteo.com/v1/forecast?${query}`);

        if (!response.ok) {
            throw new Error(`Weather request failed: ${response.status}`);
        }

        const forecast = await response.json();
        const code = Number(forecast.current.weather_code);

        if (!Number.isFinite(code)) {
            throw new Error('Weather response is missing the current weather code.');
        }

        const [effect, intensity, density] = weatherForCode(code);
        weatherBackground.dataset.weatherEffect = effect;
        weatherBackground.dataset.weatherIntensity = intensity;
        weatherBackground.dataset.weatherDensity = density;
        weatherBackground.dataset.weatherMode = forecast.current.is_day ? 'day' : 'night';
        currentWeather.textContent = `Current: ${effect[0].toUpperCase()}${effect.slice(1)}`;
        startWeatherEffects();
    } catch (error) {
        currentWeather.textContent = 'Current: Unavailable';
        console.warn('Unable to load current weather.', error);
    }
};

if (window.lucide) {
    window.lucide.createIcons();
}

loadCurrentWeather();

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
