from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, ColorClip
import moviepy.video.fx.all as vfx 
import os
import random
import numpy as np 
from PIL import Image 
from scipy import signal # Meskipun vignette dihapus, scipy mungkin masih berguna untuk efek lain di masa depan

from app.utils import generate_unique_filename, get_media_path

VIDEO_SIZE = (1024, 720)

# --- Fungsi Efek Vignette Dihapus ---
# def apply_vignette_effect(clip):
#     # ... (kode vignette sebelumnya) ...

def apply_zoom_effect(clip, direction="in", zoom_magnitude=0.15, video_size=VIDEO_SIZE):
    if direction == "out":
        start_zoom = 1.0 + zoom_magnitude 
        end_zoom = 1.0                   
    else: # Zoom In
        start_zoom = 1.0
        end_zoom = 1.0 + zoom_magnitude
    def resize_func(t):
        current_progress = t / clip.duration
        current_zoom_factor = start_zoom + (end_zoom - start_zoom) * current_progress
        return current_zoom_factor
    return clip.fx(vfx.resize, resize_func).set_position('center', 'center')

# --- Fungsi Utama Pembuatan Video ---
def create_video_from_parts(story_segments_data, effect_settings=None, output_video_name_prefix="final_story_video"):
    video_clips = []
    print("\n--- MEMULAI PEMBUATAN VIDEO (Efek Vignette Dihapus Total) ---")
    
    if effect_settings is None: 
        effect_settings = {
            "enabled": True, 
            "fade_prob": 0.5, 
            "zoom_in_prob": 40, "zoom_out_prob": 20, "static_prob": 40 
        }
    
    effects_are_generally_enabled = effect_settings.get("enabled", False)

    if effects_are_generally_enabled:
        print("Efek visual (Motion, Fade) diaktifkan dengan pengaturan:", effect_settings)
    else:
        print("Semua efek visual (Motion, Fade) dinonaktifkan.")


    for i, segment_data in enumerate(story_segments_data):
        print(f"Memproses segmen video ke-{i+1}...")
        audio_path = segment_data.get('audio_path')
        image_paths = segment_data.get('image_paths', [])
        if not audio_path or not os.path.exists(audio_path): continue
        if not image_paths or not all(os.path.exists(p) for p in image_paths): continue

        try:
            audio_clip = AudioFileClip(audio_path)
            segment_audio_duration = audio_clip.duration
            if segment_audio_duration <= 0: audio_clip.close(); continue
            
            duration_per_image = segment_audio_duration / len(image_paths)
            if duration_per_image < 0.5 and effects_are_generally_enabled:
                print(f"  Peringatan: Durasi gambar pendek ({duration_per_image:.2f}s), efek motion/fade mungkin tidak optimal.")
            
            segment_image_fx_clips = []
            for img_idx, img_path in enumerate(image_paths):
                try:
                    img_clip_orig = ImageClip(img_path).set_duration(duration_per_image)
                    resized_clip_w_first = img_clip_orig.fx(vfx.resize, width=VIDEO_SIZE[0])
                    if resized_clip_w_first.h < VIDEO_SIZE[1]:
                        base_for_effects = resized_clip_w_first.fx(vfx.resize, height=VIDEO_SIZE[1])
                    else:
                        base_for_effects = resized_clip_w_first
                    current_fx_clip = base_for_effects.fx(vfx.crop, 
                                                      x_center=base_for_effects.w / 2, 
                                                      y_center=base_for_effects.h / 2, 
                                                      width=VIDEO_SIZE[0], 
                                                      height=VIDEO_SIZE[1])
                    
                    if effects_are_generally_enabled:
                        # Pemanggilan apply_vignette_effect(current_fx_clip) DIHAPUS
                        # print("    Efek: Vignette (Otomatis jika efek umum aktif)") # Log ini juga dihapus
                        
                        motion_probs = {
                            "zoom_in": effect_settings.get("zoom_in_prob", 40),
                            "zoom_out": effect_settings.get("zoom_out_prob", 20),
                            "static": effect_settings.get("static_prob", 40) 
                        }
                        total_prob = sum(motion_probs.values())
                        if total_prob == 0: motion_probs["static"] = 100; total_prob = 100
                        
                        chosen_effect = "static" 
                        if total_prob > 0:
                            rand_motion_val = random.uniform(0, total_prob) 
                            cumulative_prob = 0
                            effect_order = ["zoom_in", "zoom_out", "static"]
                            for effect_name in effect_order:
                                if motion_probs[effect_name] > 0:
                                    cumulative_prob += motion_probs[effect_name]
                                    if rand_motion_val < cumulative_prob:
                                        chosen_effect = effect_name
                                        break
                        
                        print(f"    Efek Motion Dipilih: {chosen_effect.replace('_',' ').capitalize()}")
                        if chosen_effect == "zoom_in":
                            current_fx_clip = apply_zoom_effect(current_fx_clip, direction="in", zoom_magnitude=0.15)
                        elif chosen_effect == "zoom_out":
                            current_fx_clip = apply_zoom_effect(current_fx_clip, direction="out", zoom_magnitude=0.10)
                        
                        if random.random() < effect_settings.get("fade_prob", 0.5): 
                            print("    Efek: Fade In")
                            fade_duration = min(0.5, duration_per_image * 0.2)
                            current_fx_clip = current_fx_clip.fadein(fade_duration)
                    
                    final_image_clip_on_canvas = CompositeVideoClip(
                        [current_fx_clip.set_position('center', 'center')],
                        size=VIDEO_SIZE, bg_color=(0,0,0) 
                    ).set_duration(duration_per_image)
                    segment_image_fx_clips.append(final_image_clip_on_canvas)
                except Exception as e_img:
                    print(f"Error memproses gambar {img_path} untuk segmen {i+1}: {e_img}. Melewati.")
                    continue
            
            if not segment_image_fx_clips: audio_clip.close(); continue

            concatenated_images_for_segment = concatenate_videoclips(segment_image_fx_clips, method="compose")
            segment_video_clip = concatenated_images_for_segment.set_audio(audio_clip)
            video_clips.append(segment_video_clip)
            print(f"Segmen video ke-{i+1} berhasil diproses.")

        except Exception as e_seg:
            print(f"Error saat memproses segmen video ke-{i+1} dengan MoviePy: {e_seg}")
            if 'audio_clip' in locals() and audio_clip: audio_clip.close()
            if 'concatenated_images_for_segment' in locals() and concatenated_images_for_segment: concatenated_images_for_segment.close()
            for clip_fx in segment_image_fx_clips if 'segment_image_fx_clips' in locals() else []: clip_fx.close()


    if not video_clips: return None

    try:
        final_video = concatenate_videoclips(video_clips, method="compose")
        output_filename = generate_unique_filename(prefix=output_video_name_prefix, extension="mp4")
        output_filepath = get_media_path("videos", output_filename)
        print(f"Menulis video akhir ke: {output_filepath}...")
        final_video.write_videofile(output_filepath, fps=24, codec='libx264', audio_codec='aac', threads=os.cpu_count() or 4, preset='fast', logger='bar')
        print("Video akhir berhasil dibuat.")
        return output_filepath
    except Exception as e_final:
        print(f"Error saat menggabungkan atau menulis video akhir: {e_final}")
        return None
    finally:
        if 'final_video' in locals() and final_video: final_video.close()
        for clip_group in video_clips: 
            if hasattr(clip_group, 'audio') and clip_group.audio: clip_group.audio.close()
            clip_group.close()
        print("Semua klip MoviePy telah ditutup.")
