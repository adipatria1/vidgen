import json
import os
import uuid
from flask import current_app

# Nama file untuk menyimpan template
TEMPLATES_FILENAME = "prompt_templates.json"
# Direktori untuk menyimpan data, relatif terhadap direktori 'app'
DATA_SUBDIR = "data" 

def get_templates_filepath():
    """Mendapatkan path absolut ke file JSON template."""
    if not current_app:
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_SUBDIR)
        print("PERINGATAN: current_app tidak tersedia, menggunakan path fallback untuk template file.")
    else:
        base_path = os.path.join(current_app.root_path, DATA_SUBDIR)
    
    os.makedirs(base_path, exist_ok=True) 
    return os.path.join(base_path, TEMPLATES_FILENAME)

DEFAULT_STORY_GENERATION_PROMPT_CONTENT = """Anda adalah {expertise}.
Tuliskan cerita ini dalam bahasa {language} dengan nada {tone} dalam format {format_style}.
PENTING: Buat narasi sesuai dengan kebijakan konten Azure OpenAI. Hindari topik, bahasa, atau skenario yang mungkin melanggar kebijakan konten tersebut (misalnya, konten sensitif, kebencian, kekerasan eksplisit, dll.). Fokus pada cerita yang aman untuk umum.
Tuliskan bagian cerita ini dengan panjang yang sangat mendekati {target_words} kata. Upayakan agar jumlah kata tidak menyimpang lebih dari 10-15% dari target tersebut (boleh sedikit lebih atau kurang). Presisi jumlah kata adalah penting untuk bagian ini.

{previous_summary_block}
Prompt utama untuk bagian ini:
{main_story_prompt}

{character_description_block}
Silakan tulis bagian cerita selanjutnya:"""

DEFAULT_IMAGE_GENERATION_PROMPT_CONTENT = """Buatlah prompt gambar yang sangat deskriptif untuk AI image generator dalam bahasa {language}.

Berdasarkan narasi berikut:
\"\"\"\n{current_chunk_text}\n\"\"\"

Jika ada konteks sebelumnya:
{previous_chunk_text}

Jika ada deskripsi karakter yang perlu dipertahankan:
{character_description}

Buat {num_prompts} prompt gambar yang berbeda. Setiap prompt harus:
- Fokus pada aspek visual yang berbeda dari narasi
- Berupa satu kalimat deskriptif yang kuat
- Menggambarkan adegan dengan detail
- Aman untuk umum dan mematuhi kebijakan konten
- Konsisten dengan deskripsi karakter jika ada

Format output: Daftar bernomor, satu prompt per baris."""

DEFAULT_TEMPLATES = [
    {
        "id": "default-story-v1",
        "name": "Default Story Generation V1",
        "content": DEFAULT_STORY_GENERATION_PROMPT_CONTENT,
        "is_default": True,
        "description": "Template standar untuk generasi cerita dengan berbagai opsi.",
        "type": "story"
    },
    {
        "id": "default-image-v1",
        "name": "Default Image Generation V1",
        "content": DEFAULT_IMAGE_GENERATION_PROMPT_CONTENT,
        "is_default": True,
        "description": "Template standar untuk generasi prompt gambar.",
        "type": "image"
    }
]

def load_prompt_templates():
    """Memuat template prompt dari file JSON."""
    filepath = get_templates_filepath()
    if not os.path.exists(filepath):
        save_prompt_templates(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        default_ids = {t['id'] for t in DEFAULT_TEMPLATES}
        current_default_templates_in_file = {t['id']: t for t in templates if t.get('is_default')}
        updated_templates = [t for t in templates if not t.get('is_default')] 

        needs_resave = False
        for default_tpl_def in DEFAULT_TEMPLATES:
            if default_tpl_def['id'] in current_default_templates_in_file:
                existing_version = current_default_templates_in_file[default_tpl_def['id']]
                if existing_version['content'] != default_tpl_def['content']:
                    existing_version['content'] = default_tpl_def['content']
                    needs_resave = True
                existing_version['is_default'] = True 
                updated_templates.append(existing_version)
            else:
                updated_templates.append(default_tpl_def)
                needs_resave = True
        
        for t_id in default_ids:
            if not any(ut['id'] == t_id for ut in updated_templates):
                default_to_add = next(dt for dt in DEFAULT_TEMPLATES if dt['id'] == t_id)
                updated_templates.append(default_to_add)
                needs_resave = True

        if needs_resave or len(updated_templates) != len(templates):
            save_prompt_templates(updated_templates)
            templates = updated_templates
        return templates
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error memuat template: {e}. Mengembalikan template default.")
        save_prompt_templates(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES

def save_prompt_templates(templates):
    """Menyimpan daftar template prompt ke file JSON."""
    filepath = get_templates_filepath()
    try:
        # Pastikan direktori ada
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Tulis ke file sementara dulu
        temp_filepath = filepath + '.tmp'
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=4, ensure_ascii=False)
        
        # Jika berhasil, ganti file asli
        if os.path.exists(filepath):
            os.replace(temp_filepath, filepath)
        else:
            os.rename(temp_filepath, filepath)
            
        print(f"Template berhasil disimpan ke: {filepath}")
        return True
    except IOError as e:
        print(f"Error menyimpan template: {e}")
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass
        return False

def get_template_by_id(template_id):
    """Mendapatkan satu template berdasarkan ID."""
    templates = load_prompt_templates()
    for template in templates:
        if template['id'] == template_id:
            return template
    return None

def add_prompt_template(name, content, description="", template_type="story"):
    """Menambahkan template baru."""
    templates = load_prompt_templates()
    new_template = {
        "id": str(uuid.uuid4()),
        "name": name,
        "content": content,
        "description": description,
        "is_default": False,
        "type": template_type
    }
    templates.append(new_template)
    if save_prompt_templates(templates):
        print(f"Template baru '{name}' berhasil ditambahkan dengan ID: {new_template['id']}")
        return new_template
    return None

def update_prompt_template(template_id, name, content, description="", template_type=None):
    """Memperbarui template yang ada."""
    templates = load_prompt_templates()
    updated = False
    for template in templates:
        if template['id'] == template_id:
            if template.get('is_default', False):
                template['name'] = name
                template['description'] = description
                print(f"Peringatan: Mencoba mengubah template default '{template_id}'. Hanya nama dan deskripsi yang diizinkan untuk diubah melalui UI.")
                default_content_from_code = next((dt['content'] for dt in DEFAULT_TEMPLATES if dt['id'] == template_id), template['content'])
                if template['content'] != default_content_from_code:
                    template['content'] = default_content_from_code
            else:
                template['name'] = name
                template['content'] = content
                template['description'] = description
                if template_type:
                    template['type'] = template_type
            updated = True
            break
    if updated:
        return save_prompt_templates(templates)
    return False

def delete_prompt_template(template_id):
    """Menghapus template, kecuali template default."""
    templates = load_prompt_templates()
    template_to_delete = get_template_by_id(template_id)
    
    if template_to_delete and template_to_delete.get('is_default', False):
        print(f"Peringatan: Template default '{template_id}' tidak dapat dihapus.")
        return False

    original_length = len(templates)
    templates = [t for t in templates if t['id'] != template_id]
    
    if len(templates) < original_length:
        return save_prompt_templates(templates)
    return False