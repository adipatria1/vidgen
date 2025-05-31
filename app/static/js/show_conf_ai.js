// app/static/js/show_conf_ai.js
console.log("show_conf_ai.js Parsing - vGlobalFuncDef");

// --- Referensi Elemen Form Utama (didefinisikan di dalam DOMContentLoaded nanti) ---
let narrativeSourceSelect, promptInputSection, fileUploadSection, aiProviderSelect,
    geminiApiKeySection, geminiModelSelectionSection, pollinationsModelSelectionSection,
    storyPromptTextarea, narrativeFileInput, numPartsInput, wordsPerPartInput,
    narrativeExpertiseSelect, narrativeToneSelect, narrativeFormatSelect,
    narrativeLanguageSelect, promptTemplateSelect, promptTemplateIdSection, styleOptionsSection;

// --- Fungsi untuk Mengontrol Visibilitas Form (didefinisikan di scope global window) ---
window.updateFormVisibilityBasedOnSelections = function() {
    // Ambil referensi elemen di sini, karena fungsi ini bisa dipanggil sebelum DOMContentLoaded di file ini selesai
    // Namun, idealnya DOMContentLoaded di file ini sudah selesai saat settings_manager.js memanggilnya.
    narrativeSourceSelect = narrativeSourceSelect || document.getElementById('narrative_source_select');
    aiProviderSelect = aiProviderSelect || document.getElementById('ai_provider_select');
    promptInputSection = promptInputSection || document.getElementById('prompt_input_section');
    fileUploadSection = fileUploadSection || document.getElementById('file_upload_section');
    geminiApiKeySection = geminiApiKeySection || document.getElementById('gemini_api_key_section');
    geminiModelSelectionSection = geminiModelSelectionSection || document.getElementById('gemini_model_selection_section');
    pollinationsModelSelectionSection = pollinationsModelSelectionSection || document.getElementById('pollinations_model_selection_section');
    styleOptionsSection = styleOptionsSection || document.getElementById('style_options_section');
    promptTemplateIdSection = promptTemplateIdSection || document.getElementById('prompt_template_id_section');
    storyPromptTextarea = storyPromptTextarea || document.getElementById('story_prompt');
    numPartsInput = numPartsInput || document.getElementById('num_parts');
    wordsPerPartInput = wordsPerPartInput || document.getElementById('words_per_part');
    promptTemplateSelect = promptTemplateSelect || document.getElementById('prompt_template_id');
    narrativeExpertiseSelect = narrativeExpertiseSelect || document.getElementById('narrative_expertise');
    narrativeToneSelect = narrativeToneSelect || document.getElementById('narrative_tone');
    narrativeFormatSelect = narrativeFormatSelect || document.getElementById('narrative_format');
    narrativeLanguageSelect = narrativeLanguageSelect || document.getElementById('narrative_language');
    narrativeFileInput = narrativeFileInput || document.getElementById('narrative_file');


    if (!narrativeSourceSelect || !aiProviderSelect) {
        console.warn("VISIBILITY_WARN: 'narrative_source_select' atau 'ai_provider_select' tidak ditemukan saat updateFormVisibility.");
        return;
    }

    const selectedNarrativeSource = narrativeSourceSelect.value;
    const isPromptNarrativeSource = (selectedNarrativeSource === 'prompt');
    const selectedAiProvider = aiProviderSelect.value;
    // console.log(`VISIBILITY_UPDATE: Source='${selectedNarrativeSource}', Provider='${selectedAiProvider}', isPromptSource=${isPromptNarrativeSource}`);

    const aiProviderGroup = aiProviderSelect.closest('.form-group');

    if (promptInputSection) promptInputSection.classList.toggle('hidden-input', !isPromptNarrativeSource);
    if (fileUploadSection) fileUploadSection.classList.toggle('hidden-input', isPromptNarrativeSource);
    if (aiProviderGroup) aiProviderGroup.classList.remove('hidden-input');
    
    if (geminiApiKeySection) geminiApiKeySection.classList.toggle('hidden-input', selectedAiProvider !== 'gemini');
    if (document.getElementById('gemini_api_key')) document.getElementById('gemini_api_key').required = (selectedAiProvider === 'gemini');
    
    if (geminiModelSelectionSection) geminiModelSelectionSection.classList.toggle('hidden-input', selectedAiProvider !== 'gemini');
    if (document.getElementById('gemini_model')) document.getElementById('gemini_model').required = (selectedAiProvider === 'gemini');

    if (pollinationsModelSelectionSection) pollinationsModelSelectionSection.classList.toggle('hidden-input', selectedAiProvider !== 'pollinations');
    if (document.getElementById('pollinations_text_model')) document.getElementById('pollinations_text_model').required = (selectedAiProvider === 'pollinations');
    
    const showPromptSpecificOptions = isPromptNarrativeSource;

    if (styleOptionsSection) styleOptionsSection.classList.toggle('hidden-input', !showPromptSpecificOptions);
    if (promptTemplateIdSection) promptTemplateIdSection.classList.toggle('hidden-input', !showPromptSpecificOptions);
    
    if (storyPromptTextarea && storyPromptTextarea.closest('.form-group')) {
        storyPromptTextarea.closest('.form-group').classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    if (numPartsInput && numPartsInput.closest('.form-group')) {
        numPartsInput.closest('.form-group').classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    if (wordsPerPartInput && wordsPerPartInput.closest('.form-group')) {
        wordsPerPartInput.closest('.form-group').classList.toggle('hidden-input', !showPromptSpecificOptions);
    }
    
    if (promptTemplateSelect) {
        promptTemplateSelect.disabled = !showPromptSpecificOptions;
        promptTemplateSelect.required = showPromptSpecificOptions; 
    }
    
    if (storyPromptTextarea) storyPromptTextarea.required = showPromptSpecificOptions;
    if (narrativeFileInput) narrativeFileInput.required = !isPromptNarrativeSource; 
    if (numPartsInput) numPartsInput.required = showPromptSpecificOptions;
    if (wordsPerPartInput) wordsPerPartInput.required = showPromptSpecificOptions; 
    
    if (narrativeExpertiseSelect) narrativeExpertiseSelect.required = showPromptSpecificOptions;
    if (narrativeToneSelect) narrativeToneSelect.required = showPromptSpecificOptions;
    if (narrativeFormatSelect) narrativeFormatSelect.required = showPromptSpecificOptions;
    if (narrativeLanguageSelect) narrativeLanguageSelect.required = showPromptSpecificOptions; 
    // console.log("VISIBILITY_DEBUG: updateFormVisibilityBasedOnSelections selesai dieksekusi.");
}


document.addEventListener('DOMContentLoaded', function() {
    console.log("show_conf_ai.js DOMContentLoaded - Event listeners dipasang.");
    // Ambil referensi elemen di dalam DOMContentLoaded untuk memastikan elemen sudah ada
    narrativeSourceSelect = document.getElementById('narrative_source_select'); 
    promptInputSection = document.getElementById('prompt_input_section'); 
    fileUploadSection = document.getElementById('file_upload_section');   
    aiProviderSelect = document.getElementById('ai_provider_select');
    geminiApiKeySection = document.getElementById('gemini_api_key_section'); 
    geminiModelSelectionSection = document.getElementById('gemini_model_selection_section'); 
    pollinationsModelSelectionSection = document.getElementById('pollinations_model_selection_section'); 
    storyPromptTextarea = document.getElementById('story_prompt');
    narrativeFileInput = document.getElementById('narrative_file'); 
    numPartsInput = document.getElementById('num_parts');
    wordsPerPartInput = document.getElementById('words_per_part'); 
    narrativeExpertiseSelect = document.getElementById('narrative_expertise');
    narrativeToneSelect = document.getElementById('narrative_tone');
    narrativeFormatSelect = document.getElementById('narrative_format');
    narrativeLanguageSelect = document.getElementById('narrative_language');
    promptTemplateSelect = document.getElementById('prompt_template_id');
    promptTemplateIdSection = document.getElementById('prompt_template_id_section'); 
    styleOptionsSection = document.getElementById('style_options_section'); 

    // Pasang event listener
    if (narrativeSourceSelect) {
        narrativeSourceSelect.addEventListener('change', window.updateFormVisibilityBasedOnSelections);
    }
    if (aiProviderSelect) {
        aiProviderSelect.addEventListener('change', window.updateFormVisibilityBasedOnSelections);
    }
    
    console.log("show_conf_ai.js: Event listener DOMContentLoaded selesai. Menunggu panggilan update UI dari settings_manager.");
});
