import numpy as np
import math
import io
from pydub import AudioSegment


def calculate_psnr(wav_bytes1: bytes, wav_bytes2: bytes):
    """
    Calculate PSNR between two WAV files provided as bytes data using pydub.

    Uses the formula: PSNR = 10 * log_10((P_1^2)/(P_1^2+P_0^2-2*P_1*P_0))

    Args:
        wav_bytes1: Bytes data of the first WAV file
        wav_bytes2: Bytes data of the second WAV file

    Returns:
        PSNR value in dB
    """

    audio1: AudioSegment = AudioSegment.from_wav(io.BytesIO(wav_bytes1))
    audio2: AudioSegment = AudioSegment.from_wav(io.BytesIO(wav_bytes2))

    # Check if sample rates match
    if audio1.frame_rate != audio2.frame_rate:
        raise ValueError(
            f"Sample rates do not match: {audio1.frame_rate} vs {audio2.frame_rate}"
        )

    # Convert to mono
    if audio1.channels > 1:
        audio1 = audio1.set_channels(1)
    if audio2.channels > 1:
        audio2 = audio2.set_channels(1)

    # Make sure both audios have the same length
    min_length = min(len(audio1), len(audio2))
    audio1 = audio1[:min_length]
    audio2 = audio2[:min_length]

    # Get samples as numpy arrays
    # pydub samples are integers in the range [-2^(sample_width*8-1), 2^(sample_width*8-1)-1]
    samples1 = np.array(audio1.get_array_of_samples()).astype(np.float64)
    samples2 = np.array(audio2.get_array_of_samples()).astype(np.float64)

    # Normalize samples based on sample width
    max_value = float(2 ** (audio1.sample_width * 8 - 1))
    samples1 /= max_value
    samples2 /= max_value

    # Calculate P_0^2
    P0_squared = np.mean(np.square(samples1))

    # Calculate P_1^2
    P1_squared = np.mean(np.square(samples2))

    # Calculate P_1*P_0
    P1_P0 = np.mean(samples1 * samples2)

    # print(f"P0sq {P0_squared} P1sq {P1_squared} P0P1 {P1_P0}")

    # Calculate PSNR using the given formula
    numerator = P1_squared
    denominator = P1_squared + P0_squared - 2 * P1_P0

    # Avoid division by zero or negative values
    if denominator <= 0:
        if denominator == 0:
            return float("inf")
        else:
            # Handle negative values which can occur due to numerical precision
            return float("nan")

    psnr = 10 * math.log10(numerator / denominator)

    return psnr
