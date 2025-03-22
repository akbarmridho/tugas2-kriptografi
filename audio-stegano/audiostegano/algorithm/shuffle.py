import random


def shuffle(data: str, seed: int) -> str:
    ls = list(data)
    random.seed(seed)
    random.shuffle(ls)
    return "".join(ls)


def shuffle_arr(data: list, seed: int) -> list:
    random.seed(seed)
    random.shuffle(data)
    return data


def unshuffle(data: str, seed: int):
    ls_raw = list(data)
    n = len(ls_raw)
    # Perm is [1, 2, ..., n]
    perm = [i for i in range(1, n + 1)]
    # Apply sigma to perm
    shuffled_perm = shuffle_arr(perm, seed)
    # Zip and unshuffle
    zipped_ls = list(zip(ls_raw, shuffled_perm))
    zipped_ls.sort(key=lambda x: x[1])
    return "".join([a for (a, b) in zipped_ls])


# if __name__ == "__main__":
#     seed = 1
#     data = "Hello, World!"
#     print(f"Data: {data}")
#     shuffled = shuffle(data, seed)
#     print(f"Shuffled: {shuffled}")
#     unshuffled = unshuffle(shuffled, seed)
#     print(f"Unshuffled: {unshuffled}")
