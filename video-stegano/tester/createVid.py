import os
import cv2
import logging

def create_video_from_frames(frame_folder, output_video_path, fps=30):
    """
    Membuat video dari frame-frame di folder tertentu menggunakan codec lossless.
    
    :param frame_folder: Folder yang berisi frame-frame (format PNG).
    :param output_video_path: Path untuk menyimpan video output.
    :param fps: Frame rate video (default: 30).
    :return: Path video sementara tanpa audio.
    """
    logging.info(f"Membuat video dari frame di folder: {frame_folder}")
    
    # Dapatkan daftar frame dan urutkan berdasarkan nomor
    frames = [img for img in os.listdir(frame_folder) if img.endswith(".png")]
    frames.sort(key=lambda x: int(x[5:-4]))  # Mengurutkan frame berdasarkan nomor
    
    # Path video sementara tanpa audio
    temp = output_video_path.replace(".avi", "_noaudio.avi")
    
    # Baca frame pertama untuk mendapatkan ukuran video
    frame = cv2.imread(os.path.join(frame_folder, frames[0]))
    height, width, layers = frame.shape
    
    # Gunakan codec lossless (FFV1 atau H.264 dengan CRF 0)
    # fourcc = cv2.VideoWriter_fourcc(*'FFV1')  # Codec FFV1 (lossless)
    fourcc = cv2.VideoWriter_fourcc('R', 'G', 'B', 'A') # Alternatif: H.264 dengan CRF 0
    
    # Buat VideoWriter dengan codec lossless
    video = cv2.VideoWriter(temp, fourcc, fps, (width, height))
    
    if not video.isOpened():
        logging.error("Gagal membuka VideoWriter. Pastikan codec dan path output valid.")
        raise RuntimeError("Gagal membuka VideoWriter.")
    
    # Tulis setiap frame ke video
    for frame_name in frames:
        frame_path = os.path.join(frame_folder, frame_name)
        frame = cv2.imread(frame_path)
        video.write(frame)
    
    # Tutup VideoWriter
    video.release()
    logging.info(f"Video disimpan di: {temp}")
    
    return temp  # Kembalikan path video sementara

# Contoh penggunaan
if __name__ == "__main__":
    frame_folder = "tmp_frames"  # Ganti dengan folder frame yang ingin digabungkan
    output_video_path = "output.avi"  # Ganti dengan path video output
    create_video_from_frames(frame_folder, output_video_path)
