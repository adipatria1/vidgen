import google.generativeai as genai
import os
import re 
from app.utils import api_delay, DEFAULT_GEMINI_MODEL 

def configure_gemini(api_key):
    """Konfigurasi API Key Gemini."""
    if api_key:
        genai.configure(api_key=api_key)
        # print("Gemini API Key dikonfigurasi.") # Kurangi verbositas
        return True
    else:
        print("Peringatan: GEMINI_API_KEY tidak disediakan atau tidak ditemukan.")
        return False

def generate_text_content(model_name, prompt_text, temperature=0.7, max_output_tokens=8192):
    """
    Menghasilkan teks menggunakan model Gemini yang dipilih.
    """
    try:
        effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
        model = genai.GenerativeModel(effective_model_name)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = model.generate_content(
            prompt_text,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            ),
            safety_settings=safety_settings 
        )
        if not response.candidates: 
             block_reason = response.prompt_feedback.block_reason if hasattr(response, 'prompt_feedback') and response.prompt_feedback else "Tidak diketahui (kandidat kosong)"
             print(f"Peringatan: Teks dari Gemini mungkin diblokir. Alasan: {block_reason}")
             return None
        
        return response.text
    except Exception as e:
        print(f"Error saat menghasilkan teks dengan Gemini ({model_name if model_name else DEFAULT_GEMINI_MODEL}): {e}")
        generated_text = None
        # Cek apakah 'response' ada di scope lokal sebelum diakses
        if 'response' in locals() and hasattr(response, 'candidates') and response.candidates:
            try: 
                if response.candidates[0].content and response.candidates[0].content.parts:
                     generated_text = "".join(part.text for part in response.candidates[0].content.parts)
                     return generated_text
            except Exception as e_cand: 
                print(f"Tidak bisa mengambil teks dari kandidat: {e_cand}")
        return None 

def rewrite_text_for_content_policy(model_name, original_text, language="Indonesia", max_output_tokens=1024):
    """
    Menulis ulang teks agar sesuai dengan kebijakan konten, menjaga konteks asli.
    Menggunakan model_name yang diteruskan, atau default jika None.
    """
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    prompt = (
        f"Tulis ulang teks berikut agar sepenuhnya mematuhi kebijakan konten Azure OpenAI dan aman untuk umum. "
        f"Hindari semua topik, bahasa, atau skenario yang mungkin dianggap sensitif, menyinggung, atau berbahaya. "
        f"Pertahankan makna inti, konteks, dan alur cerita dari teks asli semaksimal mungkin. "
        f"Teks harus dalam bahasa {language}.\n\n"
        f"Teks Asli yang Perlu Ditulis Ulang:\n\"\"\"\n{original_text}\n\"\"\"\n\n"
        f"Teks Hasil Penulisan Ulang (hanya teks hasil, tanpa tambahan komentar):\n"
    )
    print(f"Meminta Gemini ({effective_model_name}) untuk menulis ulang teks demi kebijakan konten (Bahasa: {language})...")
    try:
        rewritten_text = generate_text_content(effective_model_name, prompt, temperature=0.5, max_output_tokens=max_output_tokens)
        if rewritten_text:
            print("Teks berhasil ditulis ulang oleh Gemini.")
            return rewritten_text.strip()
        else:
            print("Gagal mendapatkan hasil penulisan ulang dari Gemini (hasil kosong).")
            return None
    except Exception as e:
        print(f"Error saat meminta penulisan ulang teks ke Gemini: {e}")
        return None

def summarize_text(model_name, text_to_summarize, max_summary_words=200, language="Indonesia"):
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    prompt = (
        f"Ringkaslah teks berikut dalam kurang lebih {max_summary_words} kata. "
        f"Fokus pada poin-poin utama dan alur cerita untuk menjaga kontinuitas di bagian cerita selanjutnya. "
        f"Pastikan ringkasan mematuhi kebijakan konten standar dan aman untuk umum, hindari topik sensitif. "
        f"Ringkasan harus dalam bahasa {language}.\n\n"
        f"Teks:\n{text_to_summarize}"
    )
    try:
        summary = generate_text_content(effective_model_name, prompt, temperature=0.5, max_output_tokens=1024)
        return summary
    except Exception as e:
        print(f"Error saat meringkas teks dengan Gemini ({effective_model_name}): {e}")
        return None

