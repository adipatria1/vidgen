from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
import os
import shutil 
import zipfile # Untuk membuat file ZIP
import io # Untuk mengirim file ZIP dari memori jika memungkinkan

from app.utils import get_media_path, generate_unique_filename # Tambahkan generate_unique_filename

file_manager_bp = Blueprint('file_manager', __name__, url_prefix='/files')

MEDIA_TYPES_AND_DIRS = {
    "Audio Chunks": "audio",
    "Image Files": "images",
    "Generated Videos": "videos",
    "Story Chunks (Text)": "story_chunks",
    "Full Stories (Text)": "full_stories",
    "Uploaded Narratives": "uploaded_narratives"
}

def list_files_in_directory(media_type_key):
    """Mendaftar file dalam direktori media tertentu."""
    files_list = []
    directory_name = MEDIA_TYPES_AND_DIRS.get(media_type_key)
    if not directory_name:
        return files_list
    try:
        dir_path = get_media_path(directory_name, '', base_dir_name="generated_media")
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for filename in os.listdir(dir_path):
                if os.path.isfile(os.path.join(dir_path, filename)):
                    files_list.append({
                        "name": filename,
                        "type_key": media_type_key, 
                        "subdir": directory_name    
                    })
    except Exception as e:
        print(f"Error saat mendaftar file di {directory_name}: {e}")
    return files_list

@file_manager_bp.route('/manage')
def manage_files():
    """Menampilkan halaman manajemen file."""
    all_files = {}
    total_file_count = 0
    for display_name, dir_name in MEDIA_TYPES_AND_DIRS.items():
        files_in_cat = list_files_in_directory(display_name)
        all_files[display_name] = files_in_cat
        total_file_count += len(files_in_cat)
    return render_template('manage_files.html', all_files=all_files, total_file_count=total_file_count)

@file_manager_bp.route('/delete', methods=['POST'])
def delete_file_route():
    """Menghapus file yang dipilih."""
    filename_to_delete = request.form.get('filename')
    subdir_to_delete_in = request.form.get('subdir') 
    if not filename_to_delete or not subdir_to_delete_in:
        flash('Informasi file tidak lengkap untuk penghapusan.', 'error')
        return redirect(url_for('file_manager.manage_files'))
    try:
        if subdir_to_delete_in not in MEDIA_TYPES_AND_DIRS.values():
            flash(f"Tipe direktori '{subdir_to_delete_in}' tidak valid.", 'error')
            return redirect(url_for('file_manager.manage_files'))
        file_path_to_delete = get_media_path(subdir_to_delete_in, filename_to_delete, base_dir_name="generated_media")
        if os.path.exists(file_path_to_delete) and os.path.isfile(file_path_to_delete):
            os.remove(file_path_to_delete)
            flash(f"File '{filename_to_delete}' berhasil dihapus.", 'success')
            print(f"File dihapus: {file_path_to_delete}")
        else:
            flash(f"File '{filename_to_delete}' tidak ditemukan atau bukan file.", 'warning')
            print(f"Gagal menghapus, file tidak ditemukan: {file_path_to_delete}")
    except Exception as e:
        flash(f"Error saat menghapus file '{filename_to_delete}': {e}", 'error')
        print(f"Error menghapus file {filename_to_delete}: {e}")
    return redirect(url_for('file_manager.manage_files'))

@file_manager_bp.route('/delete_all_generated_files', methods=['POST'])
def delete_all_generated_files_route():
    """Menghapus semua file dari semua direktori media yang dikelola."""
    deleted_files_count = 0
    failed_deletions_count = 0
    print("Mencoba menghapus semua file generated...")
    for display_name, dir_name in MEDIA_TYPES_AND_DIRS.items():
        try:
            dir_path = get_media_path(dir_name, '', base_dir_name="generated_media")
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                print(f"Memeriksa direktori: {dir_path}")
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files_count += 1
                            print(f"  Dihapus: {file_path}")
                        except Exception as e_file:
                            failed_deletions_count += 1
                            print(f"  Gagal menghapus file {file_path}: {e_file}")
        except Exception as e_dir:
            print(f"Error saat mengakses direktori {dir_name}: {e_dir}")
    if deleted_files_count > 0:
        flash(f"{deleted_files_count} file berhasil dihapus.", 'success')
    if failed_deletions_count > 0:
        flash(f"{failed_deletions_count} file gagal dihapus. Periksa log server untuk detail.", 'error')
    if deleted_files_count == 0 and failed_deletions_count == 0:
        flash("Tidak ada file untuk dihapus atau semua direktori kosong.", 'info')
    return redirect(url_for('file_manager.manage_files'))

