"""Small regression checks for the evidence validation and broker settings."""

import unittest
from pathlib import Path

from demo import configured_cap
from mqtt_pilot import validation_errors


ROOT = Path(__file__).resolve().parents[1]


def result(cap):
    run_id = "test"
    payloads = [f"{run_id}-durable-{index}" for index in range(5)]
    received = payloads if cap >= 5 else payloads[:cap]
    return {
        "run_id": run_id,
        "queue_cap_configured": cap,
        "normal_delivery": {"pass": True},
        "cases": [
            {
                "subscriber_count": 3,
                "published_per_subscriber": 5,
                "session_present_on_reconnect": [False] * 3,
                "received_per_subscriber": [0] * 3,
            },
            {
                "session_present_on_reconnect": [True] * 3,
                "received_per_subscriber": [len(received)] * 3,
                "received_payloads_per_subscriber": [received] * 3,
                "exact_payloads_received": [received == payloads] * 3,
            },
        ],
    }


class PilotValidationTests(unittest.TestCase):
    def test_expected_baseline_and_capped_outcomes(self):
        self.assertEqual(validation_errors(result(1000)), [])
        self.assertEqual(validation_errors(result(3)), [])

    def test_rejects_wrong_delivery_count(self):
        evidence = result(3)
        evidence["cases"][1]["received_per_subscriber"][0] = 2
        self.assertIn("Durable delivery", " ".join(validation_errors(evidence)))

    def test_rejects_repeated_payload(self):
        evidence = result(3)
        evidence["cases"][1]["received_payloads_per_subscriber"][0] = ["test-durable-0"] * 3
        self.assertIn("repeated", " ".join(validation_errors(evidence)))

    def test_rejects_surviving_clean_session(self):
        evidence = result(1000)
        evidence["cases"][0]["session_present_on_reconnect"][0] = True
        self.assertIn("Clean sessions", " ".join(validation_errors(evidence)))

    def test_broker_configs_are_the_declared_comparison(self):
        self.assertEqual(configured_cap(ROOT / "mosquitto.baseline.conf"), 1000)
        self.assertEqual(configured_cap(ROOT / "mosquitto.capped.conf"), 3)


if __name__ == "__main__":
    unittest.main()
