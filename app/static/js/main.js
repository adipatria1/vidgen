document.addEventListener('DOMContentLoaded', function() {
    const videoForm = document.getElementById('videoForm');
    const submitButton = document.getElementById('submitButton');
    const statusMessages = document.getElementById('statusMessages');
    const loader = document.getElementById('loader');
    const resultsArea = document.getElementById('resultsArea');
    const resultMessage = document.getElementById('resultMessage');
    const videoPlayerContainer = document.getElementById('videoPlayerContainer');
    const storyPreview = document.getElementById('storyPreview');
    
    // Buat elemen baru untuk menampilkan laporan
    const reportDisplayArea = document.createElement('div');
    reportDisplayArea.id = 'reportDisplayArea';
    // Styling dasar untuk reportDisplayArea bisa ditambahkan di CSS jika perlu
    // resultsArea.parentNode.insertBefore(reportDisplayArea, resultsArea.nextSibling); // Dipindahkan ke dalam blok sukses

    // Ambil nilai default dari elemen HTML jika ada, atau gunakan fallback
    const wordsPerPartElement = document.getElementById('words_per_part'); 
    const WORDS_PER_STORY_PART_JS = wordsPerPartElement ? (parseInt(wordsPerPartElement.value) || 3500) : 3500;
    // IMAGES_PER_PARAGRAPH_MIN_JS dan MAX_JS tidak digunakan di sini, bisa dihapus jika tidak relevan untuk estimasi

    if (videoForm) {
        videoForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            submitButton.disabled = true;
            loader.style.display = 'block';
            statusMessages.textContent = 'Memulai proses pembuatan video... Ini mungkin memakan waktu beberapa menit atau lebih.';
            
            // Sembunyikan dan kosongkan area hasil dan laporan sebelumnya
            resultsArea.style.display = 'none';
            videoPlayerContainer.innerHTML = ''; 
            storyPreview.textContent = '';
            if (document.getElementById('reportDisplayArea')) { // Cek jika reportDisplayArea sudah ada
                document.getElementById('reportDisplayArea').innerHTML = '';
                document.getElementById('reportDisplayArea').style.display = 'none';
            }


            const formData = new FormData(videoForm);
            
            const narrativeSource = formData.get('narrative_source');
            let estimatedTotalSeconds = 180; // Waktu dasar untuk pembuatan video

            if (narrativeSource === 'prompt') {
                const numParts = parseInt(formData.get('num_parts')) || 1;
                // Ambil target kata dari form, bukan konstanta JS lagi untuk estimasi
                const wordsPerPartForm = parseInt(formData.get('words_per_part')) || WORDS_PER_STORY_PART_JS;
                const estimatedParagraphsPerPart = wordsPerPartForm / 25; 
                const totalEstimatedParagraphs = numParts * estimatedParagraphsPerPart;
                estimatedTotalSeconds += (numParts * 60) + (totalEstimatedParagraphs * 15); // Perkiraan kasar
            } else {
                estimatedTotalSeconds += 300; 
            }
            const estimatedMinutes = Math.ceil(estimatedTotalSeconds / 60);
            statusMessages.textContent += `\nPerkiraan waktu proses: ~${estimatedMinutes} menit. Harap bersabar.`;

            try {
                const response = await fetch("/generate_video", { 
                    method: 'POST',
                    body: formData
                });

                const result = await response.json(); 

                // Pastikan reportDisplayArea ada sebelum mencoba menampilkannya
                let currentReportDisplayArea = document.getElementById('reportDisplayArea');
                if (!currentReportDisplayArea) {
                    currentReportDisplayArea = document.createElement('div');
                    currentReportDisplayArea.id = 'reportDisplayArea';
                    // Tambahkan style jika perlu, atau pastikan CSS menanganinya
                    resultsArea.parentNode.insertBefore(currentReportDisplayArea, resultsArea.nextSibling);
                }

                if (result.report) {
                    currentReportDisplayArea.style.display = 'block';
                    let reportHTML = '<h3>Laporan Generasi Media:</h3><ul>';
                    for (const key in result.report) {
                        if (result.report.hasOwnProperty(key)) {
                            const readableKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                            reportHTML += `<li><strong>${readableKey}:</strong> ${result.report[key]}</li>`;
                        }
                    }
                    reportHTML += '</ul>';
                    currentReportDisplayArea.innerHTML = reportHTML;
                } else {
                    currentReportDisplayArea.style.display = 'none';
                }


                if (response.ok && result.video_url) {
                    statusMessages.textContent = 'Video berhasil dibuat!';
                    resultMessage.textContent = result.message || 'Video telah selesai diproses.';
                    
                    // Kosongkan kontainer sebelum menambahkan video baru
                    videoPlayerContainer.innerHTML = ''; 
                    
                    const videoElement = document.createElement('video');
                    console.log('JavaScript: URL Video yang diterima dari server:', result.video_url); // Baris Debugging
                    videoElement.src = result.video_url;
                    videoElement.controls = true;
                    // Menggunakan CSS untuk styling lebih disarankan, tapi ini bisa untuk sementara
                    videoElement.style.width = "640px"; 
                    videoElement.style.maxWidth = "100%";
                    videoElement.style.display = "block"; // Pastikan video adalah block element
                    videoElement.style.margin = "10px auto"; // Contoh margin
                    
                    videoPlayerContainer.appendChild(videoElement);

                    if(result.full_story_text_preview) {
                        storyPreview.textContent = result.full_story_text_preview;
                    } else {
                        storyPreview.textContent = ''; // Kosongkan jika tidak ada preview
                    }
                    resultsArea.style.display = 'block';

                } else {
                    const errorMessage = result.error || 'Terjadi kesalahan yang tidak diketahui dari server.';
                    statusMessages.textContent = `Error: ${errorMessage}`;
                    resultMessage.textContent = `Gagal membuat video: ${errorMessage}`;
                    resultsArea.style.display = 'block'; 
                    videoPlayerContainer.innerHTML = ''; // Pastikan tidak ada sisa video player
                    storyPreview.textContent = ''; // Kosongkan preview cerita
                }

            } catch (error) {
                console.error('JavaScript: Error saat fetch atau proses JSON:', error);
                // Pastikan reportDisplayArea ada sebelum mencoba menyembunyikannya
                let currentReportDisplayAreaOnError = document.getElementById('reportDisplayArea');
                if (currentReportDisplayAreaOnError) {
                    currentReportDisplayAreaOnError.style.display = 'none'; 
                }

                if (error instanceof SyntaxError && error.message.includes("JSON")) {
                     statusMessages.textContent = `Error: Respons dari server bukan JSON yang valid. Kemungkinan ada error di server atau URL salah. Cek konsol server (Flask). Error klien: ${error.message}`;
                } else {
                    statusMessages.textContent = `Error pada sisi klien: ${error.message}. Periksa konsol untuk detail.`;
                }
                resultMessage.textContent = `Gagal menghubungi server atau terjadi error pada klien.`;
                resultsArea.style.display = 'block';
                videoPlayerContainer.innerHTML = ''; 
                storyPreview.textContent = ''; 
            } finally {
                submitButton.disabled = false;
                loader.style.display = 'none';
            }
        });
    }
    
    // Logika untuk toggle input narasi (bagian ini tampaknya duplikat dari show_conf_ai.js dan mungkin tidak diperlukan di sini jika show_conf_ai.js sudah berjalan dengan benar)
    // Jika show_conf_ai.js sudah menangani ini dengan baik, Anda bisa menghapus bagian di bawah ini dari main.js
    // Untuk sementara, saya akan biarkan dengan catatan.
    /*
    const narrativeSourceSelect = document.getElementById('narrative_source_select'); // Sudah ada di show_conf_ai.js
    const promptInputSection = document.getElementById('prompt_input_section');
    const fileUploadSection = document.getElementById('file_upload_section');
    const storyPromptTextarea = document.getElementById('story_prompt');
    const narrativeFileInput = document.getElementById('narrative_file');
    const numPartsInput = document.getElementById('num_parts');
    // const wordsPerPartInput = document.getElementById('words_per_part'); // Sudah ada di atas

    function toggleNarrativeInputSectionsBasedOnSource() { // Ganti nama fungsi agar unik jika diperlukan
        if (!narrativeSourceSelect) return; 

        const isPromptSource = narrativeSourceSelect.value === 'prompt';
        
        promptInputSection.classList.toggle('hidden-input', !isPromptSource);
        fileUploadSection.classList.toggle('hidden-input', isPromptSource);
        
        storyPromptTextarea.required = isPromptSource;
        // narrativeFileInput.required = !isPromptSource; // Diurus oleh show_conf_ai.js
        numPartsInput.required = isPromptSource;
        // wordsPerPartInput.required = isPromptSource; // Diurus oleh show_conf_ai.js
    }

    if (narrativeSourceSelect) {
        narrativeSourceSelect.addEventListener('change', toggleNarrativeInputSectionsBasedOnSource);
        // Panggil sekali saat load untuk set kondisi awal, jika show_conf_ai.js belum melakukannya.
        // Namun, settings_manager.js seharusnya sudah memicu show_conf_ai.js.
        // toggleNarrativeInputSectionsBasedOnSource(); 
    }
    */
});
