import requests
import os
import time
from app.utils import generate_unique_filename, get_media_path, api_delay
from urllib.parse import quote_plus

POLLINATIONS_TTS_BASE_URL = "https://text.pollinations.ai/"
# MAX_RETRIES_TTS dihapus dari sini, akan diterima sebagai parameter
RETRY_DELAY_SECONDS_TTS = 5 

CONTENT_POLICY_ERROR_SIGNAL = "CONTENT_POLICY_ERROR"

def generate_audio_pollinations(text_to_speak, voice="alloy", output_directory_name="audio", max_retries_override=2):
    """
    Menghasilkan audio dari teks menggunakan API TTS Pollinations.
    max_retries_override: Jumlah percobaan ulang yang dikonfigurasi pengguna.
    """
    if not text_to_speak:
        print("Error: Teks untuk diubah menjadi suara tidak boleh kosong.")
        return None

    encoded_text = quote_plus(text_to_speak)
    request_url = f"{POLLINATIONS_TTS_BASE_URL}{encoded_text}?model=openai-audio&voice={voice}"
    
    last_exception = None
    # Gunakan max_retries_override dari parameter, pastikan minimal 1 percobaan jika override 0
    effective_max_retries = max(1, max_retries_override) 

    for attempt in range(1, effective_max_retries + 1):
        print(f"Memanggil API Pollinations TTS (Percobaan ke-{attempt}/{effective_max_retries}): {request_url[:150]}...")
        try:
            response = requests.get(request_url, timeout=120) 
            response.raise_for_status()  

            if 'audio/' in response.headers.get('Content-Type', ''): 
                extension = response.headers.get('Content-Type').split('/')[-1]
                if extension == 'mpeg': extension = 'mp3'
                
                filename = generate_unique_filename(prefix=f"tts_{voice}", extension=extension)
                filepath = get_media_path(output_directory_name, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Audio berhasil disimpan di: {filepath} (setelah percobaan ke-{attempt})")
                return filepath 
            else:
                print(f"Respon tidak terduga dari API TTS (bukan audio) percobaan ke-{attempt}: {response.headers.get('Content-Type')}")
                print(f"Response text: {response.text[:200]}")
                last_exception = Exception(f"Respon bukan audio: {response.headers.get('Content-Type')}")

        except requests.exceptions.RequestException as e:
            print(f"Error API Pollinations TTS percobaan ke-{attempt}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Detail Error TTS: Status {e.response.status_code}, Respon: {e.response.text[:300]}")
                if e.response.status_code == 400 and "content management policy" in e.response.text.lower():
                    print("Terdeteksi error kebijakan konten Azure OpenAI.")
                    return CONTENT_POLICY_ERROR_SIGNAL 
            last_exception = e
        except Exception as e:
            print(f"Error umum TTS percobaan ke-{attempt}: {e}")
            last_exception = e

        if attempt < effective_max_retries:
            print(f"Menunggu {RETRY_DELAY_SECONDS_TTS} detik sebelum mencoba lagi...")
            time.sleep(RETRY_DELAY_SECONDS_TTS)
        else:
            print(f"Gagal menghasilkan audio setelah {effective_max_retries} percobaan.")
            if last_exception:
                print(f"Error terakhir yang tercatat: {last_exception}")
            return None 
    
    return None 
