"""Champ VHT MIMO Control (3 octets) de l'Action frame de beamforming.

Disposition des bits (B0 = LSB du premier octet) :
    B0-B2   Nc Index            (Nc = index + 1)
    B3-B5   Nr Index            (Nr = index + 1)
    B6-B7   Channel Width
    B8-B9   Grouping (Ng index)
    B10     Codebook Information
    B11     Feedback Type        (0 = SU, 1 = MU)
    B12-B14 Remaining Feedback Segments
    B15     First Feedback Segment
    B16-B17 Reserved
    B18-B23 Sounding Dialog Token Number
"""

from __future__ import annotations

from dataclasses import dataclass

from . import spec
from .bitio import BitReader, BitWriter


@dataclass
class VhtMimoControl:
    nc: int
    nr: int
    channel_width: int       # brut 0..3
    grouping: int            # brut 0..3 (index Ng)
    codebook: int            # 0/1
    feedback_type: int       # 0 = SU, 1 = MU
    remaining_segments: int = 0
    first_segment: int = 1
    sounding_token: int = 0

    @property
    def width_mhz(self) -> int:
        return spec.CHANNEL_WIDTH_MHZ[self.channel_width]

    @property
    def ng(self) -> int:
        return spec.GROUPING_NG[self.grouping]

    @property
    def feedback_name(self) -> str:
        return "MU" if self.feedback_type else "SU"

    @property
    def num_subcarriers(self) -> int:
        return spec.num_subcarriers(self.width_mhz, self.ng)

    @property
    def bits_psi_phi(self) -> tuple[int, int]:
        return spec.angle_bits(self.feedback_name, self.codebook)


def parse_mimo_control(data: bytes) -> VhtMimoControl:
    if len(data) < 3:
        raise ValueError("Le champ VHT MIMO Control fait 3 octets")
    r = BitReader(data[:3])
    nc = r.read(3) + 1
    nr = r.read(3) + 1
    channel_width = r.read(2)
    grouping = r.read(2)
    codebook = r.read(1)
    feedback_type = r.read(1)
    remaining = r.read(3)
    first = r.read(1)
    r.read(2)  # reserved
    token = r.read(6)
    return VhtMimoControl(
        nc=nc, nr=nr, channel_width=channel_width, grouping=grouping,
        codebook=codebook, feedback_type=feedback_type,
        remaining_segments=remaining, first_segment=first, sounding_token=token,
    )


def pack_mimo_control(m: VhtMimoControl) -> bytes:
    w = BitWriter()
    w.write(m.nc - 1, 3)
    w.write(m.nr - 1, 3)
    w.write(m.channel_width, 2)
    w.write(m.grouping, 2)
    w.write(m.codebook, 1)
    w.write(m.feedback_type, 1)
    w.write(m.remaining_segments, 3)
    w.write(m.first_segment, 1)
    w.write(0, 2)  # reserved
    w.write(m.sounding_token, 6)
    return w.to_bytes()
