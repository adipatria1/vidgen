import requests
import os
import random
import time
from app.utils import generate_unique_filename, get_media_path, api_delay, IMAGE_ASPECT_RATIOS_PIXELS
from urllib.parse import quote_plus

POLLINATIONS_IMAGE_BASE_URL = "https://pollinations.ai/p/"
# MAX_RETRIES_IMG dihapus dari sini, akan diterima sebagai parameter
RETRY_DELAY_SECONDS_IMG = 7 

def generate_image_pollinations(
    prompt,
    aspect_ratio_str="16:9",
    image_model="flux", 
    seed=None,
    output_directory_name="images",
    nologo=True,         
    private=True,        
    enhance=True,        
    disable_safe_filter=False,
    max_retries_override=2 # Parameter baru untuk jumlah retry
):
    """
    Menghasilkan gambar dari teks menggunakan API Image Pollinations.
    max_retries_override: Jumlah percobaan ulang yang dikonfigurasi pengguna.
    """
    if not prompt:
        print("Error: Prompt gambar tidak boleh kosong.")
        return None

    width, height = IMAGE_ASPECT_RATIOS_PIXELS.get(aspect_ratio_str, (1024, 1024)) 

    current_seed = seed if seed is not None else random.randint(0, 2**32 - 1)
    encoded_prompt = quote_plus(prompt)

    request_url = f"{POLLINATIONS_IMAGE_BASE_URL}{encoded_prompt}?width={width}&height={height}&seed={current_seed}&model={image_model}"
    
    if nologo: request_url += "&nologo=true"
    if private: request_url += "&private=true"
    if enhance: request_url += "&enhance=true" 
    if disable_safe_filter: request_url += "&safe=false"
    
    last_exception = None
    # Gunakan max_retries_override dari parameter, pastikan minimal 1 percobaan
    effective_max_retries_img = max(1, max_retries_override)

    for attempt in range(1, effective_max_retries_img + 1):
        print(f"Memanggil API Pollinations Image (Percobaan ke-{attempt}/{effective_max_retries_img}): {request_url[:150]}...")
        try:
            response = requests.get(request_url, timeout=300) 
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'image/' in content_type:
                extension = content_type.split('/')[-1]
                if extension not in ['jpeg', 'png', 'gif', 'webp']: 
                    extension = 'jpg'
                if extension == 'jpeg': extension = 'jpg'

                filename = generate_unique_filename(prefix=f"img_{image_model}_{current_seed}", extension=extension)
                filepath = get_media_path(output_directory_name, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Gambar berhasil disimpan di: {filepath} (setelah percobaan ke-{attempt})")
                return filepath 
            else:
                print(f"Respon tidak terduga dari API Image (bukan gambar) percobaan ke-{attempt}: {content_type}")
                print(f"Response text: {response.text[:200]}")
                last_exception = Exception(f"Respon bukan gambar: {content_type}")

        except requests.exceptions.RequestException as e:
            print(f"Error API Pollinations Image percobaan ke-{attempt}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Detail Error Image: Status {e.response.status_code}, Respon: {e.response.text[:300]}")
                # Jika ada error spesifik yang tidak perlu di-retry (misal 400 karena prompt buruk), bisa ditambahkan di sini
                # if e.response.status_code == 400 and "bad_prompt" in e.response.text.lower():
                #     print("Error karena prompt gambar buruk, tidak mencoba lagi.")
                #     return None
            last_exception = e
        except Exception as e:
            print(f"Error umum Image Gen percobaan ke-{attempt}: {e}")
            last_exception = e

        if attempt < effective_max_retries_img:
            print(f"Menunggu {RETRY_DELAY_SECONDS_IMG} detik sebelum mencoba lagi...")
            time.sleep(RETRY_DELAY_SECONDS_IMG)
        else:
            print(f"Gagal menghasilkan gambar setelah {effective_max_retries_img} percobaan untuk prompt: {prompt[:50]}...")
            if last_exception:
                print(f"Error terakhir yang tercatat: {last_exception}")
            return None 
    
    return None 
