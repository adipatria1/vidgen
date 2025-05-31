import re
import uuid
import os
import time

# ... (fungsi-fungsi utilitas yang sudah ada tetap sama) ...
def split_text_into_paragraphs(text):
    if not text: return []
    lines = (line.strip() for line in text.splitlines())
    stripped_text = "\n".join(line for line in lines if line)
    paragraphs = re.split(r'\n\s*\n', stripped_text)
    return [p.strip() for p in paragraphs if p.strip()]

def find_best_split_point(text_segment, max_chars, preferred_delimiters):
    if len(text_segment) <= max_chars: return len(text_segment)
    best_split = -1
    for delimiter_set in preferred_delimiters:
        for i in range(min(len(text_segment) -1, max_chars), 0, -1):
            if text_segment[i] in delimiter_set:
                if i > 0 and text_segment[i-1].isspace(): best_split = i + 1; return best_split
                elif text_segment[i+1:i+2].isspace() or text_segment[i+1:i+2] == '': best_split = i + 1; return best_split
        for i in range(min(len(text_segment) -1, max_chars), 0, -1):
             if text_segment[i] in delimiter_set: best_split = i + 1; return best_split
    if best_split == -1:
        for i in range(max_chars, 0, -1):
            if text_segment[i].isspace(): best_split = i + 1; return best_split
    return max_chars if best_split == -1 else best_split

def split_text_into_chunks(text, max_chars=600):
    if not text: return []
    preferred_delimiters_ordered = [['.', '?', '!'], [':', ';'], [',', ')', '(']]
    chunks = []; current_pos = 0; text_len = len(text)
    while current_pos < text_len:
        remaining_text = text[current_pos:]
        if len(remaining_text) <= max_chars: chunks.append(remaining_text.strip()); break
        search_segment = remaining_text[:max_chars + 50]; split_at = -1
        for delimiter_group in preferred_delimiters_ordered:
            for i in range(min(len(search_segment) -1, max_chars), 0, -1):
                if search_segment[i] in delimiter_group:
                    char_after = search_segment[i+1:i+2]
                    if char_after.isspace() or char_after == '' or (i > 0 and search_segment[i-1].isalnum()): split_at = i + 1; break
            if split_at != -1: break
        if split_at == -1:
            for i in range(max_chars, 0, -1):
                if remaining_text[i].isspace(): split_at = i + 1; break
        if split_at == -1 or split_at == 0: split_at = max_chars
        split_at = min(split_at, len(remaining_text))
        chunk_text = remaining_text[:split_at].strip()
        if chunk_text: chunks.append(chunk_text)
        current_pos += split_at
        while current_pos < text_len and text[current_pos].isspace(): current_pos += 1
    return [c for c in chunks if c] 

def generate_unique_filename(prefix="media", extension="tmp"): return f"{prefix}_{uuid.uuid4().hex}.{extension}"
def get_project_root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def get_media_path(media_type, filename, base_dir_name="generated_media"):
    project_root = get_project_root()
    return os.path.join(project_root, 'app', 'static', base_dir_name, media_type, filename)
def api_delay(seconds=4): # Default delay diubah menjadi 4 detik sesuai permintaan
    print(f"Menunggu {seconds} detik (API delay)..."); time.sleep(seconds)

IMAGE_ASPECT_RATIOS_PIXELS = {"16:9": (1024, 576), "9:16": (576, 1024), "1:1": (1024, 1024), "4:3": (1024, 768)}
AVAILABLE_GEMINI_MODELS = ["gemini-2.5-flash-preview-05-20", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash" 
POLLINATIONS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "ballad", "coral", "sage"]
DEFAULT_POLLINATIONS_VOICE = "alloy"
POLLINATIONS_IMAGE_MODELS = ["Flux", "Midjourney", "Turbo", "Flux-pro", "Flux-realism", "Flux-anime", "Flux-3d", "Flux-cablayai"] 
DEFAULT_POLLINATIONS_IMAGE_MODEL = "flux"
POLLINATIONS_ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3"]
DEFAULT_POLLINATIONS_ASPECT_RATIO = "16:9"
WORDS_PER_STORY_PART = 3500 
IMAGES_PER_PARAGRAPH_MIN = 3
IMAGES_PER_PARAGRAPH_MAX = 5

