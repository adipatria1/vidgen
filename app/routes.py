from flask import Blueprint, render_template, request, jsonify, current_app, url_for
import os
import random
import uuid 
from werkzeug.utils import secure_filename

from . import gemini_handler
from . import pollinations_tts_handler 
from .pollinations_tts_handler import CONTENT_POLICY_ERROR_SIGNAL 
from . import pollinations_image_handler 
from . import pollinations_text_handler 
from . import video_creator 
from .utils import (
    split_text_into_chunks, api_delay, get_media_path, generate_unique_filename, 
    AVAILABLE_GEMINI_MODELS, DEFAULT_GEMINI_MODEL,
    POLLINATIONS_TEXT_MODELS, DEFAULT_POLLINATIONS_TEXT_MODEL, 
    POLLINATIONS_VOICES, DEFAULT_POLLINATIONS_VOICE, 
    POLLINATIONS_IMAGE_MODELS, DEFAULT_POLLINATIONS_IMAGE_MODEL,
    POLLINATIONS_ASPECT_RATIOS, DEFAULT_POLLINATIONS_ASPECT_RATIO,
    WORDS_PER_STORY_PART as DEFAULT_WORDS_PER_PART, 
    IMAGES_PER_PARAGRAPH_MIN, 
    IMAGES_PER_PARAGRAPH_MAX, 
    NARRATIVE_EXPERTISE_OPTIONS, DEFAULT_NARRATIVE_EXPERTISE,
    NARRATIVE_TONE_OPTIONS, DEFAULT_NARRATIVE_TONE,
    NARRATIVE_FORMAT_OPTIONS, DEFAULT_NARRATIVE_FORMAT,
    NARRATIVE_LANGUAGE_OPTIONS, DEFAULT_NARRATIVE_LANGUAGE,
    DEFAULT_EFFECTS_ENABLED, 
    DEFAULT_FADE_PROBABILITY,
    DEFAULT_ZOOM_IN_PROBABILITY, DEFAULT_ZOOM_OUT_PROBABILITY,
    DEFAULT_STATIC_PROBABILITY,
    DEFAULT_TTS_MAX_RETRIES,
    DEFAULT_IMAGE_MAX_RETRIES 
)
from . import prompt_template_utils as ptu

bp = Blueprint('main', __name__)

CHUNK_TEXT_DIR = "story_chunks" 
FULL_STORY_DIR = "full_stories" 
UPLOADED_NARRATIVES_DIR = "uploaded_narratives"

def ensure_media_dirs():
    if current_app:
        base_static_path = current_app.static_folder
        generated_media_base = os.path.join(base_static_path, "generated_media")
        os.makedirs(generated_media_base, exist_ok=True)
        for media_type in ["audio", "images", "videos", CHUNK_TEXT_DIR, FULL_STORY_DIR, UPLOADED_NARRATIVES_DIR]:
            path_to_create = get_media_path(media_type, '', base_dir_name="generated_media")
            os.makedirs(path_to_create, exist_ok=True)
        ptu.get_templates_filepath() 
    else:
        print("Peringatan: current_app tidak tersedia saat ensure_media_dirs dipanggil.")

