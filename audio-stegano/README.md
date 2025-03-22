# Audio Steganography

## How to Install

- Tested on Python 3.12.
- Install `pydub` with `pip install pydub audioop-lts numpy`.
- Install FFMPEG.

## Run the Program

```python
python ./main.py -h
```

## Commands

```plain
usage: main.py [-h] {encode,decode} ...

File encoding and decoding tool

positional arguments:
  {encode,decode}  Commands
    encode         Encode a file
    decode         Decode a file

options:
  -h, --help       show this help message and exit
```

### Encode

The PSNR value is being printed out after the encoding operation success.

```plain
usage: main.py encode [-h] [--shuffle] [--key KEY] input_file message_file output_file

positional arguments:
  input_file    Path to the input file
  message_file  Path to the message file
  output_file   Path to the output file

options:
  -h, --help    show this help message and exit
  --shuffle     Shuffle the data (optional)
  --key KEY     Encryption key (optional, max 25 characters)
```

### Decode

```plain
usage: main.py decode [-h] [--key KEY] input_file [output_file]

positional arguments:
  input_file   Path to the input file
  output_file  Path to the output file (optional)

options:
  -h, --help   show this help message and exit
  --key KEY    Decryption key (optional, max 25 characters)
```

## Example

### Without encryption

**Encoding:**

```python
python ./main.py encode ./sample/butai-ni-tatte.aac ./sample/butai-ni-tatte.txt ./output/butai-ni-tatte.enc.wav
```

**Decoding:**

```python
python ./main.py decode ./output/butai-ni-tatte.enc.wav
```

### Encryption without Shuffling

**Encoding:**

```python
python ./main.py encode --key YOASOBI ./sample/yuusha.aac ./sample/yuusha.txt ./output/yuusha.enc.wav
```

**Decoding:**

```python
python ./main.py decode --key YOASOBI ./output/yuusha.enc.wav
```

### Encryption with Shuffling

**Encoding:**

```python
python ./main.py encode --shuffle --key YOASOBI ./sample/new-me.mp3 ./sample/new-me.txt ./output/new-me.enc.wav
```

**Decoding:**

```python
python ./main.py decode --key YOASOBI ./output/new-me.enc.wav
```
