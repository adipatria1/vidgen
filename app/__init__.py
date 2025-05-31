from flask import Flask, current_app
import os

# Impor fungsi ensure_media_dirs dari routes.py
from .routes import ensure_media_dirs 
# Impor fungsi untuk memastikan file template ada saat startup
from .prompt_template_utils import load_prompt_templates # Untuk inisialisasi

def create_app():
    """
    Factory function untuk membuat instance aplikasi Flask.
    """
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_ganti_ini_di_produksi_banget')
    if app.config['SECRET_KEY'] == 'dev_secret_key_ganti_ini_di_produksi_banget' and not app.debug:
        print("PERINGATAN: FLASK_SECRET_KEY tidak diatur dengan aman untuk lingkungan produksi!")

    # Daftarkan blueprint utama
    from . import routes 
    app.register_blueprint(routes.bp)

    # Daftarkan blueprint file manager
    from .file_manager_routes import file_manager_bp
    app.register_blueprint(file_manager_bp)

    # Daftarkan blueprint prompt template manager baru
    from .prompt_template_routes import prompt_template_bp
    app.register_blueprint(prompt_template_bp)

    with app.app_context():
        print("Menjalankan initial setup (memastikan direktori media & data)...")
        ensure_media_dirs() 
        # Pastikan direktori data untuk prompt_templates.json ada (dipanggil di dalam load_prompt_templates)
        # dan file template diinisialisasi jika belum ada.
        print("Memuat/menginisialisasi template prompt...")
        load_prompt_templates() 
        print("Initial setup selesai.")
    
    return app
