import requests
import urllib.parse
import json
import time
import re # Impor modul re untuk parsing
from app.utils import POLLINATIONS_TEXT_BASE_URL, POLLINATIONS_TEXT_API_DELAY_SECONDS

def generate_text_pollinations(
    main_prompt, 
    model="openai", 
    system_prompt=None, 
    private=True,
    max_retries=2,
    temperature=0.7,
    top_p=None,
    presence_penalty=None,
    frequency_penalty=None
    ):
    """
    Menghasilkan teks menggunakan API Text-to-Text Pollinations.
    """
    if not main_prompt:
        print("Error: Prompt utama tidak boleh kosong untuk Pollinations Text API.")
        return None

    encoded_prompt = urllib.parse.quote(main_prompt)
    url = f"{POLLINATIONS_TEXT_BASE_URL}{encoded_prompt}"
    
    params = {
        "model": model,
        "json": "true", 
        "private": str(private).lower(),
        "temperature": temperature
    }
    if system_prompt:
        params["system"] = urllib.parse.quote(system_prompt)
    if top_p is not None:
        params["top_p"] = top_p
    if presence_penalty is not None:
        params["presence_penalty"] = presence_penalty
    if frequency_penalty is not None:
        params["frequency_penalty"] = frequency_penalty
    
    last_exception = None
    for attempt in range(1, max_retries + 1):
        print(f"Memanggil API Pollinations Text (Percobaan ke-{attempt}/{max_retries}): Model={model}, Prompt='{main_prompt[:70]}...'")
        try:
            response = requests.get(url, params=params, timeout=120) 
            response.raise_for_status()

            try:
                data_text = response.text
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    print(f"Peringatan: Respons Pollinations Text bukan JSON valid, mengembalikan sebagai teks biasa. Respons: {data_text[:200]}")
                    return data_text.strip()

                generated_text = None
                if isinstance(data, dict):
                    if "text" in data: generated_text = data["text"]
                    elif "output" in data: generated_text = data["output"]
                    elif "response" in data: generated_text = data["response"]
                    elif "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0 and "text" in data["choices"][0]:
                        generated_text = data["choices"][0]["text"]
                    elif "data" in data and isinstance(data["data"], str) : 
                        generated_text = data["data"]
                    else:
                        if len(data) == 1:
                            generated_text = str(list(data.values())[0])
                        else:
                             generated_text = data_text
                elif isinstance(data, str):
                    generated_text = data
                else:
                    generated_text = data_text

                if generated_text is not None:
                    print(f"Teks berhasil dihasilkan oleh Pollinations Text API (Model: {model}).")
                    return str(generated_text).strip()
                else:
                    print(f"Gagal mengekstrak teks dari respons JSON Pollinations: {data}")
                    last_exception = Exception("Format JSON tidak dikenali atau tidak ada teks.")

            except Exception as e_parse:
                print(f"Error memproses respons dari Pollinations Text: {e_parse}")
                last_exception = e_parse

        except requests.exceptions.RequestException as e:
            print(f"Error memanggil API Pollinations Text pada percobaan ke-{attempt}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Detail Error: Status {e.response.status_code}, Respon: {e.response.text[:200]}")
            last_exception = e
        except Exception as e_general:
            print(f"Error umum saat proses Pollinations Text pada percobaan ke-{attempt}: {e_general}")
            last_exception = e_general
        
        if attempt < max_retries:
            print(f"Menunggu {POLLINATIONS_TEXT_API_DELAY_SECONDS + attempt} detik sebelum mencoba lagi...")
            time.sleep(POLLINATIONS_TEXT_API_DELAY_SECONDS + attempt)
        else:
            print(f"Gagal menghasilkan teks dari Pollinations setelah {max_retries} percobaan.")
            if last_exception: print(f"Error terakhir: {last_exception}")
            return None
    return None


def summarize_text_pollinations(
    text_to_summarize, 
    model="openai-fast", 
    language="Indonesia", 
    max_summary_words=150,
    private=True
    ):
    """
    Meringkas teks menggunakan API Text-to-Text Pollinations.
    """
    main_prompt_for_summary = (
        f"Dalam bahasa {language}, ringkaslah teks berikut menjadi sekitar {max_summary_words} kata. "
        f"Fokus pada poin-poin utama dan alur cerita. "
        f"Pastikan ringkasan aman untuk umum.\n\n"
        f"Teks yang akan diringkas:\n\"\"\"\n{text_to_summarize[:1500]}\n\"\"\""
    )
    
    system_prompt_for_summary = f"Anda adalah asisten AI yang ahli dalam membuat ringkasan teks dalam berbagai bahasa dan memastikan konten aman."

    print(f"Meminta ringkasan dari Pollinations Text API (Model: {model})...")
    summary = generate_text_pollinations(
        main_prompt=main_prompt_for_summary,
        model=model,
        system_prompt=system_prompt_for_summary,
        private=private,
        temperature=0.5
    )
    if summary:
        print("Ringkasan berhasil dibuat oleh Pollinations Text API.")
    else:
        print("Gagal membuat ringkasan dengan Pollinations Text API.")
    return summary


