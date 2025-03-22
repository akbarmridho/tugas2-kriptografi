def encrypt(data: bytearray, key: str) -> bytearray:
    """
    Encrypts plaintext using the extended Vigenère cipher with the given key.
    """
    cipher: list[int] = []
    key_length = len(key)

    for i in range(len(data)):
        p = data[i]
        k = ord(key[i % key_length])

        c = (p + k) % 256

        cipher.append(c)

    return bytearray(cipher)


def decrypt(cipher: bytearray, key: str) -> bytearray:
    """
    Decrypts ciphertext using the extended Vigenère cipher with the given key.
    """
    plain: list[int] = []
    key_length = len(key)

    for i in range(len(cipher)):
        c = cipher[i]
        k = ord(key[i % key_length])

        p = (c - k) % 256

        plain.append(p)

    return bytearray(plain)


# if __name__ == "__main__":
#     key = "yeah"
#     data = "Hello, World!"
#     print(f"Data: {data}, Key: {key}")
#     encrypted = encrypt(bytearray(data, "utf-8"), key)
#     print(f"encrypted: {str(encrypted)}")
#     decrypted = decrypt(encrypted, key)
#     print(f"decrypted: {str(decrypted)}")
