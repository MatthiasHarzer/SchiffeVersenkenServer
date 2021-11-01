import os
import random

PATH = os.path.dirname(os.path.realpath(__file__))

NAMES_FILE_PATH = f'{PATH}/names.txt'


def genericName():
    with open(NAMES_FILE_PATH, "r") as file:
        lines = file.readlines()

        return lines[round(random.random() * len(lines) - 1)].strip()


def uniqueRandomString(compare_list: list[str], length: int = 5) -> str:
    s = ''.join(random.choice([chr(i) for i in range(ord('a'), ord('z'))]) for _ in range(length))
    while s in compare_list:
        s = ''.join(random.choice([chr(i) for i in range(ord('a'), ord('z'))]) for _ in range(length))
    return s


if __name__ == "__main__":
    print(genericName())
