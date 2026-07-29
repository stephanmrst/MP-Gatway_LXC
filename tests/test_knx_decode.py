import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
for path in (ROOT, APP):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services import knx
from xknx.dpt import DPTBinary
from xknx.dpt.dpt_14 import DPT4ByteFloat
from xknx.dpt.dpt_9 import DPTTemperature
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


class KnxDecodeTests(unittest.TestCase):
    def test_dpt1_true_decodes_to_int_one(self):
        result = knx.decode_knx_value(GroupValueWrite(DPTBinary(1)), "0/0/1", "1.001")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 1)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "1")
        self.assertEqual(result["raw_value"], "01")
        self.assertEqual(result["value_type"], "integer")

    def test_dpt1_false_decodes_to_int_zero(self):
        result = knx.decode_knx_value(GroupValueWrite(DPTBinary(0)), "0/0/1", "1.001")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 0)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "0")
        self.assertEqual(result["raw_value"], "00")
        self.assertEqual(result["value_type"], "integer")

    def test_dpt1_integer_one_decodes_to_int_one(self):
        result = knx.decode_knx_value(GroupValueWrite(1), "0/0/1", "1.001")

        self.assertEqual(result["value"], 1)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "1")

    def test_dpt1_integer_zero_decodes_to_int_zero_without_raw_fallback(self):
        result = knx.decode_knx_value(GroupValueWrite(0), "0/0/1", "1.001")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 0)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "0")
        self.assertFalse(result["display_value"].startswith("Raw:"))

    def test_unknown_two_byte_payload_is_auto_decoded_without_unit(self):
        result = knx.decode_knx_value(GroupValueWrite(DPTTemperature.to_knx(21.5)), "2/1/5", None)

        self.assertIs(result["decoded"], True)
        self.assertAlmostEqual(float(result["value"]), 21.5, places=2)
        self.assertEqual(result["display_value"], "21.5")
        self.assertEqual(result["raw_value"], "0C33")
        self.assertEqual(result["dpt"], "9.xxx auto")
        self.assertIsNone(result["unit"])

    def test_binary_payload_without_configured_dpt_is_payload_inferred(self):
        result = knx.decode_knx_value(GroupValueWrite(DPTBinary(1)), "0/0/9", None)

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 1)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "1")
        self.assertIsNone(result["dpt"])
        self.assertEqual(result["dpt_source"], "payload_inferred")

    def test_binary_payload_without_configured_dpt_false_is_payload_inferred(self):
        result = knx.decode_knx_value(GroupValueWrite(DPTBinary(0)), "0/0/9", None)

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 0)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "0")
        self.assertEqual(result["raw_value"], "00")
        self.assertIsNone(result["dpt"])
        self.assertEqual(result["dpt_source"], "payload_inferred")

    def test_unknown_dpt_text_does_not_block_binary_payload_inference(self):
        self.assertEqual(knx.normalize_dpt("unbekannt"), "")
        result = knx.decode_knx_value(GroupValueWrite(DPTBinary(1)), "0/0/9", "unbekannt")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["value"], 1)
        self.assertIs(type(result["value"]), int)
        self.assertEqual(result["display_value"], "1")
        self.assertEqual(result["dpt_source"], "payload_inferred")

    def test_dpt1_text_formats_decode_to_integer(self):
        for dpt in ("DPT 1.001", "DPT1.001", "1.1", "1.001 Schalten"):
            with self.subTest(dpt=dpt):
                result = knx.decode_knx_value(GroupValueWrite(DPTBinary(0)), "0/0/9", dpt)
                self.assertIs(result["decoded"], True)
                self.assertEqual(result["value"], 0)
                self.assertIs(type(result["value"]), int)
                self.assertEqual(result["display_value"], "0")
                self.assertEqual(result["dpt"], "1.001")

    def test_group_value_read_has_no_invented_value(self):
        result = knx.decode_knx_value(GroupValueRead(), "0/0/1", "1.001")

        self.assertIs(result["decoded"], True)
        self.assertIsNone(result["value"])
        self.assertEqual(result["display_value"], "Leseanfrage")
        self.assertEqual(result["value_type"], "read")

    def test_dpt9_decoding_still_works(self):
        payload = GroupValueWrite(DPTTemperature.to_knx(21.5))
        result = knx.decode_knx_value(payload, "0/0/2", "9.001")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["display_value"], "21.5")
        self.assertEqual(result["raw_value"], "0C33")

    def test_configured_temperature_and_humidity_addresses_decode_numerically(self):
        temperature = knx.decode_knx_value(
            GroupValueWrite(bytes.fromhex("192F")), "0/2/0", "9.001"
        )
        humidity = knx.decode_knx_value(
            GroupValueWrite(bytes.fromhex("1B1F")), "0/2/1", "9.007"
        )

        self.assertIs(temperature["decoded"], True)
        self.assertAlmostEqual(float(temperature["display_value"]), 24.24, places=2)
        self.assertEqual(temperature["dpt"], "9.001")
        self.assertIs(humidity["decoded"], True)
        self.assertAlmostEqual(float(humidity["display_value"]), 63.92, places=2)
        self.assertEqual(humidity["dpt"], "9.007")

    def test_dpt14_decoding_still_works(self):
        payload = GroupValueWrite(DPT4ByteFloat.to_knx(69.28))
        result = knx.decode_knx_value(payload, "0/0/3", "14.056")

        self.assertIs(result["decoded"], True)
        self.assertEqual(result["display_value"], "69.28")
        self.assertEqual(result["raw_value"], "428A8F5C")

    def test_same_value_updates_receive_count_twice(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        core.add_knx_monitor_entry("0/0/1", "1", "RX", "1.001", telegram_type="GroupValueWrite", apdu="01", decoded=True, display_value="1", raw_value="01", value_data=1)
        first = core.knx_monitor_payload()["last"]["0/0/1"]
        core.add_knx_monitor_entry("0/0/1", "1", "RX", "1.001", telegram_type="GroupValueWrite", apdu="01", decoded=True, display_value="1", raw_value="01", value_data=1)
        second = core.knx_monitor_payload()["last"]["0/0/1"]

        self.assertEqual(first["receive_count"], 1)
        self.assertEqual(second["receive_count"], 2)
        self.assertEqual(second["display_value"], "1")

    def test_monitor_entry_keeps_integer_value_and_display_value(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        core.add_knx_monitor_entry(
            "0/0/9",
            "1",
            "RX",
            "1.001",
            telegram_type="GroupValueWrite",
            apdu="01",
            decoded=True,
            display_value="1",
            raw_value="01",
            value_data=1,
        )
        entry = core.knx_monitor_payload()["last"]["0/0/9"]

        self.assertEqual(entry["value"], 1)
        self.assertIs(type(entry["value"]), int)
        self.assertEqual(entry["display_value"], "1")
        self.assertEqual(entry["raw_value"], "01")
        self.assertIs(entry["decoded"], True)

    def test_parse_dpt1_payload_for_mqtt_uses_one_and_zero(self):
        self.assertEqual(knx.parse_knx_payload_value(GroupValueWrite(DPTBinary(1)), "1.001"), "1")
        self.assertEqual(knx.parse_knx_payload_value(GroupValueWrite(DPTBinary(0)), "1.001"), "0")

    def test_legacy_knx_to_mqtt_publishes_one_and_zero(self):
        class FakeMqtt:
            def __init__(self):
                self.payloads = []

            def publish(self, topic, payload, retain=False):
                self.payloads.append((topic, payload, retain))
                return type("Result", (), {"rc": 0, "mid": 1})()

        logs = []
        fake = FakeMqtt()
        routes = [{"enabled": True, "group_address": "0/0/9", "mqtt_topic": "knx/switch", "dpt": "1.001", "retain": False}]

        knx.publish_knx_to_mqtt("0/0/9", GroupValueWrite(DPTBinary(1)), lambda: routes, lambda: fake, {}, logs.append)
        knx.publish_knx_to_mqtt("0/0/9", GroupValueWrite(DPTBinary(0)), lambda: routes, lambda: fake, {}, logs.append)

        self.assertEqual(fake.payloads[0][1], "1")
        self.assertEqual(fake.payloads[1][1], "0")

    def test_knx_monitor_history_keeps_last_15_events(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        for i in range(20):
            core.add_knx_monitor_entry("0/0/9", str(i), "RX", "1.001", telegram_type="GroupValueWrite", value_data=i, display_value=str(i), raw_value=f"{i:02X}")

        log = core.knx_monitor_payload()["log"]

        self.assertEqual(len(log), 15)
        self.assertEqual([entry["value"] for entry in log], list(range(19, 4, -1)))
        self.assertEqual(len({entry["id"] for entry in log}), 15)

    def test_knx_monitor_history_allows_duplicate_group_address_and_values(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        for value in (1, 0, 1):
            core.add_knx_monitor_entry("0/0/9", str(value), "RX", "1.001", telegram_type="GroupValueWrite", value_data=value, display_value=str(value), raw_value=f"{value:02X}")

        payload = core.knx_monitor_payload()

        self.assertEqual([entry["value"] for entry in payload["log"]], [1, 0, 1])
        self.assertEqual(payload["last"]["0/0/9"]["value"], 1)
        self.assertEqual(len({entry["id"] for entry in payload["log"]}), 3)

    def test_knx_monitor_api_refresh_and_reconnect_keep_history(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        for i in range(3):
            core.add_knx_monitor_entry("1/2/3", str(i), "RX", "1.001", telegram_type="GroupValueWrite", value_data=i, display_value=str(i), raw_value=f"{i:02X}")

        before = [entry["id"] for entry in core.knx_monitor_payload()["log"]]
        after_refresh = [entry["id"] for entry in core.knx_monitor_payload()["log"]]
        core.set_knx_runtime_state(connection_status="starting")
        after_reconnect = [entry["id"] for entry in core.knx_monitor_payload()["log"]]

        self.assertEqual(after_refresh, before)
        self.assertEqual(after_reconnect, before)

    def test_knx_monitor_history_has_no_time_to_live(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        core.add_knx_monitor_entry("1/2/3", "1", "RX", "1.001", telegram_type="GroupValueWrite", value_data=1, display_value="1", raw_value="01", timestamp="2026-07-13T21:00:00")

        before = [entry["id"] for entry in core.knx_monitor_payload()["log"]]
        for state in ("idle", "disconnected", "connected"):
            core.set_knx_runtime_state(connection_status=state)
            self.assertEqual([entry["id"] for entry in core.knx_monitor_payload()["log"]], before)

    def test_knx_monitor_polling_without_new_telegrams_keeps_history(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        for i in range(15):
            core.add_knx_monitor_entry("1/2/3", str(i), "RX", "1.001", telegram_type="GroupValueWrite", value_data=i, display_value=str(i), raw_value=f"{i:02X}")

        before = [entry["id"] for entry in core.knx_monitor_payload()["log"]]
        for _ in range(20):
            payload = core.knx_monitor_payload()
            self.assertEqual([entry["id"] for entry in payload["log"]], before)
            self.assertEqual(len(payload["log"]), 15)

    def test_knx_monitor_payload_is_explicit_snapshot_from_same_history_instance(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        core.add_knx_monitor_entry("1/2/3", "1", "RX", "1.001", telegram_type="GroupValueWrite", value_data=1, display_value="1", raw_value="01")

        payload = core.knx_monitor_payload()
        with core.runtime_context.knx.lock:
            expected_id = id(core.runtime_context.knx.monitor_log)

        self.assertIs(payload["snapshot"], True)
        self.assertEqual(payload["event"], "knx_history_snapshot")
        self.assertEqual(payload["history"], payload["log"])
        self.assertEqual(payload["history_count"], 1)
        self.assertEqual(payload["history_object_id"], expected_id)
        self.assertEqual(payload["history"][0]["value"], 1)

    def test_knx_monitor_live_update_prepends_without_replacing_history(self):
        import app.core as core

        core.clear_knx_monitor_values()
        core.clear_knx_monitor_log()
        for i in range(14):
            core.add_knx_monitor_entry("1/2/3", str(i), "RX", "1.001", telegram_type="GroupValueWrite", value_data=i, display_value=str(i), raw_value=f"{i:02X}")
        previous_ids = [entry["id"] for entry in core.knx_monitor_payload()["log"]]

        core.add_knx_monitor_entry("1/2/3", "14", "RX", "1.001", telegram_type="GroupValueWrite", value_data=14, display_value="14", raw_value="0E")
        log = core.knx_monitor_payload()["log"]

        self.assertEqual(len(log), 15)
        self.assertEqual(log[0]["value"], 14)
        self.assertEqual([entry["id"] for entry in log[1:]], previous_ids)

    def test_frontend_empty_snapshot_only_clears_after_explicit_user_action(self):
        source = (ROOT / "app" / "core.py").read_text(encoding="utf-8-sig")
        function = source.split("function applyKnxSnapshot(data, source) {", 1)[1].split(
            "\nfunction renderLast(data, source) {", 1
        )[0]

        self.assertNotIn("backendCount", function)
        self.assertIn("if (nextLog.length > 0)", function)
        self.assertIn("data.history_cleared === true", function)
        self.assertIn('data.clear_reason === "explicit_user_action"', function)
        self.assertIn("knxHistoryEntries = previousLog;", function)
        self.assertIn("knxHistoryEntries = [];", function)

    def test_frontend_snapshot_keeps_original_latest_group_address_handling(self):
        source = (ROOT / "app" / "core.py").read_text(encoding="utf-8-sig")
        function = source.split("function applyKnxSnapshot(data, source) {", 1)[1].split(
            "\nfunction renderLast(data, source) {", 1
        )[0]

        self.assertIn("const previousLast = knxLatestByGa;", function)
        self.assertIn('if (data.last && typeof data.last === "object")', function)
        self.assertIn("knxLatestByGa = data.last;", function)
        self.assertIn("data.last = previousLast;", function)

    def test_frontend_history_uses_browser_storage_as_resilience_layer(self):
        source = (ROOT / "app" / "core.py").read_text(encoding="utf-8-sig")
        self.assertIn('const KNX_HISTORY_STORAGE_KEY = "mp_gateway_knx_history_v1";', source)
        self.assertIn("let knxHistoryEntries = loadStoredKnxHistory();", source)
        self.assertIn("storeKnxHistory();", source)


if __name__ == "__main__":
    unittest.main()
