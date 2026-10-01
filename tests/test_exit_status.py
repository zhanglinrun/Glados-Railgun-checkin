import unittest
from types import SimpleNamespace
from unittest.mock import DEFAULT, patch

import checkin


class ExitStatusTests(unittest.TestCase):
    def test_business_results_control_exit_status(self):
        cases = [
            ([checkin.CheckinStatus.SUCCESS], 0),
            ([checkin.CheckinStatus.REPEAT], 0),
            ([checkin.CheckinStatus.FAILURE], 1),
            ([checkin.CheckinStatus.SUCCESS, checkin.CheckinStatus.FAILURE], 1),
            ([], 1),
        ]
        for codes, expected in cases:
            with self.subTest(codes=codes), patch.multiple(
                checkin, Config=DEFAULT, Checker=DEFAULT,
                PushService=DEFAULT, logger=DEFAULT,
            ) as mocks:
                mocks["Config"].return_value.cookies_list = ["test-cookie"]
                checker = mocks["Checker"].return_value
                checker.results = [SimpleNamespace(code=code) for code in codes]
                checker.format_results.return_value = ("title", "content", "log")
                self.assertEqual(checkin.main(), expected)

    def test_missing_cookie_fails_without_attempting_checkin(self):
        with patch.multiple(
            checkin, Config=DEFAULT, Checker=DEFAULT,
            PushService=DEFAULT, logger=DEFAULT,
        ) as mocks:
            mocks["Config"].return_value.cookies_list = []
            self.assertEqual(checkin.main(), 1)
            mocks["Checker"].assert_not_called()

    def test_configuration_error_fails_without_sending_push(self):
        with patch.multiple(
            checkin, Config=DEFAULT, PushService=DEFAULT, logger=DEFAULT,
        ) as mocks:
            mocks["Config"].side_effect = ValueError("invalid configuration")
            self.assertEqual(checkin.main(), 1)
            mocks["PushService"].assert_not_called()

    def test_checkin_exception_fails(self):
        with patch.multiple(
            checkin, Config=DEFAULT, Checker=DEFAULT,
            PushService=DEFAULT, logger=DEFAULT,
        ) as mocks:
            mocks["Config"].return_value.cookies_list = ["test-cookie"]
            mocks["Checker"].return_value.checkin_all.side_effect = RuntimeError("request failed")
            self.assertEqual(checkin.main(), 1)


if __name__ == "__main__":
    unittest.main()
