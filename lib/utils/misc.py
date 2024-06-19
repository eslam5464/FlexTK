import random
import re
import string
from itertools import islice
from typing import Iterable, Generator, Any


def split_iterable_by_chunk(iterable: Iterable, chunk_size: int) -> Generator:
    """
    Given an iterable parameter the function returns a generator for
    the iterable that is split by the number of chunks
    \n**example:** \n split_iterable_by_chunk('ABCDEFG', 3) --> ABC DEF G
    :param iterable: Series of data like list or tuple etc.
    :param chunk_size: Integer value of chunk size
    :return: Generator of tuple for each chunk
    :raise ValueError: if chunk_size less than 1
    """
    if chunk_size < 1:
        raise ValueError('chunk_size must be at greater than or equal to 1')

    it = iter(iterable)

    while batch := tuple(islice(it, chunk_size)):
        yield batch


def validate_text(text: str, regex_pattern: str) -> bool:
    """
    Validates a string using a regular expression pattern
    :param text: String to be validated
    :param regex_pattern: Regular expression pattern to match against the text
    :return: Boolean indicating whether the string is valid or not
    """
    return True if re.match(regex_pattern, text) else False


def find_indices(list_to_check: list, item_to_find: Any) -> list[int]:
    """
    Find all available indices for an item in the list,
    \n**example:** \n find_indices([1,2,2,4,5,2], 2) --> [1,2,6]
    :param list_to_check: List of values to check for indices
    :param item_to_find: Any variable to check if it is in the list
    :return: A list of occurrences of the item inside list_to_check
    """
    return [idx for idx, value in enumerate(list_to_check) if value == item_to_find]


def generate_random_password(length=15):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"

    return ''.join(
        [
            random.choice(string.ascii_letters),
            *[random.choice(characters) for _ in range(length - 1)]
        ]
    )


for _ in range(30):
    print(generate_random_password())