def generate_image_prompts_for_paragraph(
    model_name, 
    current_chunk_text, 
    num_prompts_target, 
    character_details=None, 
    language="Inggris", 
    previous_chunk_text=None,
    template_content=None
):
    """
    Menghasilkan prompt gambar menggunakan model Gemini yang dipilih.
    """
    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL

    if template_content:
        # Gunakan template yang dipilih
        prompt_instruction = template_content.format(
            language=language,
            current_chunk_text=current_chunk_text,
            previous_chunk_text=previous_chunk_text if previous_chunk_text else "Tidak ada konteks sebelumnya.",
            character_description=character_details if character_details else "Tidak ada deskripsi karakter khusus.",
            num_prompts=num_prompts_target
        )
    else:
        # Gunakan prompt default (kode yang sudah ada)
        prompt_instruction = (
            f"Anda adalah seorang asisten yang bertugas membuat prompt gambar yang sangat deskriptif untuk AI image generator. "
            f"Prompt gambar yang dihasilkan harus dalam bahasa {language}.\n\n"
        )
        if previous_chunk_text:
            prompt_instruction += (
                f"Sebagai referensi dan untuk menjaga kontinuitas visual, berikut adalah ringkasan atau kutipan dari adegan/narasi sebelumnya:\n"
                f"\"\"\"\n{previous_chunk_text[:300]}...\n\"\"\"\n\n" 
            )
        prompt_instruction += (
            f"Sekarang, berdasarkan narasi/adegan saat ini di bawah ini, buatlah persis {num_prompts_target} prompt gambar yang berbeda satu sama lain. "
            f"Setiap prompt harus fokus pada aspek visual yang berbeda dari narasi saat ini, atau menggambarkan momen kunci secara detail. "
            f"Jika narasi saat ini adalah kelanjutan, pastikan prompt gambar mencerminkan kesinambungan dari konteks sebelumnya (jika diberikan).\n"
            f"PENTING: Pastikan semua prompt gambar mematuhi kebijakan konten standar dan aman untuk umum, hindari deskripsi yang mungkin melanggar kebijakan konten Azure OpenAI.\n"
        )
        if character_details:
            prompt_instruction += (
                f"Jika ada karakter yang disebutkan, usahakan untuk menjaga konsistensi deskripsi karakter berdasarkan detail berikut: {character_details}. "
                f"Sebutkan detail karakter ini dalam prompt jika relevan dengan adegan.\n"
            )
        else:
            prompt_instruction += (
                "Jika ada karakter yang disebutkan, deskripsikan penampilan mereka secara konsisten di semua prompt jika mereka muncul.\n"
            )
        prompt_instruction += (
            "Setiap prompt harus berupa satu kalimat atau frasa deskriptif yang kuat. "
            "Hindari frasa seperti 'Gambar yang menunjukkan...' atau 'Sebuah prompt untuk...'. Langsung ke deskripsi visual. "
            "Format output HARUS berupa daftar bernomor dari prompt, masing-masing di baris baru, dan HANYA berisi daftar tersebut. Contoh:\n"
            "1. [Prompt gambar 1]\n"
            f"{num_prompts_target}. [Prompt gambar {num_prompts_target}]\n\n"
            f"Narasi/Adegan Saat Ini (untuk dibuatkan prompt gambar):\n\"\"\"\n{current_chunk_text}\n\"\"\""
        )

    try:
        print(f"Meminta {num_prompts_target} prompt gambar dari Gemini ({effective_model_name}) untuk chunk: {current_chunk_text[:100]}...")
        if previous_chunk_text:
            print(f"  Dengan konteks chunk sebelumnya: {previous_chunk_text[:100]}...")
        raw_prompts_text = generate_text_content(effective_model_name, prompt_instruction, temperature=0.8, max_output_tokens=1024)
        if not raw_prompts_text: return []
        extracted_prompts = []
        found_numbered_prompts = re.findall(r"^\s*\d+\.\s*(.+)$", raw_prompts_text, re.MULTILINE)
        for p_text in found_numbered_prompts: extracted_prompts.append(p_text.strip())
        if not extracted_prompts: 
            lines = raw_prompts_text.splitlines()
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line and not cleaned_line.lower().startswith(("berikut adalah", "daftar prompt", "contoh prompt")):
                    extracted_prompts.append(cleaned_line)
        if not extracted_prompts: return []
        final_prompts = extracted_prompts[:num_prompts_target]
        if len(final_prompts) < num_prompts_target:
            print(f"Peringatan: Gemini hanya mengembalikan {len(final_prompts)} prompt valid, kurang dari {num_prompts_target} yang diminta.")
        return final_prompts
    except Exception as e:
        print(f"Error saat menghasilkan atau memproses prompt gambar dengan Gemini ({effective_model_name}): {e}")
        return []

