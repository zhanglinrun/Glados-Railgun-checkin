import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

import checkin


class CheckinRetryTests(unittest.TestCase):
    def test_permission_rejections_retry_with_a_limit(self):
        cases = [
            ([-2, 0], checkin.CheckinStatus.SUCCESS, [30]),
            ([-2, -2, 0], checkin.CheckinStatus.SUCCESS, [30, 60]),
            ([-2, 1], checkin.CheckinStatus.REPEAT, [30]),
            ([-2, -2, -2], checkin.CheckinStatus.FAILURE, [30, 60]),
            ([0], checkin.CheckinStatus.SUCCESS, []),
            ([1], checkin.CheckinStatus.REPEAT, []),
            ([None], checkin.CheckinStatus.FAILURE, []),
        ]
        for codes, expected, delays in cases:
            responses = [
                SimpleNamespace(json=lambda code=code: {"code": code})
                if code is not None else None
                for code in codes
            ]
            with self.subTest(codes=codes), checkin.API("glados.cloud") as api, \
                    patch.object(api, "_make_request", side_effect=responses) as request, \
                    patch.object(api, "_log"), patch("checkin.time.sleep") as sleep:
                result = api.checkin("test-cookie")
                self.assertEqual(result["code"], expected)
                self.assertEqual(request.call_count, len(codes))
                self.assertEqual(sleep.call_args_list, [call(delay) for delay in delays])

    def test_device_adaptation_also_recovers_from_a_permission_rejection(self):
        payloads = [
            {"code": 4, "reason": "device-mismatch", "loginDevice": "macOS"},
            {"code": -2},
            {"code": 0},
        ]
        responses = [SimpleNamespace(json=lambda payload=payload: payload) for payload in payloads]
        with checkin.API("glados.cloud") as api, \
                patch.object(api, "_make_request", side_effect=responses) as request, \
                patch.object(api, "_log"), patch("checkin.time.sleep") as sleep:
            result = api.checkin("test-cookie")
            self.assertEqual(result["code"], checkin.CheckinStatus.SUCCESS)
            self.assertEqual(
                [item.kwargs["user_agent"] for item in request.call_args_list],
                [checkin.PLATFORM_UA["Windows"], checkin.PLATFORM_UA["macOS"], checkin.PLATFORM_UA["macOS"]],
            )
            sleep.assert_called_once_with(30)


if __name__ == "__main__":
    unittest.main()
