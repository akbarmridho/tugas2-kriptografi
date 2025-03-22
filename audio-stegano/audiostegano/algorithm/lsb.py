import struct  # For packing and unpacking the message length
from audiostegano.config import RANDOM_SHUFFLE
from audiostegano.algorithm.shuffle import shuffle, unshuffle


def encode(raw: bytes, config: int, messages: bytes, seed: int | None = None) -> bytes:
    """
    Encodes a secret message into an audio file using basic LSB steganography with message length.

    data is the audio data in bytes
    meta is the metadata of the messages
    """

    print("Encoding starts...")

    data = bytearray(raw)

    # Convert the secret message to bits
    secret_message_bits = "".join([bin(i).lstrip("0b").rjust(8, "0") for i in messages])

    # Add shuffling
    if config & RANDOM_SHUFFLE:
        if seed is None:
            raise Exception(
                "Seed cannot be None when using random shuffle. Consider adding secret key"
            )

        secret_message_bits = shuffle(secret_message_bits, seed)

    message_length = len(secret_message_bits)

    # Pack the length of the message into 4 bytes (32 bits)
    length_bytes = struct.pack(">I", message_length)  # '>I' is big-endian unsigned int

    # Convert the length bytes to bits
    length_bits = "".join(
        [bin(byte).lstrip("0b").rjust(8, "0") for byte in length_bytes]
    )

    # Pack the length of the message into 4 bytes (32 bits)
    meta_bytes = struct.pack(">I", config)  # '>I' is big-endian unsigned int

    # Convert the meta bytes to bits
    meta_bits = "".join([bin(byte).lstrip("0b").rjust(8, "0") for byte in meta_bytes])

    # Combine length bits and message bits
    full_bits = length_bits + meta_bits + secret_message_bits

    # Ensure the message fits into the frame bytes
    if len(full_bits) > len(data):
        raise ValueError("The message is too large to fit in the audio file.")

    # Encode the full bits into the frame bytes
    for i, bit in enumerate(full_bits):
        data[i] = (data[i] & 254) | int(bit)

    data_modified = bytes(data)

    print("Encoding success ...")

    return data_modified


def decode(raw: bytes, seed: int | None = None) -> tuple[bytes, int]:
    """
    Decodes a secret message from an audio bytes using basic LSB steganography with message length.

    :param input_file_path: Path to the encoded audio file
    :return: The decoded secret message
    """
    print("Decoding starts...")
    frame_bytes = bytearray(raw)

    # Extract the first 32 bits to determine the message length
    length_bits = "".join([str((frame_bytes[i] & 1)) for i in range(32)])
    message_length = struct.unpack(
        ">I", int(length_bits, 2).to_bytes(4, byteorder="big")
    )[0]

    config_bits = "".join([str((frame_bytes[i + 32] & 1)) for i in range(32)])
    config = struct.unpack(">I", int(config_bits, 2).to_bytes(4, byteorder="big"))[0]

    # Now extract the message bits using the extracted length
    if message_length > len(frame_bytes) * 8:
        raise ValueError(
            "The extracted message length is larger than the available audio data."
        )

    message_bits = "".join(
        [str((frame_bytes[i + 64] & 1)) for i in range(message_length)]
    )

    # Unshuffle
    if config & RANDOM_SHUFFLE:
        if seed is None:
            raise Exception(
                "Seed cannot be None when using random shuffle. Consider adding secret key"
            )

        message_bits = unshuffle(message_bits, seed)

    # Convert bits back to bytes
    decoded_message = bytes(
        bytearray(
            [int(message_bits[i : i + 8], 2) for i in range(0, len(message_bits), 8)]
        )
    )

    print("Decoding success")

    return decoded_message, config
