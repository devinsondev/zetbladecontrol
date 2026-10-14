"""Offline packet construction smoke tests. Run python -m unittest discover -s tests."""
import sys
import types
import unittest
from unittest import mock
sys.modules.setdefault("hid", types.SimpleNamespace())
from blade_protocol import KEYS, SKIPS, BladeDevice, effect_packet, custom_packets, validate_color


class ProtocolTests(unittest.TestCase):
    def test_key_count(self):
        self.assertEqual(len(KEYS), 104)
        self.assertEqual(len(set(KEYS)), 104)

    def test_effect(self):
        packet = effect_packet("Static", "Blue", 2, 4)
        self.assertEqual(len(packet), 65)
        self.assertEqual(packet[:3], bytes([4, 0xAE, 1]))
        self.assertEqual(packet[5:9], bytes([2, 2, 4, 2]))

    def test_custom_profile(self):
        packets = custom_packets(["#010203"] * 104, 4)
        self.assertEqual(len(packets), 9)
        self.assertTrue(all(len(p) == 65 for p in packets))
        self.assertEqual(packets[0][5:9], bytes([0x1C, 2, 4, 0xFF]))
        self.assertEqual(packets[0][9:13], bytes([0x80, 1, 2, 3]))
        self.assertEqual(packets[0][13], 0x82)  # skipped key ID 0x81
        self.assertEqual(packets[-1][41], 0xFF)

    def test_bad_color(self):
        with self.assertRaises(ValueError):
            custom_packets(["invalid"] * 104, 4)
        # bytes.fromhex() silently ignores spaces: reject these before encoding.
        with self.assertRaises(ValueError):
            validate_color("#AA BB ")

    def test_windows_hid_write_reports_64(self):
        device = BladeDevice()
        device.dev = mock.Mock()
        device.dev.write.return_value = 64
        packet = effect_packet("Static", "Blue", 2, 4)
        with mock.patch("blade_protocol.sys.platform", "win32"), mock.patch("blade_protocol.time.sleep"):
            device.send([packet])
        device.dev.write.assert_called_once_with(packet)

    def test_real_short_hid_writes_are_rejected(self):
        device = BladeDevice()
        device.dev = mock.Mock()
        packet = effect_packet("Static", "Blue", 2, 4)
        with mock.patch("blade_protocol.sys.platform", "win32"), mock.patch("blade_protocol.time.sleep"):
            for sent in (-1, 63):
                device.dev.write.return_value = sent
                with self.subTest(sent=sent), self.assertRaises(IOError):
                    device.send([packet])

    def test_invalid_hid_packet_length_is_rejected(self):
        device = BladeDevice()
        device.dev = mock.Mock()
        with self.assertRaises(ValueError):
            device.send([bytes(64)])
        device.dev.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