def generate_story_part_from_template(
    gemini_api_key, model_name, template_content,
    fill_data, part_number 
):
    """
    Menghasilkan satu bagian cerita menggunakan template prompt yang disediakan.
    """
    if not configure_gemini(gemini_api_key): 
        return "Error: Gemini API Key tidak terkonfigurasi."

    previous_summary_block = ""
    if part_number > 1 and fill_data.get("previous_summary_content"):
        previous_summary_block = (
            f"Ini adalah bagian ke-{part_number} dari cerita. Berikut adalah ringkasan dari bagian sebelumnya "
            f"(pastikan ringkasan ini juga dalam bahasa {fill_data.get('language', 'Indonesia')}, mematuhi kebijakan konten, dan gaya yang diminta):\n"
            f"{fill_data['previous_summary_content']}\n\n"
        )

    character_description_block = ""
    if fill_data.get("character_description_content"):
        character_description_block = (
            f"Deskripsi Karakter (jika ada, pertahankan konsistensi dan pastikan deskripsi aman, sesuai gaya, dan relevan dengan bahasa {fill_data.get('language', 'Indonesia')}):\n"
            f"{fill_data['character_description_content']}\n\n"
        )
    
    final_fill_data = {
        "expertise": fill_data.get("expertise", "seorang pendongeng ulung"),
        "language": fill_data.get("language", "Indonesia"),
        "tone": fill_data.get("tone", "normal"),
        "format_style": fill_data.get("format_style", "narasi deskriptif"),
        "target_words": fill_data.get("target_words", "3500"),
        "azure_openai_policy_note": "PENTING: Buat narasi sesuai dengan kebijakan konten Azure OpenAI. Hindari topik, bahasa, atau skenario yang mungkin melanggar kebijakan konten tersebut. Fokus pada cerita yang aman untuk umum.",
        "previous_summary_block": previous_summary_block,
        "main_story_prompt": fill_data.get("main_story_prompt", ""),
        "character_description_block": character_description_block,
        "continuation_instruction": "Silakan tulis bagian cerita selanjutnya:"
    }

    # Inisialisasi final_prompt dengan konten template asli
    final_prompt = template_content  # Pastikan ini di level indentasi yang benar
    
    # Lakukan penggantian placeholder
    for key, value in final_fill_data.items():
        placeholder = f"{{{key}}}" 
        final_prompt = final_prompt.replace(placeholder, str(value)) 

    print(f"\n--- MENGHASILKAN BAGIAN CERITA KE-{part_number} MENGGUNAKAN TEMPLATE (Bahasa: {final_fill_data['language']}) ---")
    # print(f"Prompt Final ke Gemini:\n{final_prompt[:1000]}...\n") 

    effective_model_name = model_name if model_name else DEFAULT_GEMINI_MODEL
    story_text = generate_text_content(effective_model_name, final_prompt) # final_prompt sekarang sudah terdefinisi
    
    if story_text:
        print(f"Bagian cerita ke-{part_number} (dari template) berhasil dihasilkan (panjang: {len(story_text.split())} kata).")
    else:
        print(f"Gagal menghasilkan bagian cerita ke-{part_number} (dari template).")
        story_text = f"Error: Gagal menghasilkan teks untuk bagian ke-{part_number} menggunakan template."

    return story_text