def generate_image_prompts_via_pollinations(
    model_name, 
    current_chunk_text, 
    num_prompts_target, 
    character_details=None, 
    language_of_chunk="Indonesia",
    output_language="Inggris",
    previous_chunk_text=None,
    private=True,
    template_content=None
):
    """
    Menghasilkan prompt gambar menggunakan API Text-to-Text Pollinations.
    """
    if template_content:
        main_prompt_for_img = template_content.format(
            language=output_language,
            current_chunk_text=current_chunk_text,
            previous_chunk_text=previous_chunk_text if previous_chunk_text else "Tidak ada konteks sebelumnya.",
            character_description=character_details if character_details else "Tidak ada deskripsi karakter khusus.",
            num_prompts=num_prompts_target
        )
    else:
        system_prompt_for_img = (
            f"Anda adalah AI yang sangat kreatif dan ahli dalam membuat prompt gambar yang detail dan visual untuk generator gambar AI. "
            f"Output Anda HARUS berupa daftar bernomor dari {num_prompts_target} prompt gambar dalam bahasa {output_language}. "
            f"Setiap prompt harus unik dan mendeskripsikan adegan atau elemen visual dari narasi yang diberikan. "
            f"Pastikan semua prompt aman untuk umum dan mematuhi kebijakan konten."
        )

        main_prompt_for_img = f"Narasi saat ini (dalam bahasa {language_of_chunk}):\n\"\"\"\n{current_chunk_text}\n\"\"\"\n\n"
        if previous_chunk_text:
            main_prompt_for_img += f"Konteks dari narasi sebelumnya (dalam bahasa {language_of_chunk}):\n\"\"\"\n{previous_chunk_text[:300]}...\n\"\"\"\n\n"
        if character_details:
            main_prompt_for_img += f"Detail karakter yang perlu dipertimbangkan (jika relevan dengan adegan saat ini):\n{character_details}\n\n"
        
        main_prompt_for_img += (
            f"Berdasarkan narasi di atas, buatlah {num_prompts_target} prompt gambar dalam bahasa {output_language}. "
            f"Setiap prompt harus berupa satu kalimat deskriptif. Jangan gunakan frasa seperti 'Gambar yang menunjukkan...'. "
            f"Format output: daftar bernomor (misal: 1. Prompt A, 2. Prompt B, dst.)."
        )
    
    print(f"Meminta {num_prompts_target} prompt gambar dari Pollinations Text API (Model: {model_name})...")
    raw_prompts_text = generate_text_pollinations(
        main_prompt=main_prompt_for_img,
        model=model_name,
        system_prompt=system_prompt_for_img if not template_content else None,
        private=private,
        temperature=0.8
    )

    if not raw_prompts_text:
        print("Tidak ada output teks dari Pollinations untuk prompt gambar.")
        return []

    print(f"Teks mentah untuk prompt gambar diterima dari Pollinations:\n{raw_prompts_text}")
    
    extracted_prompts = []
    found_numbered_prompts = re.findall(r"^\s*\d+\.\s*(.+)$", raw_prompts_text, re.MULTILINE)
    
    for p_text in found_numbered_prompts:
        extracted_prompts.append(p_text.strip())
    
    if not extracted_prompts:
        print("Tidak ada prompt bernomor yang berhasil diekstrak. Mencoba membagi berdasarkan baris baru.")
        lines = raw_prompts_text.splitlines()
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line and len(cleaned_line) > 10 and not cleaned_line.lower().startswith(("berikut adalah", "daftar prompt", "contoh prompt", "prompt gambar:")):
                extracted_prompts.append(cleaned_line)
    
    if not extracted_prompts:
        print("Tidak ada prompt gambar yang berhasil diekstrak dari output Pollinations.")
        return []

    final_prompts = extracted_prompts[:num_prompts_target]
    if len(final_prompts) < num_prompts_target:
        print(f"Peringatan: Pollinations hanya mengembalikan {len(final_prompts)} prompt gambar, kurang dari {num_prompts_target} yang diminta.")
    
    return final_prompts