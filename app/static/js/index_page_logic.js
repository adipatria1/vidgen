// app/static/js/index_page_logic.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("index_page_logic.js Loaded (UI Logic Only) - vRemoveFileButtonFix");

    // --- Referensi Elemen Form ---
    const effectsEnabledCheckbox = document.getElementById('effects_enabled');
    const effectProbabilitiesFieldset = document.getElementById('effect_probabilities_fieldset');

    const motionSliders = [
        document.getElementById('zoom_in_probability'),
        document.getElementById('zoom_out_probability'),
        document.getElementById('static_probability') 
    ].filter(slider => slider !== null); 
    const totalMotionProbabilityDisplay = document.getElementById('totalMotionProbability');

    const minImagesInput = document.getElementById('images_per_chunk_min');
    const maxImagesInput = document.getElementById('images_per_chunk_max');

    const minWordsInput = document.getElementById('min_words_per_part');
    const maxWordsInput = document.getElementById('max_words_per_part');

    const dropZone = document.getElementById('narrative_file_drop_zone');
    const fileInputForDropZone = document.getElementById('narrative_file'); 
    const fileListDisplay = document.getElementById('file_list_display');

    // --- Fungsi Update UI Tambahan (Slider, Efek, dll.) ---
    window.updateTotalMotionDisplay = function() { 
        if (!totalMotionProbabilityDisplay || motionSliders.some(s => s === null)) {
            return;
        }
        let total = 0;
        motionSliders.forEach(slider => { 
            if(slider && slider.value) { 
                total += parseInt(slider.value); 
            }
        });
        totalMotionProbabilityDisplay.textContent = total + '%';
        totalMotionProbabilityDisplay.style.color = (total !== 100) ? '#e74c3c' : '#2ecc71';
        totalMotionProbabilityDisplay.style.fontWeight = (total !== 100) ? 'bold' : 'normal';
    }
    
    function handleMotionSliderInput(sliderElement) { 
        if (sliderElement && sliderElement.nextElementSibling && sliderElement.nextElementSibling.tagName === 'OUTPUT') {
            sliderElement.nextElementSibling.value = sliderElement.value + '%';
        }
        if (typeof window.updateTotalMotionDisplay === 'function') {
            window.updateTotalMotionDisplay();
        }
    }

    motionSliders.forEach(slider => { 
        if(slider) {
            slider.addEventListener('input', function() {
                handleMotionSliderInput(this); 
            });
        }
    });
    
    window.toggleEffectProbabilities = function() { 
         if (effectsEnabledCheckbox && effectProbabilitiesFieldset) {
            effectProbabilitiesFieldset.style.display = effectsEnabledCheckbox.checked ? 'block' : 'none';
        }
    }
    if (effectsEnabledCheckbox) { 
        effectsEnabledCheckbox.addEventListener('change', window.toggleEffectProbabilities);
    }

    // --- Validasi Min/Max Gambar ---
    if(minImagesInput && maxImagesInput) { 
        function validateImageCounts() {
            const minVal = parseInt(minImagesInput.value);
            const maxVal = parseInt(maxImagesInput.value);
            if (minVal > maxVal) { maxImagesInput.value = minVal; }
            if (parseInt(maxImagesInput.value) < parseInt(maxImagesInput.min)) { maxImagesInput.value = maxImagesInput.min; }
            if (parseInt(minImagesInput.value) > parseInt(minImagesInput.max)) { minImagesInput.value = minImagesInput.max; }
        }
        minImagesInput.addEventListener('change', validateImageCounts);
        maxImagesInput.addEventListener('change', validateImageCounts);
    }

    // --- Validasi Min/Max Kata ---
    if(minWordsInput && maxWordsInput) {
        function validateWordCounts() {
            const minVal = parseInt(minWordsInput.value);
            const maxVal = parseInt(maxWordsInput.value);
            if (minVal > maxVal) { maxWordsInput.value = minVal; }
            if (parseInt(maxWordsInput.value) < parseInt(maxWordsInput.min)) { maxWordsInput.value = maxWordsInput.min; }
            if (parseInt(minWordsInput.value) > parseInt(minWordsInput.max)) { minWordsInput.value = minWordsInput.max; }
        }
        minWordsInput.addEventListener('change', validateWordCounts);
        maxWordsInput.addEventListener('change', validateWordCounts);
    }

    // --- Drag and Drop File Upload dengan Fitur Hapus ---
    if (dropZone && fileInputForDropZone && fileListDisplay) {
        console.log("Drag and drop elements found. Attaching listeners.");
        const fileUploadSectionRef = document.getElementById('file_upload_section'); 

        // Menyimpan file yang valid untuk diunggah (yang akan dikirim ke server)
        let currentValidFiles = new DataTransfer();

        dropZone.addEventListener('click', (e) => {
            if (fileUploadSectionRef && !fileUploadSectionRef.classList.contains('hidden-input')) {
                 fileInputForDropZone.click(); 
            }
        });

        fileInputForDropZone.addEventListener('change', (event) => {
            console.log("File input changed, handling files:", event.target.files);
            // Saat memilih file baru, kita reset daftar file yang valid dan di UI
            currentValidFiles = new DataTransfer(); 
            Array.from(event.target.files).forEach(file => {
                if (file.type === "text/plain") {
                    currentValidFiles.items.add(file);
                }
            });
            fileInputForDropZone.files = currentValidFiles.files; // Update input file dengan yang valid saja
            renderFileList(); // Render ulang daftar di UI
        });

        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault(); 
            if (fileUploadSectionRef && !fileUploadSectionRef.classList.contains('hidden-input')) {
                dropZone.classList.add('dragover');
            }
        });
        dropZone.addEventListener('dragleave', (event) => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (event) => {
            event.preventDefault(); 
            if (fileUploadSectionRef && !fileUploadSectionRef.classList.contains('hidden-input')) {
                dropZone.classList.remove('dragover');
                currentValidFiles = new DataTransfer(); // Reset untuk file yang di-drop
                Array.from(event.dataTransfer.files).forEach(file => {
                    if (file.type === "text/plain") {
                        currentValidFiles.items.add(file);
                    }
                });
                fileInputForDropZone.files = currentValidFiles.files; // Update input file
                renderFileList(); // Render ulang daftar di UI
            }
        });

        function renderFileList() {
            fileListDisplay.innerHTML = ''; 
            if (currentValidFiles.files && currentValidFiles.files.length > 0) {
                const ul = document.createElement('ul');
                Array.from(currentValidFiles.files).forEach(file => {
                    const li = document.createElement('li');
                    li.textContent = `${file.name} (${(file.size / 1024).toFixed(2)} KB) `;
                    
                    const removeButton = document.createElement('button');
                    removeButton.textContent = 'x';
                    removeButton.type = 'button'; 
                    removeButton.classList.add('remove-file-btn'); 
                    removeButton.dataset.fileName = file.name; 
                    
                    removeButton.addEventListener('click', function() {
                        removeFileFromDataTransfer(file.name);
                    });
                    
                    li.appendChild(removeButton);
                    ul.appendChild(li);
                });
                fileListDisplay.appendChild(ul);
            } else { 
                fileListDisplay.textContent = 'Tidak ada file .txt dipilih.';
                // Pastikan input file juga dikosongkan jika tidak ada file valid
                const emptyDt = new DataTransfer();
                fileInputForDropZone.files = emptyDt.files;
            }
        }

        function removeFileFromDataTransfer(fileNameToRemove) {
            console.log("Mencoba menghapus file dari DataTransfer:", fileNameToRemove);
            const newFiles = new DataTransfer();
            let fileRemoved = false;

            for (let i = 0; i < currentValidFiles.files.length; i++) {
                const currentFile = currentValidFiles.files[i];
                if (currentFile.name !== fileNameToRemove) {
                    newFiles.items.add(currentFile);
                } else {
                    fileRemoved = true;
                }
            }

            if (fileRemoved) {
                currentValidFiles = newFiles; 
                fileInputForDropZone.files = currentValidFiles.files; 
                renderFileList(); // Re-render daftar UI
                console.log("File dihapus dari daftar dan input:", fileNameToRemove);
            } else {
                console.warn("File tidak ditemukan dalam daftar untuk dihapus:", fileNameToRemove);
            }
        }
    } else {
        console.warn("Satu atau lebih elemen untuk drag-and-drop TIDAK ditemukan.");
    }
    
    // --- Panggil Fungsi Inisialisasi UI ---
    if (typeof window.updateFormVisibilityBasedOnSelections === 'function') {
        window.updateFormVisibilityBasedOnSelections(); 
    }
    if (typeof window.toggleEffectProbabilities === 'function') {
        window.toggleEffectProbabilities(); 
    }
    if (typeof window.updateTotalMotionDisplay === 'function') {
        window.updateTotalMotionDisplay(); 
    }
    
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        if (slider.nextElementSibling && slider.nextElementSibling.tagName === 'OUTPUT') {
            slider.nextElementSibling.value = slider.value + '%';
        }
        handleMotionSliderInput(slider); 
    });
    console.log("index_page_logic.js UI enhancements initialization complete.");
});