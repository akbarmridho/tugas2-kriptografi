import cv2
import os
import numpy as np
from subprocess import call, STDOUT
from vigenereExtended import encrypt, decrypt
import logging
import random 
import re

# Konfigurasi logger
logging.basicConfig(
    level=logging.DEBUG,  # Level logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format pesan log
    filename='steganography.log',  # Menyimpan log ke file
    filemode='w'  # Mode file: 'w' untuk menulis ulang, 'a' untuk menambahkan
)

# Fungsi untuk mengekstrak frame dari video
def extract_frames(video_path, output_folder):
    logging.info(f"Mengekstrak frame dari video: {video_path}")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.debug(f"Membuat folder: {output_folder}")
    
    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()
    count = 0
    
    while success:
        frame_path = os.path.join(output_folder, f"frame{count}.png")
        cv2.imwrite(frame_path, image)
        success, image = vidcap.read()
        count += 1
    
    logging.info(f"Total frame yang diekstrak: {count}")
    return count

# Fungsi untuk memeriksa apakah video memiliki audio
def has_audio(video_path):
    command = [
        "ffprobe",  # Gunakan ffprobe untuk memeriksa metadata video
        "-i", video_path,
        "-show_streams",  # Tampilkan informasi stream
        "-select_streams", "a",  # Pilih hanya stream audio
        "-loglevel", "error"  # Hanya tampilkan pesan error
    ]
    
    try:
        # Jalankan perintah ffprobe
        call(command, stdout=open(os.devnull, "w"), stderr=STDOUT)
        return True  
    except Exception:
        return False  # Jika ada error, video tidak memiliki audio

