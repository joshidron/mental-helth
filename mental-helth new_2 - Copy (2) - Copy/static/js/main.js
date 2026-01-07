// Main JS logic
document.addEventListener('DOMContentLoaded', function () {
    const lang = new URLSearchParams(window.location.search).get('lang') || localStorage.getItem('preferred_language') || 'en';

    // Apply translations function if elements exist
    applyTranslations(lang);
});

function applyTranslations(lang) {
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        const text = getTranslation(key, lang);
        if (text) {
            if (element.tagName === 'INPUT' && element.getAttribute('placeholder')) {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        }
    });
}
