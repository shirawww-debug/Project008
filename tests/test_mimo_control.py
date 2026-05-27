import pytest

from bfid.mimo_control import VhtMimoControl, pack_mimo_control, parse_mimo_control


def test_pack_parse_roundtrip():
    m = VhtMimoControl(
        nc=2, nr=4, channel_width=2, grouping=0, codebook=1,
        feedback_type=1, remaining_segments=3, first_segment=1, sounding_token=42,
    )
    packed = pack_mimo_control(m)
    assert len(packed) == 3
    out = parse_mimo_control(packed)
    assert (out.nc, out.nr) == (2, 4)
    assert out.channel_width == 2 and out.grouping == 0
    assert out.codebook == 1 and out.feedback_type == 1
    assert out.remaining_segments == 3 and out.first_segment == 1
    assert out.sounding_token == 42


def test_derived_properties():
    m = VhtMimoControl(nc=1, nr=2, channel_width=2, grouping=0,
                       codebook=1, feedback_type=0)
    assert m.width_mhz == 80
    assert m.ng == 1
    assert m.feedback_name == "SU"
    assert m.num_subcarriers == 234
    assert m.bits_psi_phi == (4, 6)


def test_short_buffer_rejected():
    with pytest.raises(ValueError):
        parse_mimo_control(b"\x00\x00")
