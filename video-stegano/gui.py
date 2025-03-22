import vlc
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
from steganography import embed_message_in_video, extract_message_from_video
import time

# GUI
class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography in Video")
        
        # Input Video
        self.label_video = tk.Label(root, text="Pilih Video:")
        self.label_video.grid(row=0, column=0, padx=10, pady=10)
        self.entry_video = tk.Entry(root, width=50)
        self.entry_video.grid(row=0, column=1, padx=10, pady=10)
        self.button_video = tk.Button(root, text="Browse", command=self.browse_video)
        self.button_video.grid(row=0, column=2, padx=10, pady=10)
        
        # Input Pesan/File
        self.label_message = tk.Label(root, text="Pesan/File:")
        self.label_message.grid(row=1, column=0, padx=10, pady=10)
        self.entry_message = tk.Entry(root, width=50)
        self.entry_message.grid(row=1, column=1, padx=10, pady=10)
        self.button_message = tk.Button(root, text="Browse", command=self.browse_message)
        self.button_message.grid(row=1, column=2, padx=10, pady=10)
        
        # Kunci
        self.label_key = tk.Label(root, text="Kunci (opsional):")
        self.label_key.grid(row=2, column=0, padx=10, pady=10)
        self.entry_key = tk.Entry(root, width=50)
        self.entry_key.grid(row=2, column=1, padx=10, pady=10)
        
        # Frame dan Pixel Options
        self.label_frame = tk.Label(root, text="Frame:")
        self.label_frame.grid(row=3, column=0, padx=10, pady=10)
        self.frame_option = ttk.Combobox(root, values=["Sekuensial", "Acak"])
        self.frame_option.grid(row=3, column=1, padx=10, pady=10)
        self.frame_option.current(0)
        
        self.label_pixel = tk.Label(root, text="Pixel:")
        self.label_pixel.grid(row=4, column=0, padx=10, pady=10)
        self.pixel_option = ttk.Combobox(root, values=["Sekuensial", "Acak"])
        self.pixel_option.grid(row=4, column=1, padx=10, pady=10)
        self.pixel_option.current(0)
        
        # Checkbox untuk Enkripsi
        self.use_encryption = tk.BooleanVar()
        self.checkbox_encryption = tk.Checkbutton(
            root, text="Gunakan Enkripsi", variable=self.use_encryption
        )
        self.checkbox_encryption.grid(row=5, column=0, padx=10, pady=10)
        
        # Tombol Embed dan Extract
        self.button_embed = tk.Button(root, text="Embed Pesan", command=self.embed_message)
        self.button_embed.grid(row=6, column=0, padx=10, pady=10)
        self.button_extract = tk.Button(root, text="Extract Pesan", command=self.extract_message)
        self.button_extract.grid(row=6, column=1, padx=10, pady=10)
        
        # Tombol Play Video
        self.button_play = tk.Button(root, text="Play Video", command=self.play_video)
        self.button_play.grid(row=6, column=2, padx=10, pady=10)
        
        # Label untuk Menampilkan PSNR
        self.label_psnr = tk.Label(root, text="PSNR: - dB")
        self.label_psnr.grid(row=7, column=0, columnspan=3, padx=10, pady=10)
        
        # Inisialisasi VLC Instance
        self.vlc_instance = vlc.Instance("--no-xlib")  # Nonaktifkan Xlib untuk menghindari error
        self.vlc_player = self.vlc_instance.media_player_new()
        self.stego_video_path = None
    
    def browse_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
        self.entry_video.delete(0, tk.END)
        self.entry_video.insert(0, file_path)
    
    def browse_message(self):
        file_path = filedialog.askopenfilename()
        self.entry_message.delete(0, tk.END)
        self.entry_message.insert(0, file_path)
    
    def embed_message(self):
        video_path = self.entry_video.get()
        message_path = self.entry_message.get()
        key = self.entry_key.get()
        sequential_frames = self.frame_option.get() == "Sekuensial"
        sequential_pixels = self.pixel_option.get() == "Sekuensial"
        use_encryption = self.use_encryption.get()
        
        if not video_path or not message_path:
            messagebox.showerror("Error", "Harap pilih video dan pesan/file.")
            return
        
        try:
            output_video_path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI Files", "*.avi")])
            if output_video_path:
                result = embed_message_in_video(video_path, message_path, output_video_path, key, sequential_frames, sequential_pixels, use_encryption)
                
                if isinstance(result, tuple):
                    avg_psnr = result[0]
                else:
                    avg_psnr = result
                
                if avg_psnr == float('inf'):
                    self.label_psnr.config(text="PSNR: Video asli dan stego identik (tidak ada perubahan).")
                else:
                    self.label_psnr.config(text=f"PSNR: {avg_psnr:.2f} dB")
                messagebox.showinfo("Sukses", "Pesan berhasil disisipkan ke dalam video.")
                
                # Simpan path video stego untuk pemutaran
                self.stego_video_path = output_video_path
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def extract_message(self):
        video_path = self.entry_video.get()
        key = self.entry_key.get()
        use_encryption = self.use_encryption.get()
        
        if not video_path:
            messagebox.showerror("Error", "Harap pilih video.")
            return
        
        try:
            message, original_filename, file_extension = extract_message_from_video(video_path, key, use_encryption)
            
            output_file_path = filedialog.asksaveasfilename(
                defaultextension=file_extension,
                filetypes=[("All Files", "*.*")],
                initialfile=original_filename
            )
            if output_file_path:
                with open(output_file_path, "wb") as f:
                    f.write(message)
                logging.info(f"File disimpan di: {output_file_path}")
                messagebox.showinfo("Sukses", "File berhasil diekstrak dari video.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def play_video(self):
        """Memutar video stego menggunakan VLC Player."""
        if hasattr(self, 'stego_video_path') and self.stego_video_path:
            media = self.vlc_instance.media_new(self.stego_video_path)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            
            # Tunggu hingga video selesai diputar
            while self.vlc_player.is_playing():
                time.sleep(1)
            
            # Hentikan dan bersihkan VLC Player setelah selesai
            self.vlc_player.stop()
            self.vlc_player.release()
        else:
            messagebox.showerror("Error", "Tidak ada video stego yang tersedia untuk diputar.")