@bp.route('/', methods=['GET'])
def index():
    """Menampilkan halaman utama dengan form input."""
    # Load templates and separate them by type
    all_templates = ptu.load_prompt_templates()
    
    return render_template(
        'index.html',
        gemini_models=AVAILABLE_GEMINI_MODELS, default_gemini_model=DEFAULT_GEMINI_MODEL,
        pollinations_text_models=POLLINATIONS_TEXT_MODELS, default_pollinations_text_model=DEFAULT_POLLINATIONS_TEXT_MODEL,
        pollinations_voices=POLLINATIONS_VOICES, default_voice=DEFAULT_POLLINATIONS_VOICE,
        pollinations_image_models=POLLINATIONS_IMAGE_MODELS, default_image_model=DEFAULT_POLLINATIONS_IMAGE_MODEL,
        pollinations_aspect_ratios=POLLINATIONS_ASPECT_RATIOS, default_aspect_ratio=DEFAULT_POLLINATIONS_ASPECT_RATIO,
        default_parts=1, words_per_story_part=DEFAULT_WORDS_PER_PART, 
        images_per_paragraph_min=IMAGES_PER_PARAGRAPH_MIN, images_per_paragraph_max=IMAGES_PER_PARAGRAPH_MAX, 
        narrative_expertise_options=NARRATIVE_EXPERTISE_OPTIONS, default_narrative_expertise=DEFAULT_NARRATIVE_EXPERTISE,
        narrative_tone_options=NARRATIVE_TONE_OPTIONS, default_narrative_tone=DEFAULT_NARRATIVE_TONE,
        narrative_format_options=NARRATIVE_FORMAT_OPTIONS, default_narrative_format=DEFAULT_NARRATIVE_FORMAT,
        narrative_language_options=NARRATIVE_LANGUAGE_OPTIONS, default_narrative_language=DEFAULT_NARRATIVE_LANGUAGE,
        prompt_templates=all_templates,
        default_effects_enabled=DEFAULT_EFFECTS_ENABLED,
        default_fade_probability=DEFAULT_FADE_PROBABILITY,
        default_zoom_in_probability=DEFAULT_ZOOM_IN_PROBABILITY,
        default_zoom_out_probability=DEFAULT_ZOOM_OUT_PROBABILITY,
        default_static_probability=DEFAULT_STATIC_PROBABILITY,
        default_tts_max_retries=DEFAULT_TTS_MAX_RETRIES,
        default_image_max_retries=DEFAULT_IMAGE_MAX_RETRIES 
    )

