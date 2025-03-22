from pydub import AudioSegment
import io


def load_audio_file(path: str) -> bytes:
    """
    Load any audio file and convert it to WAV format in memory

    Args:
        path (str): Path to the input audio file

    Returns:
        bytes: WAV file as bytes
    """
    audio: AudioSegment = AudioSegment.from_file(path)
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)
    wav_bytes = wav_io.getvalue()

    header = wav_bytes[:44]
    data = wav_bytes[44:]

    return header, data


def save_from_bytes(data: bytes, path: str):
    with open(path, "wb") as w:
        w.write(data)