# Fungsi untuk mengekstrak audio dari video
def extract_audio(video_path, output_audio_path):
    logging.info(f"Mengekstrak audio dari video: {video_path}")
    
    # Periksa apakah video memiliki audio
    if not has_audio(video_path):
        logging.warning(f"Video {video_path} tidak memiliki audio.")
        return False  # Kembalikan False jika tidak ada audio
    
    # Pastikan direktori output ada
    output_dir = os.path.dirname(output_audio_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.debug(f"Membuat direktori: {output_dir}")
    
    # Perintah FFmpeg untuk mengekstrak audio
    command = [
        "ffmpeg",
        "-i", video_path,  # Input video
        "-q:a", "0",       # Kualitas audio terbaik
        "-map", "a",       # Pilih stream audio
        output_audio_path, # Output audio
        "-y"               # Overwrite output file jika sudah ada
    ]
    
    try:
        # Jalankan perintah FFmpeg
        call(command, stdout=open(os.devnull, "w"), stderr=STDOUT)
        logging.info(f"Audio disimpan di: {output_audio_path}")
        return True  # Kembalikan True jika berhasil
    except Exception as e:
        logging.error(f"Gagal mengekstrak audio: {e}")
        raise RuntimeError(f"Gagal mengekstrak audio dari video: {e}")
    
# Fungsi untuk membuat video dari frame
def create_video_from_frames(frame_folder, output_video_path, fps=30):
    logging.info(f"Membuat video dari frame di folder: {frame_folder}")
    
    # Ambil semua frame PNG
    frames = [img for img in os.listdir(frame_folder) if img.endswith(".png")]
    if not frames:
        raise FileNotFoundError("Tidak ada frame PNG di folder.")
    
    # Urutkan berdasarkan nomor frame
    frames.sort(key=lambda x: int(re.search(r'\d+', x).group()))
    
    # Path video sementara
    temp = output_video_path.replace(".avi", "_noaudio.avi")
    
    # Cek ukuran frame pertama
    frame = cv2.imread(os.path.join(frame_folder, frames[0]))
    if frame is None:
        raise RuntimeError("Frame pertama tidak bisa dibaca.")
    
    height, width, _ = frame.shape
    
    # Gunakan codec yang stabil
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    video = cv2.VideoWriter(temp, fourcc, fps, (width, height))
    
    if not video.isOpened():
        raise RuntimeError("Gagal membuka VideoWriter.")
    
    # Tulis setiap frame ke video
    for frame_name in frames:
        frame_path = os.path.join(frame_folder, frame_name)
        frame = cv2.imread(frame_path)
        if frame is None:
            logging.warning(f"Frame {frame_path} tidak bisa dibaca, dilewati.")
            continue
        
        video.write(frame)
    
    # Tutup VideoWriter
    video.release()
    logging.info(f"Video berhasil disimpan di: {temp}")
    
    return temp

# Fungsi untuk menyisipkan pesan ke dalam frame menggunakan LSB
def encode_message_in_frame(frame, message, frame_index, sequential_pixels=True, seed=None):
    """
    Menyisipkan pesan ke dalam frame menggunakan metode LSB.
    - frame: Frame gambar tempat pesan akan disisipkan.
    - message: Pesan yang akan disisipkan (dalam bentuk byte).
    - frame_index: Indeks frame (digunakan untuk logging).
    - sequential_pixels: True jika pixel dipilih sekuensial, False jika acak.
    - seed: Seed untuk random generator jika pixel acak.
    - Mengembalikan jumlah bit yang berhasil disisipkan.
    """
    # Konversi pesan ke biner
    binary_message = ''.join(format(byte, '08b') for byte in message)
    message_length = len(binary_message)
    logging.debug(f"Sisipkan pesan ke dalam frame {frame_index}. Panjang pesan: {message_length} bit.")
    
    # Periksa apakah pesan terlalu besar untuk frame
    if message_length > frame.size * 3:
        raise ValueError("Pesan terlalu besar untuk disisipkan dalam frame ini.")
    
    # Jika pixel acak, inisialisasi random generator dengan seed
    if not sequential_pixels:
        if seed is not None:
            random.seed(seed)  # Gunakan seed untuk memastikan urutan acak yang sama
        # Buat daftar semua koordinat pixel
        height, width, _ = frame.shape
        pixels = [(i, j) for i in range(height) for j in range(width)]
        random.shuffle(pixels)  # Acak urutan pixel
    
    index = 0  # Indeks untuk melacak bit pesan yang sudah disisipkan
    for i in range(frame.shape[0]):
        for j in range(frame.shape[1]):
            # Jika pixel acak, gunakan urutan yang sudah diacak
            if not sequential_pixels:
                i, j = pixels[index // 3]  # Ambil pixel berikutnya dari daftar acak
            
            for k in range(3):  # Untuk setiap channel (R, G, B)
                if index < message_length:
                    original_pixel = frame[i, j, k]
                    modified_pixel = (original_pixel & 0xFE) | int(binary_message[index])
                    frame[i, j, k] = modified_pixel
                    
                    index += 1
                else:
                    logging.debug(f"Semua bit pesan telah disisipkan. Total bit yang disisipkan: {index}")
                    return index  # Kembalikan jumlah bit yang berhasil disisipkan
    
    logging.debug(f"Semua bit pesan telah disisipkan. Total bit yang disisipkan: {index}")
    return index  # Kembalikan jumlah bit yang berhasil disisipkan

def decode_message_from_frame(frame, message_length, sequential_pixels=True, seed=None):
    """
    Mengekstrak pesan dari frame menggunakan metode LSB.
    
    Parameters:
    - frame: Gambar (array numpy) yang akan diekstrak pesannya.
    - message_length: Panjang pesan yang akan diekstrak (dalam byte).
    - sequential_pixels: True jika pixel dipilih secara sekuensial, False jika acak.
    - seed: Seed untuk random generator jika pixel dipilih secara acak.
    
    Returns:
    - message (bytes): Pesan yang diekstrak.
    """
    if frame is None:
        raise ValueError("Frame tidak boleh None")

    height, width, _ = frame.shape
    total_bits = message_length * 8  # Konversi panjang pesan ke bit
    binary_message = []
    
    # Jika pixel acak, acak urutan akses pixel dengan seed tertentu
    if not sequential_pixels:
        if seed is not None:
            random.seed(seed)  # Gunakan seed yang sama seperti saat penyisipan
        # Buat daftar semua koordinat pixel
        pixels = [(i, j) for i in range(height) for j in range(width)]
        random.shuffle(pixels)  # Acak urutan pixel
    else:
        pixels = [(i, j) for i in range(height) for j in range(width)]  # Default sequential

    bit_count = 0  # Menghitung bit yang sudah diekstrak

    for (i, j) in pixels:
        for channel in range(3):  # Loop untuk setiap channel warna (R, G, B)
            if bit_count < total_bits:
                lsb = frame[i, j, channel] & 1  # Ekstrak bit LSB
                binary_message.append(str(lsb))
                bit_count += 1
            else:
                # Jika semua bit sudah diambil, konversi biner ke bytes
                byte_message = bytes([int("".join(binary_message[i:i+8]), 2) for i in range(0, len(binary_message), 8)])
                return byte_message

    # Konversi seluruh bit menjadi byte (untuk memastikan pesan tetap terbaca)
    byte_message = bytes([int("".join(binary_message[i:i+8]), 2) for i in range(0, len(binary_message), 8)])
    return byte_message

# Fungsi utama untuk menyisipkan pesan ke dalam video
def embed_message_in_video(video_path, file_to_embed, output_video_path, key=None, sequential_frames=True, sequential_pixels=True, useEncryption=False):
    logging.info("Memulai proses penyisipan pesan ke dalam video")
    
    # Baca file yang akan disisipkan
    try:
        with open(file_to_embed, "rb") as f:
            file_data = f.read()  # Baca seluruh konten file sebagai bytes
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_to_embed}")
        raise FileNotFoundError(f"File tidak ditemukan: {file_to_embed}")
    
    # Ambil nama file dan format asli dari file yang disisipkan
    original_filename = os.path.basename(file_to_embed)
    original_extension = os.path.splitext(original_filename)[1]
    
    # Tentukan method code berdasarkan metode penyisipan
    if sequential_frames:
        if sequential_pixels:
            method_code = "11"  # Frame sekuensial, pixel sekuensial
        else:
            method_code = "12"  # Frame sekuensial, pixel acak
    else:
        if sequential_pixels:
            method_code = "21"  # Frame acak, pixel sekuensial
        else:
            method_code = "22"  # Frame acak, pixel acak
    
    # Buat header untuk nama file, format, panjang pesan, dan metode penyisipan
    header = f"FILE_NAME:{original_filename}\nFILE_EXT:{original_extension}\nMSG_LEN:{len(file_data)}\nMETHOD:{method_code}\n".encode()
    
    # Gabungkan header dan file data menjadi satu pesan
    message = file_data
    logging.info(f"Header: {header}")
    logging.info(f"Panjang pesan sebelum ditambahkan header: {len(file_data)}")
    logging.info(f"Panjang pesan setelah ditambahkan header: {len(message)}")

    if key and useEncryption:
        logging.debug(f"Mengenkripsi pesan menggunakan kunci: {key}")
        message = encrypt(message, key)
        header = encrypt(header, key)
    
    frame_folder = "tmp_frames"
    audio_path = "tmp/audio.mp3"


    # Ekstrak frame dan audio dari video
    frame_count = extract_frames(video_path, frame_folder)
    extract_audio(video_path, audio_path)
    logging.info(f"Total frame dalam video: {frame_count}")

    # Sisipkan pesan ke dalam frame
    message_length = len(message) * 8  # Panjang pesan dalam bit
    
    # Inisialisasi random generator dengan seed dari key jika ada
    if key:
        random.seed(sum(ord(char) for char in key))  # Gunakan key sebagai seed
    
    # Pilih frame yang akan disisipi pesan
    if sequential_frames:
        selected_frames = range(frame_count)  # Semua frame sekuensial
    else:
        selected_frames = random.sample(range(frame_count), frame_count)  # Frame acak
    
    logging.info(f"Frame yang akan disisipi pesan: {selected_frames}")
    total_bits_embedded = 0  # Jumlah total bit yang telah disisipkan

    # Sisipkan header pada frame pertama yang dipilih
    header_frame_index = selected_frames[0]  # Frame pertama dalam urutan yang dipilih
    header_frame_path = os.path.join(frame_folder, f"frame{header_frame_index}.png")
    header_frame = cv2.imread(header_frame_path)

    if header_frame is None:
        logging.error(f"Frame {header_frame_index} gagal dimuat dari {header_frame_path}.")
        raise RuntimeError(f"Frame {header_frame_index} gagal dimuat dari {header_frame_path}.")

    # Simpan salinan frame sebelum dimodifikasi
    old_frame = header_frame.copy()

    # Sisipkan header pada frame pertama (pixel sekuensial)
    header_bits = ''.join(format(byte, '08b') for byte in header)
    header_length = len(header_bits)
    bits_embedded = 0

    for i in range(header_frame.shape[0]):
        for j in range(header_frame.shape[1]):
            for k in range(3):  # Untuk setiap channel (R, G, B)
                if bits_embedded < header_length:
                    original_pixel = header_frame[i, j, k]
                    modified_pixel = (original_pixel & 0xFE) | int(header_bits[bits_embedded])
                    header_frame[i, j, k] = modified_pixel
                    bits_embedded += 1
                else:
                    break
            if bits_embedded >= header_length:
                break
        if bits_embedded >= header_length:
            break

    # Simpan frame yang telah dimodifikasi
    cv2.imwrite(header_frame_path, header_frame)
    logging.info(f"Header disimpan pada frame {header_frame_index}. Total bit header: {header_length}")

    # Sisipkan pesan utama pada frame selanjutnya
    total_bits_embedded = 0
    for i in selected_frames[1:]:  # Mulai dari frame kedua dalam urutan yang dipilih
        frame_path = os.path.join(frame_folder, f"frame{i}.png")
        frame = cv2.imread(frame_path)

        if frame is None:
            logging.error(f"Frame {i} gagal dimuat dari {frame_path}.")
            continue  # Lewati frame jika tidak bisa dimuat

        # Sisipkan pesan ke dalam frame
        logging.info(f"message potong: {message[total_bits_embedded // 8:]}")
        bits_embedded = encode_message_in_frame(frame, message[total_bits_embedded // 8:], i, sequential_pixels, seed=key)
        total_bits_embedded += bits_embedded

        # Simpan frame yang telah dimodifikasi
        cv2.imwrite(frame_path, frame)
        debug_frame_path = os.path.join("debug_frames", f"frame{i}_debug.png")
        cv2.imwrite(debug_frame_path, frame)

        logging.info(f"Frame {i} telah disisipi {bits_embedded} bit pesan dan disimpan ke {frame_path}.")
        logging.info(f"Salinan frame debug disimpan di: {debug_frame_path}")

        # Jika semua bit pesan telah disisipkan, hentikan proses
        if total_bits_embedded >= message_length:
            break

    # Buat video dari frame
    cap = cv2.VideoCapture(video_path)
    # Ambil FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    create_video_from_frames(frame_folder, output_video_path, fps)
    cap.release()
    temp = output_video_path.replace(".avi", "_noaudio.avi") 
    command = [
        "ffmpeg",
        "-i", temp,  # Tanpa tanda kutip berlebih
        "-i", "tmp/audio.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        output_video_path,  # Gunakan file output sementara
        "-y"
    ]

    try:
        # Jalankan perintah FFmpeg dan tangkap output serta error
        logging.debug(f"Menjalankan perintah: {' '.join(command)}")
        process = call(command, stdout=open(os.devnull, "w"), stderr=STDOUT)
        
        if process == 0:
            logging.info(f"Video dengan pesan tersisip disimpan di: {output_video_path}")
        else:
            logging.error(f"Gagal menggabungkan audio dan video: Proses FFmpeg mengembalikan kode error {process}")
    except Exception as e:
        logging.error(f"Gagal menggabungkan audio dan video: {e}")
        raise RuntimeError(f"Gagal menggabungkan audio dan video: {e}")
    
    # Hitung PSNR antara video asli dan video stego
    avg_psnr, psnr_per_frame = calculate_average_psnr(video_path)
    
    # Hitung rata-rata PSNR dengan mengabaikan nilai inf
    avg_psnr_fixed = calculate_average_psnr_fixed(psnr_per_frame)
    
    logging.info(f"PSNR rata-rata (mengabaikan inf): {avg_psnr_fixed:.2f} dB")
    logging.info(f"Nilai PSNR per frame: {psnr_per_frame}")
    
    return avg_psnr_fixed, psnr_per_frame

# Fungsi utama untuk mengekstrak pesan dari video
def extract_message_from_video(video_path, key=None, use_encryption=False):
    """
    Mengekstrak pesan dari video.
    
    Parameters:
    - video_path: Path ke video yang akan diekstrak pesannya.
    - key: Kunci untuk dekripsi atau seed untuk randomisasi.
    - use_encryption: True jika pesan dienkripsi, False jika tidak.
    
    Returns:
    - message (bytes): Pesan yang diekstrak.
    - original_filename (str): Nama file asli.
    - file_extension (str): Ekstensi file asli.
    """
    logging.info("Memulai proses ekstraksi pesan dari video")
    logging.info(f"key: {key}")
    logging.info(f"use_encryption: {use_encryption}")
    
    frame_folder = "tmp_frames_extract"
    audio_path = "tmp/audio_extract.mp3"
    
    # Ekstrak frame dan audio dari video
    frame_count = extract_frames(video_path, frame_folder)
    extract_audio(video_path, audio_path)
    logging.info(f"Total frame dalam video: {frame_count}")
    
    # Tentukan urutan frame berdasarkan key
    if key:
        random.seed(sum(ord(char) for char in key))  # Gunakan key sebagai seed
        frame_order = random.sample(range(frame_count), frame_count)  # Frame acak
        logging.info(f"Menggunakan seed dari key untuk memilih frame acak. Urutan frame: {frame_order}")
    else:
        frame_order = list(range(frame_count))  # Frame sekuensial
        logging.info("Menggunakan metode sekuensial untuk memilih frame.")

    # Cari header pada frame pertama yang dipilih
    header_frame_index = frame_order[0]  # Frame pertama dalam urutan yang dipilih
    header_frame_path = os.path.join(frame_folder, f"frame{header_frame_index}.png")
    header_frame = cv2.imread(header_frame_path)
    
    if header_frame is None:
        logging.error(f"Gagal membaca frame {header_frame_index} yang berisi header.")
        return None, None, None

    # Ekstrak header dari frame pertama (pixel sekuensial)
    header_data = decode_message_from_frame(header_frame, 500, sequential_pixels=True, seed=None)
    
    if key and use_encryption:
        logging.debug(f"Mendekripsi header menggunakan kunci: {key}")
        header_data = decrypt(header_data, key)

    # Jika header tidak ditemukan atau tidak valid pada frame pertama yang dipilih secara acak,
    # coba cari header pada frame 0 (frame pertama secara sekuensial)
    if not header_data or not header_data.startswith(b"FILE_NAME:"):
        logging.info("Header tidak ditemukan atau tidak valid pada frame pertama yang dipilih secara acak. Mencoba pada frame 0.")
        header_frame_index = 0  # Frame 0 (frame pertama secara sekuensial)
        header_frame_path = os.path.join(frame_folder, f"frame{header_frame_index}.png")
        header_frame = cv2.imread(header_frame_path)
        
        if header_frame is None:
            logging.error(f"Gagal membaca frame {header_frame_index} yang berisi header.")
            return None, None, None

        # Ekstrak header dari frame 0 (pixel sekuensial)
        header_data = decode_message_from_frame(header_frame, 500, sequential_pixels=True, seed=None)
        if key and use_encryption:
            logging.debug(f"Mendekripsi header menggunakan kunci: {key}")
            header_data = decrypt(header_data, key)

        if not header_data or not header_data.startswith(b"FILE_NAME:"):
            logging.error("Header tidak ditemukan atau tidak valid pada frame 0.")
            return None, None, None

    try:
        # Pisahkan header sebagai byte
        header_lines = header_data.split(b"\n")[:4]
        
        original_filename = header_lines[0].decode().split(":")[1]
        file_extension = header_lines[1].decode().split(":")[1]
        msg_len = int(header_lines[2].decode().split(":")[1])
        method_code = header_lines[3].decode().split(":")[1]
    except (IndexError, ValueError, UnicodeDecodeError) as e:
        logging.error(f"Error parsing header: {e}")
        return None, None, None
    
    logging.debug(f"Metode penyisipan: {method_code}")
    logging.debug(f"Panjang pesan: {msg_len}")
    logging.debug(f"Nama file: {original_filename}")
    logging.debug(f"Ekstensi file: {file_extension}")

    # Jika metode penyisipan adalah frame sekuensial, ubah frame_order menjadi range(1, frame_count)
    if method_code.startswith("1"):  # Frame sekuensial
        frame_order = list(range(1, frame_count))  # Mulai dari frame kedua
        logging.info("Metode penyisipan adalah frame sekuensial. Menggunakan urutan frame sekuensial.")
    else:
        frame_order = frame_order[1:]  # Mulai dari frame kedua
        logging.info("Metode penyisipan adalah frame acak. Menggunakan urutan frame yang sudah diacak.")

    # Dekode pesan
    total_msg_length = msg_len
    message = b""
    
    bits_extracted = 0

    # Tentukan sequential_pixels berdasarkan method_code
    sequential_pixels = method_code.endswith("1")  # True jika pixel sekuensial, False jika acak

    # Ekstrak pesan dari frame selanjutnya (mulai dari frame kedua)
    for i in frame_order:
        frame_path = os.path.join(frame_folder, f"frame{i}.png")
        frame = cv2.imread(frame_path)

        if frame is None:
            logging.warning(f"Gagal membaca frame {i}, berhenti ekstraksi.")
            break
        
        # Ekstrak pesan dari frame
        logging.info(f"Ekstrak pesan dari frame {i}")
        logging.info(f"sequential_pixels: {sequential_pixels}")
        extracted_data = decode_message_from_frame(frame, (total_msg_length - bits_extracted), sequential_pixels, seed=key)
        message += extracted_data
        bits_extracted += len(extracted_data)

        if bits_extracted >= total_msg_length:
            break  # Hentikan jika sudah mendapatkan semua data

    # Dekripsi pesan jika enkripsi diaktifkan
    if use_encryption and key:
        logging.debug(f"Mendekripsi pesan menggunakan kunci: {key}")
        message = decrypt(message, key)
    
    # Log byte hasil ekstraksi
    logging.info(f"Byte hasil ekstraksi: {message}")
    logging.info(f"Panjang byte hasil ekstraksi: {len(message)}")

    # Simpan file yang diekstrak
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.join(output_folder, original_filename)
    
    with open(output_file_path, "wb") as f:
        f.write(message)

    logging.info(f"File disimpan sebagai: {output_file_path}")
    
    return message, original_filename, file_extension

def calculate_psnr(frame1, frame2):
    """
    Menghitung PSNR (Peak Signal-to-Noise Ratio) antara dua frame.
    
    Parameters:
    - frame1: Frame pertama (video asli).
    - frame2: Frame kedua (video stego).
    
    Returns:
    - psnr: Nilai PSNR dalam dB.
    """
    if frame1.shape != frame2.shape:
        raise ValueError("Ukuran frame tidak sama.")
    
    # Hitung Mean Squared Error (MSE)
    mse = np.mean((frame1 - frame2) ** 2)
    
    # Jika MSE = 0, PSNR adalah tak terhingga
    if mse == 0:
        return float('inf')
    
    # Hitung PSNR
    max_pixel = 255.0  # Nilai maksimum pixel untuk gambar 8-bit
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return psnr

def calculate_average_psnr(original_video_path):
    """
    Menghitung PSNR rata-rata antara video asli dan video stego per frame.
    
    Parameters:
    - original_video_path: Path ke video asli.
    - stego_video_path: Path ke video stego.
    
    Returns:
    - avg_psnr: Nilai PSNR rata-rata dalam dB.
    - psnr_per_frame: List nilai PSNR untuk setiap frame.
    """
    logging.info("Menghitung PSNR antara video asli dan video stego per frame.")
    
    # Ekstrak frame dari video asli
    original_frame_folder = "tmp_original_frames"
    original_frame_count = extract_frames(original_video_path, original_frame_folder)
    
    # Ekstrak frame dari video stego
    stego_frame_folder = "tmp_frames"
    stego_frame_count = original_frame_count  # Jumlah frame harus sama
    
    if original_frame_count != stego_frame_count:
        raise ValueError("Jumlah frame video asli dan video stego tidak sama.")
    
    total_psnr = 0.0
    frame_count = 0
    psnr_per_frame = []  # List untuk menyimpan nilai PSNR per frame
    
    # Hitung PSNR untuk setiap frame
    for i in range(original_frame_count):
        original_frame_path = os.path.join(original_frame_folder, f"frame{i}.png")
        stego_frame_path = os.path.join(stego_frame_folder, f"frame{i}.png")
        
        original_frame = cv2.imread(original_frame_path)
        stego_frame = cv2.imread(stego_frame_path)
        
        if original_frame is None or stego_frame is None:
            logging.warning(f"Frame {i} tidak bisa dibaca, dilewati.")
            continue
        
        psnr = calculate_psnr(original_frame, stego_frame)
        psnr_per_frame.append(psnr)  # Simpan nilai PSNR untuk frame ini
        total_psnr += psnr
        frame_count += 1
    
    # Hitung PSNR rata-rata
    avg_psnr = total_psnr / frame_count if frame_count > 0 else 0
    logging.info(f"PSNR rata-rata: {avg_psnr} dB")
    logging.info(f"Nilai PSNR per frame: {psnr_per_frame}")
    
    return avg_psnr, psnr_per_frame

def calculate_average_psnr_fixed(psnr_per_frame):
    """
    Menghitung rata-rata PSNR dengan mengabaikan nilai infinity.

    Parameters:
    - psnr_per_frame: List nilai PSNR untuk setiap frame.

    Returns:
    - avg_psnr: Nilai PSNR rata-rata dalam dB (mengabaikan inf jika ada).
    """
    # Filter hanya nilai PSNR yang finite
    finite_psnr_values = [psnr for psnr in psnr_per_frame if np.isfinite(psnr)]
    
    # Jika tidak ada nilai finite, maka video identik dan PSNR rata-rata adalah inf
    if len(finite_psnr_values) == 0:
        return float('inf')
    
    # Hitung rata-rata hanya dari nilai finite
    avg_psnr = np.mean(finite_psnr_values)
    return avg_psnr

# # File yang disisipkan
# file_to_embed = "test.png"
# # with open(file_to_embed, "w") as f:
# #     f.write("Hello, World!")

# # Sisipkan pesan ke dalam video
# embed_message_in_video("input_video.avi", file_to_embed, "output_video.avi")

# # Ekstrak pesan dari video
# extracted_message, filename, extension = extract_message_from_video("output_video.avi")
# print(f"File diekstrak sebagai: {filename}{extension}") 
