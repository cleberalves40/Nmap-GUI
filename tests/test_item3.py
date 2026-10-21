import tempfile
import unittest
from pathlib import Path

from nmap_gui.logic import NmapError, NmapLogic, ScanProfileStore


class ScanControlTests(unittest.TestCase):
    def setUp(self):
        self.logic = NmapLogic()
        self.logic.nmap_path = "nmap"

    def test_command_includes_ipv6_exclusions_and_tuning(self):
        command = self.logic.build_command(
            target="2001:db8::1",
            scan_type="-sV",
            ipv6=True,
            exclude_targets="2001:db8::2,2001:db8::3",
            top_ports=500,
            version_intensity=6,
        )

        self.assertIn("-6", command)
        self.assertIn("--exclude", command)
        self.assertIn("2001:db8::2,2001:db8::3", command)
        self.assertIn("--top-ports", command)
        self.assertIn("500", command)
        self.assertIn("--version-intensity", command)
        self.assertIn("6", command)

    def test_command_uses_target_file_as_single_argument(self):
        with tempfile.TemporaryDirectory() as directory:
            target_file = Path(directory) / "target list.txt"
            target_file.write_text("192.0.2.1\n192.0.2.2\n", encoding="utf-8")

            command = self.logic.build_command(target="", input_file=str(target_file))

        input_index = command.index("-iL")
        self.assertEqual(command[input_index + 1], str(target_file))
        self.assertNotIn(str(target_file), command[input_index + 2:])

    def test_target_source_and_port_controls_are_validated(self):
        with self.assertRaisesRegex(NmapError, "alvo ou um arquivo"):
            self.logic.build_command(target="", input_file="")
        with self.assertRaisesRegex(NmapError, "alvo ou um arquivo"):
            self.logic.build_command(target="192.0.2.1", input_file="targets.txt")
        with self.assertRaisesRegex(NmapError, "não existe"):
            self.logic.build_command(target="", input_file="missing-targets.txt")
        with self.assertRaisesRegex(NmapError, "exclusivas"):
            self.logic.build_command(target="192.0.2.1", ports="80", top_ports=100)
        with self.assertRaisesRegex(NmapError, "entre 1 e 65535"):
            self.logic.build_command(target="192.0.2.1", top_ports=0)
        with self.assertRaisesRegex(NmapError, "entre 0 e 9"):
            self.logic.build_command(target="192.0.2.1", version_intensity=10)

    def test_scan_profiles_save_list_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScanProfileStore(directory)
            profile = {
                "scan_type": "-sV",
                "ipv6": True,
                "top_ports_enabled": True,
                "top_ports": 500,
            }

            store.save_profile("IPv6 baseline", profile)
            self.assertEqual(store.list_profiles()["IPv6 baseline"], profile)
            store.delete_profile("IPv6 baseline")

            self.assertEqual(store.list_profiles(), {})


if __name__ == "__main__":
    unittest.main()