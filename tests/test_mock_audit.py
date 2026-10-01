import unittest

from uds_access_control_audit.catalog import default_catalog
from uds_access_control_audit.compare import compare_reports
from uds_access_control_audit.runner import run_scan
from uds_access_control_audit.transports import MockTransport


class MockAuditTests(unittest.TestCase):
    def test_mock_audit_has_two_opened_probes(self):
        transport = MockTransport()
        with transport:
            pre = run_scan(transport, default_catalog(), "pre")
            post = run_scan(transport, default_catalog(), "post")

        rows = compare_reports(pre, post)
        opened = [row for row in rows if row.change == "opened_after_auth"]
        self.assertEqual(len(opened), 2)
        self.assertEqual(rows[0].change, "unchanged")


if __name__ == "__main__":
    unittest.main()
