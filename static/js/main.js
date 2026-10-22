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

document.querySelectorAll('.post-item[data-detail-url]').forEach((card) => {
    card.addEventListener('click', (event) => {
        if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
            return;
        }
        if (event.target.closest('a, button, video, input, textarea, select, [contenteditable="true"]') || window.getSelection()?.toString()) {
            return;
        }
        window.location.assign(card.dataset.detailUrl);
    });
});

document.querySelectorAll('.like-button').forEach((button) => {
    button.addEventListener('click', async () => {
        if (button.disabled) {
            return;
        }

        const card = button.closest('.post-item');
        const errorMessage = card.querySelector('.like-error');
        const likeCount = card.querySelector('.like-count');
        const wasLiked = button.getAttribute('aria-pressed') === 'true';
        const previousCount = Number(likeCount.dataset.count);
        const renderState = (liked, count) => {
            button.setAttribute('aria-pressed', String(liked));
            button.setAttribute('aria-label', liked ? 'Unlike' : 'Like');
            likeCount.dataset.count = count;
            likeCount.textContent = count > 999 ? '999+' : count;
        };

        button.disabled = true;
        errorMessage.hidden = true;
        renderState(!wasLiked, previousCount + (wasLiked ? -1 : 1));

        try {
            const response = await fetch(button.dataset.likeUrl, {
                method: wasLiked ? 'DELETE' : 'POST',
                headers: { 'X-CSRF-Token': button.dataset.csrfToken },
            });

            if (response.status === 401) {
                renderState(wasLiked, previousCount);
                window.location.assign('/login');
                return;
            }

            const state = await response.json();
            if (!response.ok) {
                throw new Error(state.error || 'Unable to update your like. Please try again.');
            }

            renderState(state.liked, state.like_count);
        } catch (error) {
            renderState(wasLiked, previousCount);
            errorMessage.textContent = error.message;
            errorMessage.hidden = false;
        } finally {
            button.disabled = false;
        }
    });
});

document.querySelectorAll('.subscribe-button').forEach((button) => {
    button.addEventListener('click', async () => {
        if (button.disabled) {
            return;
        }

        const profile = button.closest('.profile');
        const subscribeCount = profile.querySelector('.subscribe-count');
        const wasSubscribed = button.getAttribute('aria-pressed') === 'true';
        const previousCount = Number(subscribeCount.dataset.count);
        const renderState = (subscribed, count) => {
            button.setAttribute('aria-pressed', String(subscribed));
            button.setAttribute('aria-label', subscribed ? 'Unsubscribe' : 'Subscribe');
            subscribeCount.dataset.count = count;
            subscribeCount.textContent = count;
            button.textContent = subscribed ? 'Unsubscribe' : 'Subscribe';
        };

        button.disabled = true;
        renderState(!wasSubscribed, previousCount + (wasSubscribed ? -1 : 1));

        try {
            const response = await fetch(button.dataset.subscribeUrl, {
                method: wasSubscribed ? 'DELETE' : 'POST',
                headers: { 'X-CSRF-Token': button.dataset.csrfToken },
            });

            if (response.status === 401) {
                renderState(wasSubscribed, previousCount);
                window.location.assign('/login');
                return;
            }

            const state = await response.json();
            if (!response.ok) {
                throw new Error(state.error || 'Unable to update your subscription. Please try again.');
            }

            renderState(state.subscribed, state.subscribed_count);
        } catch (error) {
            renderState(wasSubscribed, previousCount);
        } finally {
            button.disabled = false;
        }
    });
});

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