NARRATIVE_EXPERTISE_OPTIONS = { # ... (opsi tetap sama) ... 
    "Story Teller (Default)": "seorang pendongeng yang ulung dan kreatif",
    "Jurnalis Investigasi": "seorang jurnalis investigasi yang detail dan faktual",
    "Penulis Naskah Film": "seorang penulis naskah film yang mahir membangun adegan dan dialog",
    "Pakar Sejarah": "seorang pakar sejarah yang mampu merangkai cerita berdasarkan fakta sejarah",
    "Novelis Fiksi Ilmiah": "seorang novelis fiksi ilmiah dengan imajinasi liar dan detail teknis",
    "Penulis Cerita Anak": "seorang penulis cerita anak yang imajinatif dan menggunakan bahasa yang mudah dipahami"
}
DEFAULT_NARRATIVE_EXPERTISE = "Story Teller (Default)"
NARRATIVE_TONE_OPTIONS = { # ... (opsi tetap sama) ...
    "Normal (Default)": "normal dan netral",
    "Sarkastik": "sarkastik dan penuh sindiran halus",
    "Humoris": "humoris dan menghibur",
    "Serius dan Formal": "serius, formal, dan mendalam",
    "Optimis dan Inspiratif": "optimis dan penuh inspirasi",
    "Misterius dan Tegang": "misterius dan membangun ketegangan",
    "Puitis dan Filosofis": "puitis dan filosofis"
}
DEFAULT_NARRATIVE_TONE = "Normal (Default)"
NARRATIVE_FORMAT_OPTIONS = { # ... (opsi tetap sama) ...
    "Narasi (Default)": "narasi deskriptif yang mengalir",
    "Cerita dengan Dialog": "cerita yang kaya akan dialog antar karakter",
    "Laporan Jurnalistik": "laporan jurnalistik dengan struktur yang jelas",
    "Naskah Drama/Film Pendek": "naskah drama atau film pendek dengan format adegan dan dialog",
    "Puisi Naratif": "puisi naratif yang menceritakan sebuah kisah",
    "Surat atau Jurnal Pribadi": "format surat atau entri jurnal pribadi"
}
DEFAULT_NARRATIVE_FORMAT = "Narasi (Default)"
NARRATIVE_LANGUAGE_OPTIONS = { # ... (opsi tetap sama) ...
    "Indonesia (Default)": "Indonesia",
    "Inggris (English)": "Inggris",
    "Jerman (Deutsch)": "Jerman",
    "Spanyol (Español)": "Spanyol",
    "Prancis (Français)": "Prancis",
    "Jepang (日本語)": "Jepang",
    "Korea (한국어)": "Korea",
    "Arab (العربية)": "Arab",
    "Mandarin (中文)": "Mandarin"
}
DEFAULT_NARRATIVE_LANGUAGE = "Indonesia (Default)"

DEFAULT_EFFECTS_ENABLED = True 
DEFAULT_FADE_PROBABILITY = 50  
DEFAULT_ZOOM_IN_PROBABILITY = 40 
DEFAULT_ZOOM_OUT_PROBABILITY = 20 
DEFAULT_STATIC_PROBABILITY = 40  
DEFAULT_TTS_MAX_RETRIES = 2 
DEFAULT_IMAGE_MAX_RETRIES = 2 

# --- Opsi dan Default untuk "All AI (Pollinations Text)" ---
POLLINATIONS_TEXT_BASE_URL = "https://text.pollinations.ai/"
POLLINATIONS_TEXT_MODELS = [
    "openai", "openai-fast", "openai-large", "openai-roblox", 
    "qwen-coder", "llama", "llamascout", "mistral", "unity", 
    "mirexa", "searchgpt", "evil", "deepseek-reasoning", "phi", "deepseek"
]
DEFAULT_POLLINATIONS_TEXT_MODEL = "openai" 
POLLINATIONS_TEXT_API_DELAY_SECONDS = 4 # Sesuai permintaan, minimal 3 detik dari rate limit, 4 detik lebih aman
