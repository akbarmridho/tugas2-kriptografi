import argparse
import os
import traceback
from audiostegano.stegano import perform_encode, perform_decode


def validate_file_path(path, should_exist=True):
    """Validate file path exists if should_exist is True, or that parent directory exists if False."""
    if should_exist:
        if not os.path.isfile(path):
            raise argparse.ArgumentTypeError(f"File '{path}' does not exist")
    else:
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.isdir(parent_dir):
            raise argparse.ArgumentTypeError(f"Directory '{parent_dir}' does not exist")
    return path


def validate_key(key):
    """Validate key is a string with max length of 25 characters."""
    if len(key) > 25:
        raise argparse.ArgumentTypeError(f"Key must be at most 25 characters long")
    return key


def main():
    parser = argparse.ArgumentParser(description="File encoding and decoding tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    subparsers.required = True

    encode_parser = subparsers.add_parser("encode", help="Encode a file")

    encode_parser.add_argument(
        "input_file",
        type=lambda x: validate_file_path(x, True),
        help="Path to the input file",
    )

    encode_parser.add_argument(
        "message_file",
        type=lambda x: validate_file_path(x, True),
        help="Path to the message file",
    )

    encode_parser.add_argument(
        "output_file",
        type=lambda x: validate_file_path(x, False),
        help="Path to the output file",
    )

    encode_parser.add_argument(
        "--shuffle", action="store_true", help="Shuffle the data (optional)"
    )

    encode_parser.add_argument(
        "--key", type=validate_key, help="Encryption key (optional, max 25 characters)"
    )

    # Create parser for the "decode" command
    decode_parser = subparsers.add_parser("decode", help="Decode a file")

    decode_parser.add_argument(
        "input_file",
        type=lambda x: validate_file_path(x, True),
        help="Path to the input file",
    )

    decode_parser.add_argument(
        "output_file",
        type=lambda x: validate_file_path(x, False),
        help="Path to the output file (optional)",
        nargs="?",
    )

    decode_parser.add_argument(
        "--key", type=validate_key, help="Decryption key (optional, max 25 characters)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Process commands
    if args.command == "encode":
        try:
            perform_encode(
                args.input_file,
                args.message_file,
                args.output_file,
                args.shuffle,
                args.key,
            )

        except Exception as e:
            # print(traceback.format_exc())
            print(f"Error: {str(e)}")

    elif args.command == "decode":
        print(f"Decoding file: {args.input_file}")

        try:
            perform_decode(
                args.input_file,
                args.output_file,
                args.key,
            )
        except Exception as e:
            # print(traceback.format_exc())
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
