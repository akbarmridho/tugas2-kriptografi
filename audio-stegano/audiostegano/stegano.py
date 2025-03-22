import os
import struct
from audiostegano.config import ENCRYPTED, RANDOM_SHUFFLE
from audiostegano.input.input import load_audio_file, save_from_bytes
from audiostegano.algorithm.lsb import encode, decode
from audiostegano.algorithm.vigenere import encrypt, decrypt
from audiostegano.algorithm.psnr import calculate_psnr


def key_to_seed(key: str) -> int:
    seed = 0

    for ch in key:
        seed += ord(ch)

    return seed


def perform_encode(
    input_path: str,
    message_path: str,
    output_path: str,
    shuffle: bool,
    key: str | None = None,
):
    message_handle = open(message_path, "rb")
    message_bytes = message_handle.read()
    message_handle.close()

    header, input_raw = load_audio_file(input_path)
    filename = os.path.basename(message_path)
    filename_bytes = bytes(filename, encoding="ascii")

    # embed filename metadata
    filename_length_bytes = struct.pack(">I", len(filename))

    config = 0

    if key is not None:
        config = config | ENCRYPTED

    if shuffle:
        config = config | RANDOM_SHUFFLE

    print(f"Message payload {len(message_bytes)} bytes")

    total_message = filename_length_bytes + filename_bytes + message_bytes

    if key is not None:
        total_message = bytes(encrypt(bytearray(total_message), key))

    seed = None

    if key is not None:
        seed = key_to_seed(key)

    encoded = encode(input_raw, config, total_message, seed)

    save_from_bytes(header + encoded, output_path)
    psnr = calculate_psnr(header + input_raw, header + encoded)
    print(f"PSNR value: {psnr:2f}dB")


def perform_decode(
    input_path: str,
    output_path: str | None,
    key: str | None = None,
):
    header, input_raw = load_audio_file(input_path)

    seed = None

    if key is not None:
        seed = key_to_seed(key)

    decoded, config = decode(input_raw, seed)

    if config & ENCRYPTED:
        if key is None:
            raise Exception("File is encrypted. No key is provided.")
        else:
            decoded = bytes(decrypt(bytearray(decoded), key))

    decoded_arr = bytearray(decoded)

    filename_length = struct.unpack(">I", decoded_arr[:4])[0]
    filename = decoded_arr[4 : filename_length + 4].decode("ascii")
    payload = decoded_arr[filename_length + 4 :]

    print(f"Extracted message payload {len(payload)} bytes")

    final_output: str = ""

    if output_path is not None:
        if os.path.isfile(output_path):
            # out to this path
            final_output = output_path
        else:
            final_output = os.path.join(output_path, filename)
    else:
        final_output = filename

    print(f"Saving to {final_output}")

    with open(final_output, "wb") as w:
        w.write(bytes(payload))
