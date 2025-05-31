from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import prompt_template_utils as ptu # Menggunakan alias untuk utilitas template

prompt_template_bp = Blueprint('prompt_templates', __name__, url_prefix='/prompt-templates')

@prompt_template_bp.route('/')
def manage_templates():
    """Menampilkan daftar template prompt."""
    templates = ptu.load_prompt_templates()
    return render_template('manage_prompt_templates.html', templates=templates)

@prompt_template_bp.route('/create', methods=['GET', 'POST'])
def create_template():
    """Membuat template prompt baru."""
    if request.method == 'POST':
        name = request.form.get('template_name')
        content = request.form.get('template_content')
        description = request.form.get('template_description', "")
        template_type = request.form.get('template_type', 'story')  # Default to 'story' if not specified

        if not name or not content:
            flash('Nama dan Konten Template tidak boleh kosong.', 'error')
        else:
            ptu.add_prompt_template(name, content, description, template_type)
            flash('Template prompt berhasil dibuat.', 'success')
            return redirect(url_for('prompt_templates.manage_templates'))
    
    # Untuk GET request atau jika POST gagal validasi
    return render_template('edit_prompt_template.html', action="Create", template=None, 
                           default_placeholders=get_default_placeholders_info())


@prompt_template_bp.route('/edit/<template_id>', methods=['GET', 'POST'])
def edit_template(template_id):
    """Mengedit template prompt yang ada."""
    template = ptu.get_template_by_id(template_id)
    if not template:
        flash('Template tidak ditemukan.', 'error')
        return redirect(url_for('prompt_templates.manage_templates'))

    if request.method == 'POST':
        name = request.form.get('template_name')
        content = request.form.get('template_content')
        description = request.form.get('template_description', "")
        template_type = request.form.get('template_type', template.get('type', 'story'))

        if not name or (not template.get('is_default') and not content): # Konten wajib jika bukan default
            flash('Nama dan Konten Template tidak boleh kosong.', 'error')
        else:
            if ptu.update_prompt_template(template_id, name, content, description, template_type):
                flash('Template prompt berhasil diperbarui.', 'success')
            else:
                flash('Gagal memperbarui template atau template tidak ditemukan.', 'warning')
            return redirect(url_for('prompt_templates.manage_templates'))
    
    # Untuk GET request
    return render_template('edit_prompt_template.html', action="Edit", template=template,
                           default_placeholders=get_default_placeholders_info())


@prompt_template_bp.route('/delete/<template_id>', methods=['POST'])
def delete_template(template_id):
    """Menghapus template prompt."""
    template = ptu.get_template_by_id(template_id)
    if template and template.get('is_default', False):
        flash('Template default tidak dapat dihapus.', 'error')
    elif ptu.delete_prompt_template(template_id):
        flash('Template prompt berhasil dihapus.', 'success')
    else:
        flash('Gagal menghapus template atau template tidak ditemukan.', 'error')
    return redirect(url_for('prompt_templates.manage_templates'))

def get_default_placeholders_info():
    """Mengembalikan informasi placeholder untuk ditampilkan di form edit."""
    return {
        "{expertise}": "Keahlian penulis (misal: 'seorang pendongeng ulung').",
        "{language}": "Bahasa output (misal: 'Indonesia', 'Inggris').",
        "{tone}": "Nada penulisan (misal: 'humoris', 'serius').",
        "{format_style}": "Format output teks (misal: 'narasi deskriptif', 'cerita dengan dialog').",
        "{target_words}": "Target jumlah kata untuk bagian cerita.",
        "{azure_openai_policy_note}": "Peringatan standar kebijakan konten (biasanya sudah termasuk dalam template default).",
        "{previous_summary_block}": "Blok teks berisi ringkasan bagian sebelumnya (otomatis diisi jika ada).",
        "{main_story_prompt}": "Prompt cerita utama yang dimasukkan pengguna.",
        "{character_description_block}": "Blok teks berisi deskripsi karakter (otomatis diisi jika ada).",
        "{continuation_instruction}": "Instruksi untuk melanjutkan cerita (misal: 'Silakan tulis bagian cerita selanjutnya:')."
    }