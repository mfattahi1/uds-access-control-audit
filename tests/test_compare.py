import unittest

from uds_access_control_audit.compare import compare_reports
from uds_access_control_audit.models import Observation, ScanReport


class CompareReportsTests(unittest.TestCase):
    def test_opened_after_auth(self):
        pre = ScanReport.create(
            "pre",
            "mock",
            [Observation("x", "Probe X", "Service", "NEGATIVE", "SecurityAccessDenied")],
        )
        post = ScanReport.create(
            "post",
            "mock",
            [Observation("x", "Probe X", "Service", "POSITIVE")],
        )
        rows = compare_reports(pre, post)
        self.assertEqual(rows[0].change, "opened_after_auth")

    def test_unchanged(self):
        obs = Observation("x", "Probe X", "Service", "POSITIVE")
        pre = ScanReport.create("pre", "mock", [obs])
        post = ScanReport.create("post", "mock", [obs])
        self.assertEqual(compare_reports(pre, post)[0].change, "unchanged")


if __name__ == "__main__":
    unittest.main()
