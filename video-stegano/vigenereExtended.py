class MissingInputError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

def encrypt(plaintext, key):
    """
    Mengenkripsi plaintext menggunakan Extended Vigenère Cipher.
    - plaintext: Bytes atau string yang akan dienkripsi.
    - key: Kunci untuk enkripsi (string).
    - Mengembalikan ciphertext dalam bentuk bytes.
    """
    errors = []

    # Validasi input
    if not plaintext:
        errors.append({"field": "plaintext", "message": "Plaintext is required"})
    if not key:
        errors.append({"field": "key", "message": "Key is required"})
    if errors:
        raise MissingInputError("Missing required input", errors)

    # Jika plaintext adalah bytes, konversi ke list of integers
    if isinstance(plaintext, bytes):
        plaintext = list(plaintext)
    else:
        plaintext = [ord(char) for char in plaintext]

    key = [ord(char) for char in key]
    key_length = len(key)
    encrypted_text = []

    for i in range(len(plaintext)):
        # Hitung indeks karakter terenkripsi
        encrypted_char_index = (plaintext[i] + key[i % key_length]) % 256
        encrypted_text.append(encrypted_char_index)

    # Konversi list of integers ke bytes
    return bytes(encrypted_text)

def decrypt(ciphertext, key):
    """
    Mendekripsi ciphertext menggunakan Extended Vigenère Cipher.
    - ciphertext: Bytes yang akan didekripsi.
    - key: Kunci untuk dekripsi (string).
    - Mengembalikan plaintext dalam bentuk bytes.
    """
    errors = []

    # Validasi input
    if not ciphertext:
        errors.append({"field": "ciphertext", "message": "Ciphertext is required"})
    if not key:
        errors.append({"field": "key", "message": "Key is required"})
    if errors:
        raise MissingInputError("Missing required input", errors)

    # Jika ciphertext adalah bytes, konversi ke list of integers
    if isinstance(ciphertext, bytes):
        ciphertext = list(ciphertext)
    else:
        ciphertext = [ord(char) for char in ciphertext]

    key = [ord(char) for char in key]
    key_length = len(key)
    decrypted_text = []

    for i in range(len(ciphertext)):
        # Hitung indeks karakter terdekripsi
        decrypted_char_index = (ciphertext[i] - key[i % key_length] + 256) % 256
        decrypted_text.append(decrypted_char_index)

    # Konversi list of integers ke bytes
    return bytes(decrypted_text)


