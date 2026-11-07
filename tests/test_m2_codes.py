"""Milestone 2: short codes. Pure functions first, then wired into POST /shorten."""

from math import gcd

import pytest

from app.codes import ALPHABET, CODE_LENGTH, MULTIPLIER, SPACE, code_for_id, decode, encode, id_for_code
from tests.conftest import shorten


@pytest.mark.parametrize("n", [0, 1, 61, 62, 3843, 3844, 10**9, SPACE - 1])
def test_encode_decode_round_trip(n):
    assert decode(encode(n)) == n


def test_known_values():
    assert encode(0) == "0"
    assert encode(61) == "Z"
    assert encode(62) == "10"


def test_encode_rejects_negative_numbers():
    with pytest.raises(ValueError):
        encode(-1)


def test_alphabet_is_url_safe():
    assert len(ALPHABET) == 62
    assert set(encode(10**15)) <= set(ALPHABET)


def test_multiplier_is_invertible():
    assert gcd(MULTIPLIER, SPACE) == 1


def test_codes_are_fixed_length_and_unique():
    codes = [code_for_id(i) for i in range(1, 50_001)]
    assert all(len(c) == CODE_LENGTH for c in codes)
    assert len(set(codes)) == len(codes)


def test_codes_round_trip_to_ids():
    for i in (1, 2, 3, 12345, 987654321, SPACE - 1):
        assert id_for_code(code_for_id(i)) == i


def test_consecutive_ids_do_not_give_sequential_codes():
    a, b = code_for_id(1000), code_for_id(1001)
    assert a[:-1] != b[:-1], "Scramble the id before encoding"


@pytest.mark.parametrize("bad", [0, -1, SPACE])
def test_out_of_range_ids_are_rejected(bad):
    with pytest.raises(ValueError):
        code_for_id(bad)


def test_shorten_now_uses_7_character_codes(client):
    a = shorten(client).json()["code"]
    b = shorten(client).json()["code"]
    assert len(a) == len(b) == CODE_LENGTH
    assert set(a + b) <= set(ALPHABET)
    assert a[:-1] != b[:-1]
