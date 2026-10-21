import subprocess
import sys
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QCoreApplication

from nmap_gui.logic import NmapError, NmapLogic
from nmap_gui.window import ScanWorker


class FakeNmapLogic:
    def __init__(self, script):
        self.script = script

    def create_process(self, **kwargs):
        return subprocess.Popen(
            [sys.executable, "-c", self.script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )


class RoadmapItemOneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QCoreApplication.instance() or QCoreApplication([])

    def test_extra_arguments_preserve_quoted_values(self):
        logic = NmapLogic()
        logic.nmap_path = "nmap"

        command = logic.build_command(
            target="127.0.0.1",
            extra_args='--script-args "user=Jane Doe"',
        )

        self.assertIn("user=Jane Doe", command)

    def test_unclosed_extra_argument_quote_is_rejected(self):
        logic = NmapLogic()
        logic.nmap_path = "nmap"

        with self.assertRaisesRegex(NmapError, "Argumentos extras inválidos"):
            logic.build_command(target="127.0.0.1", extra_args='--script-args "open')

    def test_synchronous_scan_timeout_is_reported(self):
        logic = NmapLogic()
        logic.nmap_path = "nmap"

        with patch(
            "nmap_gui.logic.subprocess.run",
            side_effect=subprocess.TimeoutExpired("nmap", 1),
        ):
            with self.assertRaisesRegex(NmapError, "excedeu o tempo limite"):
                logic.run_scan(target="127.0.0.1", timeout=1)

    def test_worker_drains_both_streams_and_keeps_xml_raw(self):
        script = (
            "import sys; "
            "print('<nmaprun><runstats /></nmaprun>'); "
            "print('warning', file=sys.stderr)"
        )
        worker = ScanWorker(FakeNmapLogic(script), output_format="xml")
        output = []
        worker.line_received.connect(output.append)

        worker.run()
        self.application.processEvents()

        self.assertEqual(worker.xml_output, "<nmaprun><runstats /></nmaprun>\n")
        self.assertTrue(any("[STDERR] warning" in line for line in output))

    def test_worker_does_not_expose_malformed_xml(self):
        worker = ScanWorker(
            FakeNmapLogic("print('<nmaprun>incomplete')"), output_format="xml"
        )

        worker.run()

        self.assertIsNone(worker.xml_output)

    def test_worker_timeout_terminates_process(self):
        worker = ScanWorker(
            FakeNmapLogic("import time; time.sleep(10)"), timeout=0.1
        )
        errors = []
        worker.error.connect(errors.append)

        worker.run()

        self.assertTrue(any("excedeu o tempo limite" in error for error in errors))
        self.assertIsNotNone(worker.process.poll())


if __name__ == "__main__":
    unittest.main()