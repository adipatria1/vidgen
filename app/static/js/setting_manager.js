// app/static/js/settings_manager.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("[SettingsManager] DOMContentLoaded - Mulai.");

    const formId = 'videoForm'; 
    const formElement = document.getElementById(formId);

    if (!formElement) {
        console.error(`[SettingsManager] Form dengan ID '${formId}' tidak ditemukan.`);
        return;
    }

    const fieldsToPersist = [
        'ai_provider_select', 'gemini_api_key', 'narrative_source_select', 
        'prompt_template_id', 'story_prompt', 'num_parts', 'words_per_part', 
        'gemini_model', 'pollinations_text_model', 'narrative_expertise', 
        'narrative_tone', 'narrative_format', 'narrative_language', 
        'character_description', 'tts_voice', 'tts_max_retries', 
        'image_model', 'aspect_ratio', 'image_max_retries', 
        'images_per_chunk_min', 'images_per_chunk_max', 'effects_enabled', 
        'fade_probability', 'zoom_in_probability', 'zoom_out_probability', 
        'static_probability'
    ];

    function saveSetting(id, value) {
        try {
            localStorage.setItem(id, value);
        } catch (e) {
            console.error(`[SettingsManager] Error menyimpan pengaturan untuk '${id}':`, e);
        }
    }

    function loadAndApplySetting(id) {
        const element = document.getElementById(id);
        if (!element) {
            return; 
        }
        const savedValue = localStorage.getItem(id);
        if (savedValue !== null) {
            if (element.type === 'checkbox') {
                element.checked = (savedValue === 'true');
            } else {
                element.value = savedValue;
            }
            // Langsung update output jika ini adalah slider
            if (element.type === 'range' && element.nextElementSibling && element.nextElementSibling.tagName === 'OUTPUT') {
                element.nextElementSibling.value = element.value + '%';
            }
            // Picu event 'change' untuk select/checkbox, dan 'input' untuk yang lain
            const eventName = (element.type === 'select-one' || element.type === 'checkbox') ? 'change' : 'input';
            element.dispatchEvent(new Event(eventName, { bubbles: true, cancelable: true }));
        }
    }

    console.log("[SettingsManager] Memulai pemuatan semua pengaturan...");
    fieldsToPersist.forEach(id => {
        loadAndApplySetting(id);
    });
    console.log("[SettingsManager] Selesai memuat semua pengaturan dari localStorage.");

    // Setelah semua nilai dimuat dan event awal dipicu, panggil fungsi update UI global.
    // Beri jeda yang cukup untuk memastikan skrip lain (show_conf_ai.js dan index_page_logic.js) 
    // sudah mendefinisikan fungsinya ke window.
    setTimeout(function() {
        console.log("[SettingsManager] Mencoba memanggil fungsi update UI global setelah jeda...");
        if (typeof window.updateFormVisibilityBasedOnSelections === 'function') {
            console.log("[SettingsManager] Memanggil updateFormVisibilityBasedOnSelections.");
            window.updateFormVisibilityBasedOnSelections();
        } else {
            console.warn("[SettingsManager] Fungsi window.updateFormVisibilityBasedOnSelections TIDAK DITEMUKAN.");
        }
        
        if (typeof window.toggleEffectProbabilities === 'function') { 
            console.log("[SettingsManager] Memanggil toggleEffectProbabilities.");
            window.toggleEffectProbabilities();
        } else {
            console.warn("[SettingsManager] Fungsi window.toggleEffectProbabilities TIDAK DITEMUKAN.");
        }

        if (typeof window.updateTotalMotionDisplay === 'function') { 
            console.log("[SettingsManager] Memanggil updateTotalMotionDisplay.");
            window.updateTotalMotionDisplay();
        } else {
             console.warn("[SettingsManager] Fungsi window.updateTotalMotionDisplay TIDAK DITEMUKAN.");
        }
        console.log("[SettingsManager] Inisialisasi UI setelah load settings selesai.");
    }, 200); // Jeda 200ms, bisa disesuaikan jika perlu

    // Pasang event listener untuk menyimpan perubahan selanjutnya
    fieldsToPersist.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            let eventType = 'input'; 
            if (element.type === 'select-one' || element.type === 'checkbox') {
                eventType = 'change';
            }
            if (element.id === 'gemini_api_key' && element.type === 'password') {
                eventType = 'blur'; 
                 element.addEventListener('paste', () => { 
                    setTimeout(() => saveSetting(element.id, element.value), 50);
                });
            }
            element.addEventListener(eventType, function(event) {
                const currentElement = event.target;
                let valueToSave;
                if (currentElement.type === 'checkbox') {
                    valueToSave = currentElement.checked;
                } else {
                    valueToSave = currentElement.value;
                }
                if (currentElement.id === 'gemini_api_key' && currentElement.type === 'password') {
                    setTimeout(() => { 
                        saveSetting(currentElement.id, currentElement.value);
                    }, 100);
                } else {
                    saveSetting(currentElement.id, valueToSave);
                }
            });
        }
    });
    console.log("[SettingsManager] Pemasangan event listener untuk penyimpanan selesai.");
});