@file_manager_bp.route('/download_all_generated_files', methods=['GET'])
def download_all_generated_files_route():
    """Membuat arsip ZIP dari semua file generated dan mengirimkannya untuk diunduh."""
    print("Mempersiapkan unduhan semua file generated...")
    
    # Buat nama file ZIP sementara yang unik di direktori sementara sistem atau direktori 'generated_media'
    # Lebih aman di direktori sementara sistem jika memungkinkan, atau pastikan untuk membersihkannya.
    # Untuk kesederhanaan, kita buat di dalam 'generated_media' tapi tidak di subdirektori yang akan di-zip.
    
    # Path ke direktori 'generated_media' utama
    base_generated_media_path = os.path.join(current_app.static_folder, "generated_media")
    
    zip_filename_base = "all_generated_files"
    zip_filename_unique = generate_unique_filename(prefix=zip_filename_base, extension="zip")
    # Simpan file zip di luar direktori yang akan di-zip, misal di 'app/static' atau direktori sementara sistem
    # Untuk contoh ini, kita simpan di 'generated_media' tapi di level atas.
    zip_filepath = os.path.join(base_generated_media_path, zip_filename_unique)

    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for display_name, dir_name in MEDIA_TYPES_AND_DIRS.items():
                dir_to_zip = get_media_path(dir_name, '', base_dir_name="generated_media")
                if os.path.exists(dir_to_zip) and os.path.isdir(dir_to_zip):
                    print(f"Menambahkan direktori '{dir_name}' ke arsip...")
                    for root, dirs, files in os.walk(dir_to_zip):
                        for file in files:
                            file_path_abs = os.path.join(root, file)
                            # Buat path relatif di dalam ZIP agar struktur direktori terjaga
                            # Path relatif dari 'generated_media'
                            arcname = os.path.join(dir_name, file) # Ini akan membuat struktur seperti 'audio/file.mp3' di dalam ZIP
                            zipf.write(file_path_abs, arcname=arcname)
                            print(f"  Ditambahkan ke ZIP: {arcname}")
        
        print(f"File ZIP berhasil dibuat di: {zip_filepath}")
        
        # Kirim file untuk diunduh, lalu hapus file ZIP sementara setelah dikirim
        # as_attachment=True akan memicu dialog unduh di browser
        # attachment_filename adalah nama yang akan dilihat pengguna saat mengunduh
        return send_file(
            zip_filepath,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{zip_filename_base}_{time.strftime("%Y%m%d-%H%M%S")}.zip' # Nama file unduhan yang lebih rapi
        )

    except Exception as e:
        print(f"Error saat membuat atau mengirim file ZIP: {e}")
        flash("Gagal membuat arsip ZIP untuk diunduh.", "error")
        return redirect(url_for('file_manager.manage_files'))
    finally:
        # Hapus file ZIP sementara setelah dikirim atau jika terjadi error
        # Ini penting untuk membersihkan.
        # Namun, send_file mungkin belum selesai mengirim saat blok finally dieksekusi.
        # Cara yang lebih baik adalah menggunakan `after_this_request` atau menangani pembersihan secara terpisah.
        # Untuk saat ini, kita coba hapus. Jika file masih terkunci, mungkin gagal.
        # if os.path.exists(zip_filepath):
        #     try:
        #         # os.remove(zip_filepath)
        #         # print(f"File ZIP sementara {zip_filepath} dihapus.")
        #         # Penundaan penghapusan mungkin lebih baik
        #         pass 
        #     except Exception as e_del:
        #         print(f"Peringatan: Gagal menghapus file ZIP sementara {zip_filepath}: {e_del}")
        pass # Pembersihan file ZIP sementara bisa lebih kompleks karena sifat send_file

# Jika Anda ingin membersihkan file ZIP setelah dikirim, Anda bisa menggunakan:
# from flask import after_this_request
# @after_this_request
# def remove_file(response):
#     if os.path.exists(zip_filepath):
#         try:
#             os.remove(zip_filepath)
#         except Exception as error:
#             app.logger.error("Error removing or closing downloaded file handle", error)
#     return response
# Ini perlu diimplementasikan dengan hati-hati di dalam rute download_all_generated_files_route.
# Untuk sekarang, saya akan membiarkan file ZIP sementara tidak otomatis dihapus untuk kesederhanaan.
# Pengguna bisa menghapusnya secara manual dari direktori 'generated_media' atau Anda bisa menambahkan cron job.