@bp.route('/generate_video', methods=['POST'])
def generate_video_route():
    """Endpoint untuk memulai proses generasi video dengan logika kondisional prompt gambar."""
    try:
        data = request.form
        files = request.files
        
        ai_provider = data.get('ai_provider', 'gemini') 
        print(f"Penyedia AI Narasi yang dipilih: {ai_provider}")

        gemini_api_key = None
        if ai_provider == 'gemini':
            gemini_api_key = data.get('gemini_api_key', os.environ.get('GEMINI_API_KEY'))
            if not gemini_api_key: return jsonify({"error": "Gemini API Key dibutuhkan jika memilih Gemini."}), 400
            if not gemini_handler.configure_gemini(gemini_api_key): return jsonify({"error": "Konfigurasi Gemini API Key gagal."}), 500
        
        narrative_source = data.get('narrative_source', 'prompt')
        selected_tts_voice = data.get('tts_voice', DEFAULT_POLLINATIONS_VOICE)
        tts_max_retries = int(data.get('tts_max_retries', DEFAULT_TTS_MAX_RETRIES)); tts_max_retries = max(0, min(tts_max_retries, 5))
        selected_image_model_for_pollinations = data.get('image_model', DEFAULT_POLLINATIONS_IMAGE_MODEL) 
        selected_aspect_ratio = data.get('aspect_ratio', DEFAULT_POLLINATIONS_ASPECT_RATIO)
        image_max_retries = int(data.get('image_max_retries', DEFAULT_IMAGE_MAX_RETRIES)); image_max_retries = max(0, min(image_max_retries, 5))
        images_per_chunk_min_input = int(data.get('images_per_chunk_min', IMAGES_PER_PARAGRAPH_MIN))
        images_per_chunk_max_input = int(data.get('images_per_chunk_max', IMAGES_PER_PARAGRAPH_MAX))
        images_per_chunk_min_input = max(1, min(images_per_chunk_min_input, 5))
        images_per_chunk_max_input = max(images_per_chunk_min_input, min(images_per_chunk_max_input, 5))
        character_description = data.get('character_description', None)
        effect_settings = { 
            "enabled": data.get('effects_enabled') == 'true',
            "fade_prob": int(data.get('fade_probability', DEFAULT_FADE_PROBABILITY)) / 100.0,
            "zoom_in_prob": int(data.get('zoom_in_probability', DEFAULT_ZOOM_IN_PROBABILITY)),
            "zoom_out_prob": int(data.get('zoom_out_probability', DEFAULT_ZOOM_OUT_PROBABILITY)),
            "static_prob": int(data.get('static_probability', DEFAULT_STATIC_PROBABILITY))
        }

        full_story_text = ""
        narrative_language = data.get('narrative_language', NARRATIVE_LANGUAGE_OPTIONS[DEFAULT_NARRATIVE_LANGUAGE]) 
        selected_gemini_model_for_text = data.get('gemini_model', DEFAULT_GEMINI_MODEL) 
        selected_pollinations_text_model = data.get('pollinations_text_model', DEFAULT_POLLINATIONS_TEXT_MODEL) 

        # Get image prompt template
        image_prompt_template_id = data.get('image_prompt_template_id')
        if not image_prompt_template_id:
            # Get default image template
            for template in ptu.load_prompt_templates():
                if template.get('is_default') and template.get('type') == 'image':
                    image_prompt_template_id = template['id']
                    break
        image_template = ptu.get_template_by_id(image_prompt_template_id)
        if not image_template:
            return jsonify({"error": "Template prompt untuk gambar tidak ditemukan."}), 404

        if narrative_source == 'file':
            print("\n--- TAHAP 1: MEMBACA NARASI DARI FILE UNGGAPAN ---")
            if 'narrative_file' not in files or not files.getlist('narrative_file')[0].filename : 
                return jsonify({"error": "Tidak ada file narasi yang dipilih untuk diunggah."}), 400
            
            full_story_text_parts = []
            for uploaded_file in files.getlist('narrative_file'): 
                if uploaded_file and uploaded_file.filename.endswith('.txt'):
                    try:
                        filename = secure_filename(uploaded_file.filename)
                        unique_filename_part = generate_unique_filename(prefix=os.path.splitext(filename)[0], extension="txt")
                        uploaded_filepath_part = get_media_path(UPLOADED_NARRATIVES_DIR, unique_filename_part)
                        uploaded_file.save(uploaded_filepath_part)
                        print(f"File narasi bagian '{uploaded_file.filename}' disimpan di: {uploaded_filepath_part}")
                        with open(uploaded_filepath_part, "r", encoding="utf-8") as f_part:
                            full_story_text_parts.append(f_part.read())
                    except Exception as e:
                        print(f"Error memproses file unggahan '{uploaded_file.filename}': {e}")
                else:
                    if uploaded_file and uploaded_file.filename:
                        print(f"Mengabaikan file '{uploaded_file.filename}' karena bukan .txt atau tidak valid.")
            
            if not full_story_text_parts:
                    return jsonify({"error": "Tidak ada file narasi .txt yang valid berhasil diproses."}), 400
            
            full_story_text = "\n\n".join(full_story_text_parts) 

            if not full_story_text.strip():
                return jsonify({"error": "Konten gabungan dari file narasi yang diunggah kosong."}), 400
            print(f"Narasi berhasil dibaca dan digabung dari file unggahan (Total Panjang: {len(full_story_text)} chars).")
        
        elif narrative_source == 'prompt':
            print("\n--- TAHAP 1: GENERASI NARASI DARI PROMPT ---")
            story_prompt_input = data.get('story_prompt')
            if not story_prompt_input: return jsonify({"error": "Story prompt tidak boleh kosong."}), 400
            num_parts = int(data.get('num_parts', 1))
            min_words_per_part = int(data.get('min_words_per_part', 100))
            max_words_per_part = int(data.get('max_words_per_part', 150))
            
            # Validasi input kata
            min_words_per_part = max(100, min(min_words_per_part, 5000))
            max_words_per_part = max(min_words_per_part, min(max_words_per_part, 5000))

            all_story_parts_text = []
            previous_summary = None

            for i in range(1, num_parts + 1):
                print(f"Memproses bagian cerita ke-{i} dari {num_parts} menggunakan {ai_provider}...")
                current_part_text = None
                
                if ai_provider == 'gemini':
                    narrative_expertise = data.get('narrative_expertise', NARRATIVE_EXPERTISE_OPTIONS[DEFAULT_NARRATIVE_EXPERTISE])
                    narrative_tone = data.get('narrative_tone', NARRATIVE_TONE_OPTIONS[DEFAULT_NARRATIVE_TONE])
                    narrative_format = data.get('narrative_format', NARRATIVE_FORMAT_OPTIONS[DEFAULT_NARRATIVE_FORMAT])
                    prompt_template_id = data.get('prompt_template_id')
                    if not prompt_template_id: return jsonify({"error": "Template prompt harus dipilih untuk Gemini."}), 400
                    selected_template = ptu.get_template_by_id(prompt_template_id)
                    if not selected_template: return jsonify({"error": f"Template ID '{prompt_template_id}' tidak ditemukan."}), 404
                    prompt_template_content = selected_template['content']
                    
                    template_fill_data = {
                        "expertise": narrative_expertise, 
                        "language": narrative_language, 
                        "tone": narrative_tone,
                        "format_style": narrative_format, 
                        "target_words": f"{min_words_per_part}-{max_words_per_part}",
                        "main_story_prompt": story_prompt_input,
                        "previous_summary_content": previous_summary if previous_summary else "", 
                        "character_description_content": character_description if character_description else ""
                    }
                    current_part_text = gemini_handler.generate_story_part_from_template(
                        gemini_api_key=gemini_api_key, 
                        model_name=selected_gemini_model_for_text, 
                        template_content=prompt_template_content, 
                        fill_data=template_fill_data, 
                        part_number=i
                    )
                elif ai_provider == 'pollinations':
                    system_prompt_pollinations = (
                        f"Anda adalah {data.get('narrative_expertise', NARRATIVE_EXPERTISE_OPTIONS[DEFAULT_NARRATIVE_EXPERTISE])}. "
                        f"Tuliskan cerita dengan nada {data.get('narrative_tone', NARRATIVE_TONE_OPTIONS[DEFAULT_NARRATIVE_TONE])} "
                        f"dalam format {data.get('narrative_format', NARRATIVE_FORMAT_OPTIONS[DEFAULT_NARRATIVE_FORMAT])}. "
                        f"Cerita harus dalam bahasa {narrative_language}. "
                        f"Targetkan antara {min_words_per_part} sampai {max_words_per_part} kata. "
                        f"Pastikan cerita aman untuk umum dan mematuhi kebijakan konten."
                    )
                    if previous_summary:
                        system_prompt_pollinations += f"\nIni adalah kelanjutan cerita. Ringkasan sebelumnya: {previous_summary}"
                    
                    current_part_text = pollinations_text_handler.generate_text_pollinations(
                        main_prompt=story_prompt_input, 
                        model=selected_pollinations_text_model,
                        system_prompt=system_prompt_pollinations,
                        private=True
                    )

                if not current_part_text or "Error:" in current_part_text: 
                    return jsonify({"error": f"Gagal menghasilkan bagian cerita ke-{i} dengan {ai_provider}."}), 500
                
                # Validasi jumlah kata
                word_count = len(current_part_text.split())
                if word_count < min_words_per_part or word_count > max_words_per_part:
                    print(f"Peringatan: Bagian cerita ke-{i} memiliki {word_count} kata (target: {min_words_per_part}-{max_words_per_part})")
                
                all_story_parts_text.append(current_part_text)

                if i < num_parts: 
                    if ai_provider == 'gemini':
                        previous_summary = gemini_handler.summarize_text(selected_gemini_model_for_text, current_part_text, language=narrative_language)
                    elif ai_provider == 'pollinations':
                        previous_summary = pollinations_text_handler.summarize_text_pollinations(
                            current_part_text, 
                            model=selected_pollinations_text_model, 
                            language=narrative_language
                        )
                    if not previous_summary or "Error:" in previous_summary: previous_summary = current_part_text[-500:] 
            
            full_story_text = "\n\n".join(all_story_parts_text)
            if not full_story_text.strip(): return jsonify({"error": "Gagal menghasilkan konten cerita dari prompt."}), 500
        else:
            return jsonify({"error": "Sumber narasi tidak valid."}), 400

        print("\n--- TAHAP 2: MEMECAH NARASI MENJADI CHUNKS ---")
        text_chunks = split_text_into_chunks(full_story_text, max_chars=600)
        if not text_chunks: return jsonify({"error": "Gagal memecah narasi menjadi chunks atau narasi kosong."}), 500
        
        chunk_file_paths = []
        for idx, chunk_content_to_save in enumerate(text_chunks):
            chunk_filename = generate_unique_filename(prefix=f"chunk_{idx+1}", extension="txt")
            chunk_filepath = get_media_path(CHUNK_TEXT_DIR, chunk_filename)
            try:
                with open(chunk_filepath, "w", encoding="utf-8") as f: f.write(chunk_content_to_save)
                chunk_file_paths.append(chunk_filepath)
            except IOError as e: print(f"Error menyimpan chunk ke-{idx+1}: {e}")
        
        if not chunk_file_paths and not text_chunks: 
             return jsonify({"error": "Tidak ada chunk teks yang berhasil diproses."}), 500
        print(f"Total {len(text_chunks)} chunks teks dibuat untuk diproses.")

        successful_audio_count = 0; failed_audio_count = 0; rewritten_text_count = 0
        successful_image_sets_count = 0; failed_image_sets_count = 0
        total_individual_images_generated = 0; total_individual_images_attempted = 0
        story_segments_for_video = []
        previous_chunk_for_context = None 

        for idx, original_chunk_text_content in enumerate(text_chunks):
            print(f"\nMemproses chunk ke-{idx + 1}/{len(text_chunks)}")
            if not original_chunk_text_content.strip(): continue
            
            current_chunk_text_for_tts = original_chunk_text_content 
            current_segment_data = {'chunk_text': original_chunk_text_content, 'audio_path': None, 'image_paths': []}
            
            tts_prompt = f"Baca text ini : \"{current_chunk_text_for_tts}\""
            audio_file_path = pollinations_tts_handler.generate_audio_pollinations(
                tts_prompt, selected_tts_voice, max_retries_override=tts_max_retries 
            )
            
            if audio_file_path == CONTENT_POLICY_ERROR_SIGNAL:
                gemini_model_for_rewrite = selected_gemini_model_for_text 
                rewritten_chunk_text = gemini_handler.rewrite_text_for_content_policy(
                    gemini_model_for_rewrite, original_chunk_text_content, language=narrative_language
                )
                if rewritten_chunk_text:
                    rewritten_text_count += 1
                    current_chunk_text_for_tts = rewritten_chunk_text 
                    tts_prompt_rewritten = f"Baca text ini : \"{current_chunk_text_for_tts}\""
                    audio_file_path = pollinations_tts_handler.generate_audio_pollinations(
                        tts_prompt_rewritten, selected_tts_voice, max_retries_override=tts_max_retries 
                    )
                else: audio_file_path = None 
            
            if audio_file_path and audio_file_path != CONTENT_POLICY_ERROR_SIGNAL : 
                current_segment_data['audio_path'] = audio_file_path
                print(f"  Audio untuk chunk ke-{idx + 1} BERHASIL disimpan di: {audio_file_path}")
                successful_audio_count += 1
            else: 
                print(f"  Audio untuk chunk ke-{idx + 1} GAGAL dibuat.")
                failed_audio_count += 1
            api_delay(int(os.environ.get("TTS_API_DELAY", 2)))

            num_images_target = random.randint(images_per_chunk_min_input, images_per_chunk_max_input)
            image_prompts = []

            if ai_provider == 'gemini':
                print(f"  Menggunakan Gemini ({selected_gemini_model_for_text}) untuk membuat {num_images_target} prompt gambar...")
                image_prompts = gemini_handler.generate_image_prompts_for_paragraph(
                    model_name=selected_gemini_model_for_text, 
                    current_chunk_text=original_chunk_text_content, 
                    num_prompts_target=num_images_target, 
                    character_details=character_description,
                    language="Inggris", 
                    previous_chunk_text=previous_chunk_for_context,
                    template_content=image_template['content'] if image_template else None
                )
            elif ai_provider == 'pollinations':
                print(f"  Menggunakan Pollinations Text API ({selected_pollinations_text_model}) untuk membuat {num_images_target} prompt gambar...")
                image_prompts = pollinations_text_handler.generate_image_prompts_via_pollinations(
                    model_name=selected_pollinations_text_model,
                    current_chunk_text=original_chunk_text_content,
                    num_prompts_target=num_images_target,
                    character_details=character_description, 
                    language_of_chunk=narrative_language, 
                    output_language="Inggris", 
                    previous_chunk_text=previous_chunk_for_context,
                    template_content=image_template['content'] if image_template else None
                )
            
            previous_chunk_for_context = original_chunk_text_content 
            
            prompts_generated_count = len(image_prompts) if image_prompts else 0
            total_individual_images_attempted += num_images_target 
            if not image_prompts:
                print(f"  Peringatan: Gagal membuat prompt gambar untuk chunk ke-{idx + 1} menggunakan {ai_provider}.")
            api_delay(int(os.environ.get("PROMPT_API_DELAY", 1))) 

            images_generated_for_this_chunk = 0
            if image_prompts and current_segment_data['audio_path']: 
                generated_image_paths_for_chunk = []
                for img_idx, img_prompt_text in enumerate(image_prompts):
                    image_file_path = pollinations_image_handler.generate_image_pollinations(
                        prompt=img_prompt_text, 
                        aspect_ratio_str=selected_aspect_ratio,
                        image_model=selected_image_model_for_pollinations, 
                        nologo=True, private=True, enhance=True,
                        max_retries_override=image_max_retries 
                    )
                    if image_file_path:
                        generated_image_paths_for_chunk.append(image_file_path)
                        total_individual_images_generated += 1
                        images_generated_for_this_chunk +=1
                    api_delay(int(os.environ.get("IMAGE_API_DELAY", 5))) 
                
                current_segment_data['image_paths'] = generated_image_paths_for_chunk
                if images_generated_for_this_chunk > 0: successful_image_sets_count += 1
                else: failed_image_sets_count += 1
            elif not image_prompts and current_segment_data['audio_path']: 
                failed_image_sets_count += 1
            
            if current_segment_data['audio_path'] and current_segment_data['image_paths']:
                story_segments_for_video.append(current_segment_data)
            else: 
                if current_segment_data['audio_path'] and os.path.exists(current_segment_data['audio_path']) and not current_segment_data['image_paths']:
                    try: os.remove(current_segment_data['audio_path'])
                    except OSError as e: print(f"  Error menghapus file audio {current_segment_data['audio_path']}: {e}")
        
        report = {
            "total_chunks_processed": len(text_chunks), 
            "audio_generated_successfully": successful_audio_count,
            "audio_generation_failed": failed_audio_count,
            "texts_rewritten_for_tts": rewritten_text_count, 
            "image_sets_with_at_least_one_image": successful_image_sets_count,
            "image_sets_completely_failed": failed_image_sets_count, 
            "total_individual_images_generated_successfully": total_individual_images_generated,
            "total_individual_images_attempted": total_individual_images_attempted,
            "total_individual_images_failed": total_individual_images_attempted - total_individual_images_generated
        }
        print("\n--- LAPORAN GENERASI MEDIA ---")
        for key, value in report.items(): print(f"  {key.replace('_', ' ').capitalize()}: {value}")
        if not story_segments_for_video: return jsonify({"error": "Tidak ada segmen yang berhasil diproses untuk video.", "report": report}), 500
        
        final_video_path = video_creator.create_video_from_parts(story_segments_for_video, effect_settings=effect_settings) 
        
        if final_video_path:
            base_video_name = os.path.basename(final_video_path)
            relative_path_for_url = f"generated_media/videos/{base_video_name}"
            relative_video_url = url_for('static', filename=relative_path_for_url)
            print(f"Video berhasil dibuat: {final_video_path}") 
            print(f"URL Video untuk klien: {relative_video_url}")
            return jsonify({
                "message": "Video berhasil dibuat!", 
                "video_url": relative_video_url, # URL ini yang akan digunakan oleh frontend
                "full_story_text_preview": full_story_text[:1000] + "...",
                "report": report
            })
        else: return jsonify({"error": "Gagal membuat video final.", "report": report}), 500

    except Exception as e:
        print(f"Error tidak terduga di endpoint /generate_video: {e}")
        import traceback; traceback.print_exc()
        partial_report = { "error_message": str(e) } 
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}", "report": partial_report}), 500