"""Milestone 2: short codes. Database id -> scrambled number -> 7-character base62 string.

Before writing code, answer these in your notes (the study guide explains them):
  1. Why base62 (0-9a-zA-Z) and not base64?
  2. Why derive codes from a unique id instead of hashing the URL?
  3. Why scramble the id first, and why does scrambling NOT break uniqueness?
"""

from __future__ import annotations

import string
from math import gcd

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase  # "0-9a-zA-Z"
BASE = len(ALPHABET)  # 62
CODE_LENGTH = 7
SPACE = BASE**CODE_LENGTH  # number of possible 7-character codes. Work out how many that is.

# The scramble is: (id * MULTIPLIER + OFFSET) mod SPACE.
# It is a bijection (every id maps to a DIFFERENT number) only because
# MULTIPLIER shares no prime factor with SPACE = 62**7 = 2**7 * 31**7.
MULTIPLIER = 2_654_435_761   # Knuth's multiplicative-hashing constant: odd, and not a multiple of 31
OFFSET = 1_234_567_890
assert gcd(MULTIPLIER, SPACE) == 1
_INVERSE = pow(MULTIPLIER, -1, SPACE)  # undoes the multiplication: (x * MULTIPLIER * _INVERSE) % SPACE == x

_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}  # "0" -> 0, "a" -> 10, "Z" -> 61


def encode(n: int) -> str:
    """Non-negative integer -> base62 string, most significant digit first.

    TODO(M2): the same algorithm you'd use to write a number in base 2 or base 16:
      - n < 0  -> raise ValueError
      - n == 0 -> "0"
      - otherwise repeat `n, rem = divmod(n, BASE)`, collecting ALPHABET[rem],
        then reverse the collected digits.
    Check: encode(61) == "Z", encode(62) == "10"
    """
    raise NotImplementedError("TODO(M2): encode")


def decode(s: str) -> int:
    """Base62 string -> integer (the inverse of encode).

    TODO(M2): start at 0; for each character, n = n * BASE + _INDEX[ch].
    """
    raise NotImplementedError("TODO(M2): decode")


def code_for_id(id_: int) -> str:
    """Database id -> fixed-length, non-sequential 7-character code.

    TODO(M2):
      - id_ must satisfy 0 < id_ < SPACE, else ValueError
      - scrambled = (id_ * MULTIPLIER + OFFSET) % SPACE
      - encode it and left-pad to CODE_LENGTH with ALPHABET[0] (str.rjust)
    """
    raise NotImplementedError("TODO(M2): code_for_id")


def id_for_code(code: str) -> int:
    """Inverse of code_for_id. The tests use it to prove the scramble is a bijection.

    TODO(M2): undo the steps in reverse order: decode, subtract OFFSET, multiply by _INVERSE, mod SPACE.
    """
    raise NotImplementedError("TODO(M2): id_for_code")
