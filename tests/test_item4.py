import unittest
from unittest.mock import patch

from nmap_gui.logic import (
    NmapError,
    is_nmap_version_outdated,
    latest_stable_nmap_tag,
    parse_nmap_version,
)
from nmap_gui.window import NmapVersionCheckWorker


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class NmapVersionTests(unittest.TestCase):
    def test_latest_stable_tag_ignores_prereleases(self):
        tags = [
            {"name": "v7.99"},
            {"name": "v7.992"},
            {"name": "v7.100beta1"},
            {"name": "v7.991"},
        ]

        self.assertEqual(latest_stable_nmap_tag(tags), "7.992")

    def test_version_comparison_is_numeric(self):
        self.assertTrue(is_nmap_version_outdated("Nmap version 7.99", "7.992"))
        self.assertFalse(is_nmap_version_outdated("Nmap version 7.993", "7.992"))
        self.assertEqual(
            parse_nmap_version("Nmap version 7.99 ( https://nmap.org )"),
            (7, 99),
        )

    def test_invalid_versions_and_empty_tag_sets_are_rejected(self):
        with self.assertRaises(NmapError):
            parse_nmap_version("Nmap version unknown")
        with self.assertRaises(NmapError):
            latest_stable_nmap_tag([{"name": "v7.99beta1"}])

    def test_version_worker_parses_upstream_tags_without_network(self):
        payload = b'[{"name":"v7.99"},{"name":"v7.992"}]'
        worker = NmapVersionCheckWorker()
        results = []
        worker.checked.connect(lambda version, error: results.append((version, error)))

        with patch("nmap_gui.window.urlopen", return_value=FakeResponse(payload)):
            worker.run()

        self.assertEqual(results, [("7.992", "")])


if __name__ == "__main__":
    unittest.main()