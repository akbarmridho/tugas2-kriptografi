import cv2

def extract_header_from_frame(frame):
    """
    Mengekstrak header dari frame yang telah disisipkan pesan menggunakan metode LSB.
    - frame: Frame gambar yang akan diekstrak headernya.
    - Mengembalikan header dalam bentuk bytes jika berhasil, None jika gagal.
    """
    binary_header = ''
    index = 0
    
    # Header diasumsikan memiliki panjang 500 byte (4000 bit)
    header_length = 500 * 8  # Panjang header dalam bit
    
    # Ekstrak bit LSB dari pixel-pixel awal
    for i in range(frame.shape[0]):
        for j in range(frame.shape[1]):
            for k in range(3):  # Untuk setiap channel (R, G, B)
                if index < header_length:
                    binary_header += str(frame[i, j, k] & 1)  # Ekstrak bit LSB
                    index += 1
                else:
                    # Konversi binary header ke bytes
                    header_bytes = bytes([int(binary_header[i:i+8], 2) for i in range(0, len(binary_header), 8)])
                    return header_bytes
    
    # Konversi binary header ke bytes
    header_bytes = bytes([int(binary_header[i:i+8], 2) for i in range(0, len(binary_header), 8)])
    return header_bytes

# Contoh penggunaan
if __name__ == "__main__":
    # Baca gambar (frame) dari file
    image_path = "frame0.png"  # Ganti dengan path gambar yang ingin diperiksa
    frame = cv2.imread(image_path)

    if frame is None:
        print("Gagal membaca gambar. Pastikan path gambar benar.")
    else:
        # Ekstrak header dari gambar
        header = extract_header_from_frame(frame)
        
        if header:
            print("Header berhasil diekstrak dalam bytes:")
            print(header)  # Menampilkan hasil ekstraksi dalam bytes
        else:
            print("Gagal mengekstrak header. Gambar mungkin tidak mengandung pesan yang disisipkan.")

