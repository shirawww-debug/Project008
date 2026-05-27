import numpy as np

from bfid.bitio import BitReader, BitWriter


def test_roundtrip_random_fields():
    rng = np.random.default_rng(0)
    fields = [(int(rng.integers(0, 2 ** b)), int(b))
              for b in rng.integers(1, 10, size=500)]
    w = BitWriter()
    for value, nbits in fields:
        w.write(value, nbits)
    r = BitReader(w.to_bytes())
    for value, nbits in fields:
        assert r.read(nbits) == value


def test_lsb_first_layout():
    w = BitWriter()
    w.write(1, 1)   # bit 0
    w.write(0, 1)   # bit 1
    w.write(1, 1)   # bit 2
    # octet attendu : 0b00000101 = 5
    assert w.to_bytes() == bytes([5])


def test_write_overflow_rejected():
    w = BitWriter()
    try:
        w.write(8, 3)  # 8 ne tient pas sur 3 bits
    except ValueError:
        return
    raise AssertionError("overflow non détecté")


def test_read_past_end():
    r = BitReader(bytes([0xFF]))
    r.read(8)
    try:
        r.read(1)
    except EOFError:
        return
    raise AssertionError("lecture hors limite non détectée")
