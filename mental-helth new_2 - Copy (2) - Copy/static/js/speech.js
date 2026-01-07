function speakText(key) {
    if (!('speechSynthesis' in window)) {
        alert('Text-to-speech is not supported in this browser.');
        return;
    }

    // Stop any current speech
    window.speechSynthesis.cancel();

    // Detect language
    const lang =
        new URLSearchParams(window.location.search).get('lang') ||
        localStorage.getItem('preferred_language') ||
        'en';

    // Get translated text
    let textToSpeak = "";
    try {
        textToSpeak = getTranslation(key, lang);
    } catch (e) {
        textToSpeak = key;
    }

    console.log("TTS Triggered");
    console.log("Language:", lang);
    console.log("Text:", textToSpeak);

    const utterance = new SpeechSynthesisUtterance(textToSpeak);

    // Language mapping with proper BCP 47 codes
    let langCode = 'en-US';
    if (lang === 'hi') langCode = 'hi-IN';
    if (lang === 'gu') langCode = 'gu-IN';

    utterance.lang = langCode;
    utterance.rate = 0.8; // Slower for better pronunciation
    utterance.pitch = 1;
    utterance.volume = 1;

    const speakNow = () => {
        const voices = window.speechSynthesis.getVoices();
        console.log("Available voices:", voices.map(v => `${v.name} (${v.lang})`));

        let selectedVoice = null;

        // 🔵 SPECIFIC VOICE SEARCH FOR GUJARATI
        if (lang === 'gu') {
            // Try different voice names for Gujarati
            const possibleGujaratiVoices = voices.filter(v => {
                const voiceLang = v.lang.toLowerCase();
                const voiceName = v.name.toLowerCase();
                return (
                    voiceLang.includes('gu') ||
                    voiceLang.includes('gujarati') ||
                    voiceName.includes('gujarati') ||
                    voiceName.includes('gu-in') ||
                    voiceName.includes('google gujarati') ||
                    voiceName.includes('microsoft zira') // Some systems use this
                );
            });

            if (possibleGujaratiVoices.length > 0) {
                // Prefer Google voices for better quality
                selectedVoice = possibleGujaratiVoices.find(v =>
                    v.name.toLowerCase().includes('google')
                ) || possibleGujaratiVoices[0];
                console.log("Gujarati voice found:", selectedVoice.name);
            } else {
                console.warn("No Gujarati voice found in system.");

                // Fallback strategy for Gujarati
                // Try Hindi as it might handle Devanagari script better
                const hindiVoice = voices.find(v => v.lang.includes('hi-IN') || v.lang.includes('hi'));
                if (hindiVoice) {
                    selectedVoice = hindiVoice;
                    console.log("Using Hindi voice as fallback for Gujarati");
                }
            }
        } else {
            // For Hindi and English, use standard selection
            // 1️⃣ Exact match
            selectedVoice = voices.find(v => v.lang === langCode);

            // 2️⃣ Partial match
            if (!selectedVoice) {
                const shortLang = langCode.split('-')[0];
                selectedVoice = voices.find(v => v.lang.startsWith(shortLang));
            }
        }

        // 3️⃣ Apply voice or fallback to default
        if (selectedVoice) {
            utterance.voice = selectedVoice;
            utterance.lang = selectedVoice.lang; // Use the voice's actual lang
            console.log("Using voice:", selectedVoice.name, "with lang:", selectedVoice.lang);
        } else {
            console.warn(`No ${lang} voice found. Using default voice.`);
            // Let browser use default voice
        }

        // 🎯 Add event listeners for debugging
        utterance.onstart = () => console.log("Speech started");
        utterance.onend = () => console.log("Speech ended");
        utterance.onerror = (event) => console.error("Speech error:", event.error);

        window.speechSynthesis.speak(utterance);
    };

    // 🚨 CRITICAL: Ensure voices are loaded
    if (window.speechSynthesis.getVoices().length === 0) {
        console.log("Waiting for voiceschanged event...");

        // Remove any existing listeners
        window.speechSynthesis.onvoiceschanged = null;

        // Set up one-time listener
        window.speechSynthesis.onvoiceschanged = () => {
            console.log("Voices changed event fired");
            window.speechSynthesis.onvoiceschanged = null; // Remove after firing
            speakNow();
        };

        // Safety timeout
        setTimeout(() => {
            if (window.speechSynthesis.getVoices().length > 0) {
                speakNow();
            } else {
                console.warn("Voice loading timeout. Attempting with available voices.");
                speakNow();
            }
        }, 2000);
    } else {
        speakNow();
    }
}

// 🚀 INITIAL VOICE LOADING HELPER (call this on page load)
function initializeVoices() {
    // Pre-load voices by calling getVoices() early
    const voices = window.speechSynthesis.getVoices();
    console.log("Pre-loaded voices:", voices.length);

    // Set up a global voice cache
    window.availableVoices = voices;

    // If no voices, listen for voiceschanged
    if (voices.length === 0) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.availableVoices = window.speechSynthesis.getVoices();
            console.log("Voices loaded on page load:", window.availableVoices.length);
        };
    }
}

// Call this when your page loads
document.addEventListener('DOMContentLoaded', initializeVoices);