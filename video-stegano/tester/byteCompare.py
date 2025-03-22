def compare_files_detailed(file1, file2):
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        data1 = f1.read()
        data2 = f2.read()

    min_length = min(len(data1), len(data2))
    differences = []
    similarities = []

    for i in range(min_length):
        if data1[i] != data2[i]:
            differences.append((i, data1[i], data2[i]))
        else:
            similarities.append((i, data1[i]))

    # Cek apakah ukuran file berbeda
    if len(data1) != len(data2):
        print(f" Files have different sizes: {len(data1)} vs {len(data2)} bytes")

    # Menampilkan perbedaan
    if differences:
        print(f"\n Found {len(differences)} byte differences:")
        for index, byte1, byte2 in differences[:10]:  # Batasi tampilan pertama
            print(f"Byte {index}: {byte1:#04x} -> {byte2:#04x}")
        print("...")
    else:
        print("\nFiles are completely identical!")

    # Menampilkan persamaan
    if similarities:
        print(f"\n Found {len(similarities)} identical bytes:")
        for index, byte in similarities[:10]:  # Batasi tampilan pertama
            print(f"Byte {index}: {byte:#04x} (same)")
        print("...")

compare_files_detailed("hasil.jpg", "original.jpg")
