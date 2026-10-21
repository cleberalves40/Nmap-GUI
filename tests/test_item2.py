import tempfile
import unittest

from nmap_gui.logic import (
    NmapError,
    NmapHistoryStore,
    compare_nmap_xml,
    parse_nmap_xml,
)


PREVIOUS_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up" />
    <address addr="192.0.2.10" addrtype="ipv4" />
    <hostnames><hostname name="router.example" type="PTR" /></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" />
        <service name="ssh" product="OpenSSH" version="9.0" />
      </port>
    </ports>
  </host>
</nmaprun>
"""

CURRENT_XML = PREVIOUS_XML.replace(
    "</ports>",
    """<port protocol="tcp" portid="443">
        <state state="open" />
        <service name="https" product="nginx" version="1.26" />
      </port></ports>""",
)


class NmapXmlTests(unittest.TestCase):
    def test_parser_returns_host_and_service_fields(self):
        rows = parse_nmap_xml(PREVIOUS_XML)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["host"], "192.0.2.10")
        self.assertEqual(rows[0]["hostname"], "router.example")
        self.assertEqual(rows[0]["service"], "ssh")
        self.assertEqual(rows[0]["version"], "9.0")

    def test_parser_rejects_invalid_or_non_nmap_xml(self):
        for content in ("<nmaprun>", "<root />"):
            with self.subTest(content=content):
                with self.assertRaises(NmapError):
                    parse_nmap_xml(content)

    def test_compare_reports_added_port(self):
        changes = compare_nmap_xml(PREVIOUS_XML, CURRENT_XML)

        added = [change for change in changes if change["change"] == "Porta adicionada"]
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["host"], "192.0.2.10")
        self.assertEqual(added[0]["port"], "443")

    def test_history_persists_and_reloads_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NmapHistoryStore(directory)
            saved = store.save_scan(
                target="192.0.2.10",
                output_format="xml",
                content=PREVIOUS_XML,
                returncode=0,
                command="nmap -sV 192.0.2.10",
            )

            reopened = NmapHistoryStore(directory)
            records = reopened.list_scans()
            loaded, content = reopened.load_scan(saved["id"])

            self.assertEqual(records[0]["id"], saved["id"])
            self.assertEqual(loaded["target"], "192.0.2.10")
            self.assertEqual(content, PREVIOUS_XML)


if __name__ == "__main__":
    unittest.main()