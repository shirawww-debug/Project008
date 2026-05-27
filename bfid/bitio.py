"""Lecture/écriture de champs binaires en convention "LSB d'abord".

Le rapport de beamforming compressé empile des champs de taille arbitraire
(2 à 9 bits par angle). La convention utilisée ici suit l'ordre des bits de
la norme 802.11 (B0, B1, ...) : dans chaque octet le bit de poids faible est
transmis en premier, et la valeur d'un champ multi-bits est reconstruite avec
son premier bit comme LSB.

BitWriter et BitReader sont strictement symétriques, ce qui est vérifié par
les tests de round-trip (test_bitio.py, test_report.py).

NOTE PERF : l'implémentation est bit-à-bit (claire mais lente). Pour des
captures volumineuses (80/160 MHz), vectoriser via numpy.unpackbits. Voir
docs/ROADMAP.md.
"""

from __future__ import annotations


class BitWriter:
    """Accumule des champs entiers et produit des octets (LSB d'abord)."""

    def __init__(self) -> None:
        self._bits: list[int] = []

    def write(self, value: int, nbits: int) -> "BitWriter":
        if value < 0:
            raise ValueError("BitWriter.write attend une valeur non signée")
        if value >> nbits:
            raise ValueError(f"value={value} ne tient pas sur {nbits} bits")
        for i in range(nbits):
            self._bits.append((value >> i) & 1)
        return self

    @property
    def bit_length(self) -> int:
        return len(self._bits)

    def to_bytes(self) -> bytes:
        out = bytearray()
        for i in range(0, len(self._bits), 8):
            byte = 0
            for j, bit in enumerate(self._bits[i:i + 8]):
                byte |= (bit & 1) << j
            out.append(byte)
        return bytes(out)


class BitReader:
    """Lit des champs entiers depuis des octets (LSB d'abord)."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def read(self, nbits: int) -> int:
        if self._pos + nbits > len(self._data) * 8:
            raise EOFError("Lecture au-delà de la fin du buffer")
        value = 0
        for i in range(nbits):
            byte_index, bit_index = divmod(self._pos, 8)
            bit = (self._data[byte_index] >> bit_index) & 1
            value |= bit << i
            self._pos += 1
        return value

    @property
    def bits_read(self) -> int:
        return self._pos

    @property
    def bits_remaining(self) -> int:
        return len(self._data) * 8 - self._pos
