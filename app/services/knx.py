import asyncio
import re
import threading
import time
from datetime import datetime

import requests


def normalize_knx_ga(value):
    """Normalize KNX group addresses."""
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return ""

    if "/" in text:
        parts = [p for p in text.split("/") if p != ""]
        if len(parts) >= 3:
            return f"{parts[0]}/{parts[1]}/{parts[2]}"
        if len(parts) == 2:
            a, b = parts[0], parts[1]
            b_digits = re.sub(r"\D", "", b)
            if len(b_digits) >= 2:
                return f"{a}/{b_digits[0]}/{b_digits[1:]}"
            return f"{a}/{b}"
        if len(parts) == 1:
            return normalize_knx_ga(parts[0])
        return ""

    digits = re.sub(r"\D", "", text)
    if not digits:
        return text
    if len(digits) == 1:
        return digits
    if len(digits) == 2:
        return f"{digits[0]}/{digits[1]}"
    return f"{digits[0]}/{digits[1]}/{digits[2:]}"


normalize_knx_group_address = normalize_knx_ga


def _normalize_knx_dpt(dpt):
    text = normalize_dpt(dpt)
    if not text:
        return "1.001"
    if text in {"bool", "boolean", "switch"}:
        return "1.001"
    return text


def _normalize_knx_send_dpt(dpt):
    text = normalize_dpt(dpt)
    if not text:
        return ""
    if text in {"bool", "boolean", "switch"}:
        return "1.001"
    return text


def normalize_dpt(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    if text in {"unbekannt", "unknown", "none", "null", "-", "auto"}:
        return ""
    if text in {"bool", "boolean", "switch"}:
        return "1.001"
    text = text.replace("dpt_", "dpt").replace("_", ".")
    match = re.search(r"(\d+)(?:\.(\d+))?", text.replace("dpt", "", 1).strip())
    if not match:
        return text.replace("dpt", "", 1).strip().split(" ", 1)[0].replace(" ", "")
    main = match.group(1)
    sub = match.group(2)
    if sub is None:
        return main
    if len(sub) < 3:
        sub = sub.zfill(3)
    return f"{int(main)}.{sub[:3]}"


def get_dpt_main(dpt):
    normalized = normalize_dpt(dpt)
    if not normalized:
        return None
    try:
        return int(normalized.split(".", 1)[0])
    except Exception:
        return None


def _knx_parse_number(value):
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    return float(text)


def _knx_parse_int(value):
    return int(round(_knx_parse_number(value)))


def _knx_send_value_for_dpt(value, dpt, invert=False):
    dpt = _normalize_knx_dpt(dpt)
    raw = value
    text = str(raw).strip().lower() if isinstance(raw, str) else ""

    if dpt.startswith("1."):
        if isinstance(raw, bool):
            b = raw
        elif isinstance(raw, (int, float)):
            b = float(raw) != 0
        elif text in ["true", "on", "1", "yes", "ja", "open", "auf"]:
            b = True
        elif text in ["false", "off", "0", "no", "nein", "closed", "zu"]:
            b = False
        else:
            b = bool(raw)
        return (not b) if invert else b

    if dpt.startswith("5.001"):
        return max(0.0, min(100.0, float(_knx_parse_number(raw))))

    if dpt.startswith("5."):
        return max(0, min(255, _knx_parse_int(raw)))

    if dpt.startswith("7.") or dpt.startswith("12."):
        return max(0, _knx_parse_int(raw))

    if dpt.startswith("8.") or dpt.startswith("13."):
        return _knx_parse_int(raw)

    if dpt.startswith("9.") or dpt.startswith("14."):
        return float(_knx_parse_number(raw))

    if dpt.startswith("16."):
        return str(raw)

    return raw


def _knx_monitor_value(value, dpt):
    """Return the normalized display value used by the KNX monitor.

    xknx needs Python booleans for DPT 1 internally, while the MP-Gateway UI
    consistently displays binary states as numeric 0/1.
    """
    normalized = _knx_send_value_for_dpt(value, dpt)
    if _normalize_knx_dpt(dpt).startswith("1."):
        return 1 if bool(normalized) else 0
    return normalized


def _knx_send_value_type_for_dpt(dpt, types):
    if dpt.startswith("1."):
        return types["DPTBinary"], "DPTBinary"
    if dpt.startswith("5.001"):
        return types["DPTScaling"], "DPTScaling"
    if dpt.startswith("5."):
        return types["DPTValue1Ucount"], "DPTValue1Ucount"
    if dpt.startswith("7."):
        return types["DPT2ByteUnsigned"], "DPT2ByteUnsigned"
    if dpt.startswith("8."):
        return types["DPT2ByteSigned"], "DPT2ByteSigned"
    if dpt.startswith("9.001"):
        return types.get("DPTTemperature") or types["DPT2ByteFloat"], "DPTTemperature"
    if dpt.startswith("9.004"):
        return types.get("DPTLux") or types["DPT2ByteFloat"], "DPTLux"
    if dpt.startswith("9.005"):
        return types.get("DPTWsp") or types["DPT2ByteFloat"], "DPTWsp"
    if dpt.startswith("9.006"):
        return types.get("DPTPressure2Byte") or types["DPT2ByteFloat"], "DPTPressure2Byte"
    if dpt.startswith("9.007"):
        return types.get("DPTHumidity") or types["DPT2ByteFloat"], "DPTHumidity"
    if dpt.startswith("9."):
        return types["DPT2ByteFloat"], "DPT2ByteFloat"
    if dpt.startswith("12."):
        return types["DPT4ByteUnsigned"], "DPT4ByteUnsigned"
    if dpt.startswith("13."):
        return types["DPT4ByteSigned"], "DPT4ByteSigned"
    if dpt.startswith("14.056"):
        return types.get("DPTPower") or types["DPT4ByteFloat"], "DPTPower"
    if dpt.startswith("14.019"):
        return types.get("DPTElectricCurrent") or types["DPT4ByteFloat"], "DPTElectricCurrent"
    if dpt.startswith("14.027"):
        return types.get("DPTElectricPotential") or types["DPT4ByteFloat"], "DPTElectricPotential"
    if dpt.startswith("14."):
        return types["DPT4ByteFloat"], "DPT4ByteFloat"
    if dpt.startswith("16."):
        return types["DPTString"], "DPTString"
    return None, ""


def _knx_encode_group_value_write_payload(value, dpt, types):
    value_type, method = _knx_send_value_type_for_dpt(dpt, types)
    if value_type is None:
        return None, method
    if dpt.startswith("1."):
        return types["DPTBinary"](1 if bool(value) else 0), method
    return value_type.to_knx(value), method


def _knx_payload_data_bytes(knx_payload):
    payload_value = getattr(knx_payload, "value", None)
    if isinstance(payload_value, (bytes, bytearray)):
        return bytes(payload_value)
    if isinstance(payload_value, (list, tuple)):
        return bytes(int(v) & 0xFF for v in payload_value)
    if payload_value is not None and not isinstance(payload_value, str):
        try:
            return bytes(int(v) & 0xFF for v in payload_value)
        except Exception:
            pass
    if hasattr(knx_payload, "to_knx"):
        try:
            return bytes(knx_payload.to_knx())
        except Exception:
            pass
    if knx_payload.__class__.__name__ == "DPTBinary":
        return bytes([1 if bool(getattr(knx_payload, "value", False)) else 0])
    return b""


def resolve_knx_test_dpt(raw_value, selected_dpt):
    dpt = _normalize_knx_dpt(selected_dpt)
    if dpt != "auto":
        return dpt

    text = str(raw_value or "").strip().lower()
    if not text:
        return "1.001"

    bool_like = {"true", "false", "on", "off", "1", "0", "yes", "no", "ja", "nein", "open", "closed", "auf", "zu"}
    if text in bool_like:
        return "1.001"

    if "%" in text:
        return "5.001"
    if "°c" in text or " c" in text or text.endswith("c") or "temp" in text:
        return "9.001"
    if "w" in text or "watt" in text or "leistung" in text or "power" in text:
        return "14.056"
    if "a" in text or "amp" in text or "strom" in text:
        return "14.019"
    if "v" in text or "volt" in text or "spannung" in text:
        return "14.027"

    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", text):
        return "9.001"

    return "16.001"


def build_knx_send_diagnostic(group_address, dpt, value):
    try:
        from xknx.dpt import DPTBinary
        from xknx.dpt.dpt_5 import DPTScaling, DPTValue1Ucount
        from xknx.dpt.dpt_7 import DPT2ByteUnsigned
        from xknx.dpt.dpt_8 import DPT2ByteSigned
        from xknx.dpt.dpt_9 import DPT2ByteFloat, DPTTemperature, DPTLux, DPTWsp, DPTPressure2Byte, DPTHumidity
        from xknx.dpt.dpt_12 import DPT4ByteUnsigned
        from xknx.dpt.dpt_13 import DPT4ByteSigned
        from xknx.dpt.dpt_14 import DPT4ByteFloat, DPTPower, DPTElectricCurrent, DPTElectricPotential
        from xknx.dpt.dpt_16 import DPTString
        from xknx.telegram import Telegram
        from xknx.telegram.address import parse_device_group_address
        from xknx.telegram.apci import GroupValueWrite
    except Exception as e:
        return {
            "ok": False,
            "error": f"xknx fehlt oder laedt nicht: {e}",
            "telegram_type": "GroupValueWrite",
            "group_address": normalize_knx_ga(group_address),
            "dpt": _normalize_knx_dpt(dpt),
            "raw_value": value,
            "converted_value": value,
            "payload_hex": "",
            "payload_len": 0,
            "apdu": "",
        }

    ga = normalize_knx_ga(group_address)
    dpt = resolve_knx_test_dpt(value, dpt)
    converted_value = _knx_send_value_for_dpt(value, dpt)
    types = locals()
    knx_payload, method = _knx_encode_group_value_write_payload(converted_value, dpt, types)
    if knx_payload is None:
        return {
            "ok": False,
            "error": f"KNX DPT {dpt} wird nicht unterstuetzt",
            "telegram_type": "GroupValueWrite",
            "group_address": ga,
            "dpt": dpt,
            "raw_value": value,
            "converted_value": converted_value,
            "payload_hex": "",
            "payload_len": 0,
            "apdu": "",
        }

    payload_bytes = _knx_payload_data_bytes(knx_payload)
    telegram = Telegram(
        destination_address=parse_device_group_address(ga),
        payload=GroupValueWrite(knx_payload),
    )
    try:
        apdu_hex = bytes(telegram.payload.to_knx()).hex()
    except Exception:
        apdu_hex = ""
    return {
        "ok": True,
        "error": "",
        "telegram_type": "GroupValueWrite",
        "group_address": ga,
        "dpt": dpt,
        "raw_value": value,
        "converted_value": converted_value,
        "method": method,
        "payload_hex": payload_bytes.hex(),
        "payload_len": len(payload_bytes),
        "apdu": apdu_hex,
    }


def convert_knx_value(value, dpt, invert=False):
    return _knx_send_value_for_dpt(value, dpt, invert=invert)


knx_convert_value = convert_knx_value


def infer_knx_dpt(group_address, default="", load_knx2mqtt_config=None, load_knx2lox_config=None, load_mqtt2knx_config=None, load_udp2knx_config=None):
    """Find configured DPT for a KNX group address from all mapping tables."""
    ga_in = normalize_knx_ga(group_address)
    if not ga_in:
        return default

    sources = []
    for loader in [load_knx2mqtt_config, load_knx2lox_config, load_mqtt2knx_config, load_udp2knx_config]:
        if not loader:
            continue
        try:
            sources += loader()
        except Exception:
            pass

    for item in sources:
        if not isinstance(item, dict):
            continue
        ga = normalize_knx_ga(item.get("group_address", ""))
        if ga and ga == ga_in:
            dpt = str(item.get("dpt", "") or "").strip()
            if dpt:
                return dpt
    return default


def payload_to_bytes(payload):
    """Extract raw KNX payload bytes from xknx Telegram payload variants."""
    raw = payload
    try:
        if hasattr(raw, "value"):
            raw = raw.value
        if hasattr(raw, "value"):
            raw = raw.value
    except Exception:
        pass

    if isinstance(raw, (bytes, bytearray)):
        return list(raw)
    if isinstance(raw, (list, tuple)):
        out = []
        for x in raw:
            try:
                out.append(int(x) & 0xFF)
            except Exception:
                pass
        return out

    txt = str(raw)
    nums = re.findall(r"\b\d{1,3}\b", txt)
    vals = []
    for n in nums:
        try:
            v = int(n)
            if 0 <= v <= 255:
                vals.append(v)
        except Exception:
            pass
    return vals


def payload_to_hex(payload):
    data = payload_to_bytes(payload)
    return "".join(f"{int(x) & 0xFF:02X}" for x in data)


def _payload_value(payload):
    raw = payload
    try:
        if hasattr(raw, "value"):
            raw = raw.value
        if hasattr(raw, "value"):
            raw = raw.value
    except Exception:
        pass
    return raw


def _telegram_payload(telegram_or_payload):
    try:
        payload = getattr(telegram_or_payload, "payload", None)
        if payload is not None:
            return payload
    except Exception:
        pass
    return telegram_or_payload


def _telegram_type(payload):
    name = payload.__class__.__name__ if payload is not None else "Telegram"
    return name or "Telegram"


def _short_apdu_small_data(payload):
    """Return KNX small-data bits for short APDUs, if xknx exposes them."""
    try:
        data = payload.to_knx()
        if data is not None and len(data) >= 2:
            return int(data[-1]) & 0x3F
    except Exception:
        pass
    return None


def format_knx_raw_value(telegram_or_payload):
    """Format KNX payload data as stable uppercase hex without Python repr noise."""
    payload = _telegram_payload(telegram_or_payload)
    raw = _payload_value(payload)

    if isinstance(raw, bool):
        return "01" if raw else "00"
    if isinstance(raw, int):
        return f"{raw & 0xFF:02X}"
    if isinstance(raw, float) and raw.is_integer():
        return f"{int(raw) & 0xFF:02X}"

    data = payload_to_bytes(payload)
    if data:
        return "".join(f"{int(x) & 0xFF:02X}" for x in data)

    small_data = _short_apdu_small_data(payload)
    if small_data is not None:
        return f"{small_data & 0x3F:02X}"
    return ""


def _dpt1_boolean_from_payload(payload):
    raw = _payload_value(payload)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(int(raw) & 0x01)
    if isinstance(raw, (bytes, bytearray)) and len(raw) > 0:
        return bool(int(raw[0]) & 0x01)
    if isinstance(raw, (list, tuple)) and len(raw) > 0:
        return bool(int(raw[0]) & 0x01)

    small_data = _short_apdu_small_data(payload)
    if small_data is not None:
        return bool(small_data & 0x01)

    data = payload_to_bytes(payload)
    if data:
        return bool(int(data[-1]) & 0x01)

    txt = str(raw).strip().lower()
    if txt in ["1", "true", "on", "yes", "ein", "open", "auf"]:
        return True
    if txt in ["0", "false", "off", "no", "aus", "closed", "zu"]:
        return False
    return None


def _payload_is_xknx_binary(payload):
    """Detect xknx binary payloads even when wrapped multiple levels deep."""
    current = payload
    for _ in range(5):
        if current is None:
            return False
        if current.__class__.__name__ == "DPTBinary":
            return True
        if isinstance(current, bool):
            return True
        try:
            next_value = getattr(current, "value", None)
        except Exception:
            next_value = None
        if next_value is None or next_value is current:
            break
        current = next_value
    return False


def _payload_is_short_binary(payload):
    """Best-effort detection for KNX 1-bit short APDUs without configured DPT.

    Some xknx versions wrap DPTBinary differently, so class-name detection alone
    is not reliable. A GroupValueWrite/Response carrying small-data 0 or 1 is a
    valid switch telegram and should still reach the Explorer as numeric 0/1.
    """
    if _payload_is_xknx_binary(payload):
        return True

    raw = _payload_value(payload)
    if isinstance(raw, bool):
        return True

    telegram_type = _telegram_type(payload)
    if telegram_type not in {"GroupValueWrite", "GroupValueResponse"}:
        return False

    small_data = _short_apdu_small_data(payload)
    return small_data in (0, 1)


def decode_knx_value(telegram, group_address="", configured_dpt=None, invert=False):
    """Decode one KNX telegram/payload for KNX Explorer and routing consumers."""
    payload = _telegram_payload(telegram)
    telegram_type = _telegram_type(payload)
    dpt = _normalize_knx_send_dpt(configured_dpt) if configured_dpt else ""
    raw_value = format_knx_raw_value(payload)
    source_address = ""
    destination_address = normalize_knx_ga(group_address)
    try:
        source_address = str(getattr(telegram, "source_address", "") or "")
    except Exception:
        source_address = ""
    try:
        destination_address = normalize_knx_ga(getattr(telegram, "destination_address", "") or destination_address)
    except Exception:
        pass

    result = {
        "decoded": False,
        "value": None,
        "display_value": f"Raw: {raw_value}" if raw_value else "Raw",
        "raw_value": raw_value,
        "dpt": dpt or None,
        "unit": None,
        "value_type": "raw",
        "telegram_type": telegram_type,
        "group_address": destination_address or normalize_knx_ga(group_address),
        "source_address": source_address,
    }

    if telegram_type == "GroupValueRead":
        result.update({
            "decoded": True,
            "display_value": "Leseanfrage",
            "value_type": "read",
        })
        return result

    if get_dpt_main(dpt) == 1 or dpt in ["bool", "boolean", "switch"]:
        b = _dpt1_boolean_from_payload(payload)
        if b is not None:
            b = (not b) if invert else b
            normalized_value = 1 if b else 0
            result.update({
                "decoded": True,
                "value": normalized_value,
                "display_value": str(normalized_value),
                "raw_value": "01" if normalized_value else "00",
                "dpt": dpt or "1.001",
                "unit": None,
                "value_type": "integer",
            })
        return result

    if not dpt:
        if _payload_is_short_binary(payload):
            b = _dpt1_boolean_from_payload(payload)
            if b is not None:
                b = (not b) if invert else b
                normalized_value = 1 if b else 0
                result.update({
                    "decoded": True,
                    "value": normalized_value,
                    "display_value": str(normalized_value),
                    "raw_value": "01" if normalized_value else "00",
                    "dpt": "1.001",
                    "dpt_source": "payload_inferred",
                    "unit": None,
                    "value_type": "integer",
                })
            return result

        # The KNX bus does not transport the configured DPT.  For Explorer
        # telegrams without a mapping we still decode the unambiguous wire
        # width, while keeping the DPT explicitly marked as automatic and
        # never inventing a unit.
        data = payload_to_bytes(payload)
        auto_display, auto_dpt = auto_decode_value(data)
        if auto_display not in (None, "") and auto_dpt:
            native_value = auto_display
            value_type = "text"
            if auto_dpt.startswith(("5.", "9.", "14.")):
                try:
                    native_value = float(auto_display)
                    if auto_dpt.startswith("5.") and native_value.is_integer():
                        native_value = int(native_value)
                        value_type = "integer"
                    else:
                        value_type = "number"
                except (TypeError, ValueError):
                    native_value = auto_display
            result.update({
                "decoded": True,
                "value": native_value,
                "display_value": str(auto_display),
                "dpt": auto_dpt,
                "dpt_source": "payload_length_inferred",
                "unit": None,
                "value_type": value_type,
            })
        return result

    try:
        display = parse_knx_payload_value(payload, dpt, invert=invert)
        if display is not None and display != "":
            value_type = "number" if dpt.startswith(("5.", "6.", "7.", "8.", "9.", "12.", "13.", "14.", "17.", "18.", "20.")) else "text"
            native_value = display
            if value_type == "number":
                try:
                    number = float(display)
                    if dpt.startswith(("5.", "6.", "7.", "8.", "12.", "13.", "17.", "18.", "20.")) and number.is_integer():
                        native_value = int(number)
                        value_type = "integer"
                    else:
                        native_value = number
                except (TypeError, ValueError):
                    native_value = display
                    value_type = "text"
            result.update({
                "decoded": True,
                "value": native_value,
                "display_value": str(display),
                "dpt": dpt,
                "unit": _dpt_unit(dpt),
                "value_type": value_type,
            })
    except Exception:
        pass

    return result


def _dpt_unit(dpt):
    dpt = normalize_dpt(dpt)
    return {
        "5.001": "%",
        "5.003": "°",
        "5.004": "%",
        "9.001": "°C",
        "9.004": "lx",
        "9.005": "m/s",
        "9.006": "Pa",
        "9.007": "%",
        "14.019": "A",
        "14.027": "V",
        "14.056": "W",
    }.get(dpt)


def _decode_knx_dpt9_float(data):
    """Decode KNX DPT 9.xxx 2-byte float (EIS5)."""
    if len(data) < 2:
        return None
    b1, b2 = int(data[-2]) & 0xFF, int(data[-1]) & 0xFF
    raw = (b1 << 8) | b2
    sign = -1 if (raw & 0x8000) else 1
    exponent = (raw >> 11) & 0x0F
    mantissa = raw & 0x07FF
    if sign < 0:
        mantissa = -(~(mantissa - 1) & 0x07FF)
    return 0.01 * mantissa * (2 ** exponent)


def _decode_knx_dpt14_float(data):
    """Decode KNX DPT 14.xxx 4-byte IEEE float."""
    if len(data) < 4:
        return None
    import struct
    return struct.unpack(">f", bytes(data[-4:]))[0]


def auto_decode_value(data):
    """Best-effort decode for KNX monitor when no mapping/DPT exists yet."""
    if not data:
        return "", ""

    if len(data) == 2:
        val = _decode_knx_dpt9_float(data)
        if val is not None and -273.15 <= float(val) <= 100000:
            return _format_knx_number(val), "9.xxx auto"

    if len(data) == 4:
        val = _decode_knx_dpt14_float(data)
        if val is not None and abs(float(val)) < 1e12:
            return _format_knx_number(val), "14.xxx auto"

    if len(data) == 1:
        return str(data[-1]), "5.xxx auto"

    return "0x" + "".join(f"{x:02X}" for x in data), ""


def _format_knx_number(value):
    try:
        v = float(value)
        txt = f"{v:.3f}".rstrip("0").rstrip(".")
        return txt if txt != "-0" else "0"
    except Exception:
        return str(value)


def parse_knx_payload_value(payload, dpt="1.001", invert=False):
    dpt = str(dpt or "").strip().lower()
    raw = payload

    try:
        if hasattr(raw, "value"):
            raw = raw.value
        if hasattr(raw, "value"):
            raw = raw.value
    except Exception:
        pass

    data = payload_to_bytes(payload)

    if dpt.startswith("1.") or dpt in ["bool", "boolean", "switch"]:
        try:
            if isinstance(raw, (bytes, bytearray)):
                b = bool(raw[-1] & 0x01)
            elif isinstance(raw, (list, tuple)):
                b = bool(int(raw[-1]) & 0x01)
            elif isinstance(raw, bool):
                b = raw
            elif isinstance(raw, (int, float)):
                b = bool(int(raw) & 0x01)
            elif data:
                b = bool(data[-1] & 0x01)
            else:
                txt = str(raw).strip().lower()
                b = txt in ["1", "true", "on", "yes", "ein", "open", "auf"]
            b = (not b) if invert else b
            return "1" if b else "0"
        except Exception:
            return str(raw)

    if dpt.startswith("5."):
        if data:
            val = data[-1]
            if dpt.startswith("5.001"):
                return _format_knx_number(val * 100.0 / 255.0)
            return str(val)

    if dpt.startswith("7.") and len(data) >= 2:
        return str((data[-2] << 8) | data[-1])

    if dpt.startswith("8.") and len(data) >= 2:
        val = (data[-2] << 8) | data[-1]
        if val & 0x8000:
            val -= 0x10000
        return str(val)

    if dpt.startswith("12.") and len(data) >= 4:
        return str(int.from_bytes(bytes(data[-4:]), "big", signed=False))

    if dpt.startswith("13.") and len(data) >= 4:
        return str(int.from_bytes(bytes(data[-4:]), "big", signed=True))

    if dpt.startswith("9.") or dpt in ["eis5", "analog", "float2"]:
        val = _decode_knx_dpt9_float(data)
        if val is not None:
            return _format_knx_number(val)

    if dpt.startswith("14."):
        val = _decode_knx_dpt14_float(data)
        if val is not None:
            return _format_knx_number(val)

    try:
        if isinstance(raw, (int, float, bool)):
            return str(raw)
        if data:
            auto_value, _auto_dpt = auto_decode_value(data)
            if auto_value:
                return auto_value
    except Exception:
        pass
    return str(raw)


format_knx_value_for_mqtt = parse_knx_payload_value
_knx_payload_to_bytes = payload_to_bytes
_knx_auto_decode_value = auto_decode_value
_knx_payload_to_text = parse_knx_payload_value


def build_knx_mqtt_topic(item):
    return str((item or {}).get("mqtt_topic", "") or "").strip()


def build_knx_udp_payload(value):
    return str(value)


def _load_core_runtime_api():
    try:
        from app import core as core_module
        return core_module
    except Exception:
        return None


def _log_core_runtime_identity(core_api, add_log_entry, prefix):
    try:
        module_name = getattr(core_api, "__name__", "<unknown>")
        module_file = getattr(core_api, "__file__", "<unknown>")
        knx_state = getattr(getattr(core_api, "runtime_context", None), "knx", None)
        add_log_entry(
            f"{prefix} core module={module_name} file={module_file} knx_state_id={id(knx_state)}"
        )
    except Exception:
        pass


def _knx_runtime_ready(state):
    return bool(
        state.get("listener_running")
        and state.get("connection_status") == "connected"
        and state.get("xknx")
        and state.get("loop")
    )


def _knx_runtime_state_text(state):
    mode = str(state.get("connection_mode") or "-")
    gateway_ip = str(state.get("gateway_ip") or "-")
    gateway_port = str(state.get("gateway_port") or "-")
    local_ip = str(state.get("local_ip") or "-")
    status = str(state.get("connection_status") or "-")
    last_error = str(state.get("last_error") or "").strip()
    return (
        f"status={status} mode={mode} gateway={gateway_ip}:{gateway_port} "
        f"local_ip={local_ip} last_error={last_error or '-'}"
    )


def _log_knx_send_prepared(group_address, dpt, value, add_log_entry):
    diagnostic = build_knx_send_diagnostic(group_address, dpt, value)
    if diagnostic.get("ok"):
        add_log_entry(
            "KNX TX prepared "
            f"ga={diagnostic.get('group_address') or group_address} "
            f"dpt={diagnostic.get('dpt') or dpt} "
            f"raw={value} "
            f"normalized={diagnostic.get('converted_value')} "
            f"payload_len={diagnostic.get('payload_len')} "
            f"payload_hex={diagnostic.get('payload_hex') or '-'} "
            f"method=group_value_write encoder={diagnostic.get('method') or '-'}"
        )
    else:
        add_log_entry(
            "KNX TX prepare failed "
            f"ga={group_address} dpt={dpt} raw={value} error={diagnostic.get('error') or '-'}"
        )
    return diagnostic


async def _send_knx_runtime(group_address, dpt, value, xknx, add_log_entry, add_monitor_entry=None):
    try:
        from xknx.dpt import DPTBinary
        from xknx.dpt.dpt_5 import DPTScaling, DPTValue1Ucount
        from xknx.dpt.dpt_7 import DPT2ByteUnsigned
        from xknx.dpt.dpt_8 import DPT2ByteSigned
        from xknx.dpt.dpt_9 import DPT2ByteFloat, DPTTemperature, DPTLux, DPTWsp, DPTPressure2Byte, DPTHumidity
        from xknx.dpt.dpt_12 import DPT4ByteUnsigned
        from xknx.dpt.dpt_13 import DPT4ByteSigned
        from xknx.dpt.dpt_14 import DPT4ByteFloat, DPTPower, DPTElectricCurrent, DPTElectricPotential
        from xknx.dpt.dpt_16 import DPTString
        from xknx.telegram import Telegram
        from xknx.telegram.address import parse_device_group_address
        from xknx.telegram.apci import GroupValueWrite
    except Exception as e:
        add_log_entry(f"KNX Fehler: xknx fehlt oder laedt nicht ({e})")
        add_log_entry("KNX Hinweis: pip install xknx")
        return False
    dpt = _normalize_knx_send_dpt(dpt)
    if not dpt:
        add_log_entry(f"KNX send skipped: missing DPT for GA {group_address}")
        if add_monitor_entry:
            add_monitor_entry(group_address, value, "OUT", "", status="ERROR", update_live=False, source="Objektmanager")
        return False
    converted_value = _knx_send_value_for_dpt(value, dpt)
    types = locals()
    knx_payload, encoder = _knx_encode_group_value_write_payload(converted_value, dpt, types)
    if knx_payload is None:
        add_log_entry(f"KNX DPT {dpt} wird nicht unterstuetzt")
        if add_monitor_entry:
            add_monitor_entry(group_address, value, "OUT", dpt, status="ERROR", update_live=False, source="Objektmanager")
        return False
    payload_bytes = _knx_payload_data_bytes(knx_payload)
    try:
        add_log_entry(
            f"KNX TX ga={group_address} dpt={dpt} raw={value} normalized={converted_value} payload_len={len(payload_bytes)} payload_hex={payload_bytes.hex() or '-'} method=group_value_write encoder={encoder}"
        )
        telegram = Telegram(
            destination_address=parse_device_group_address(group_address),
            payload=GroupValueWrite(knx_payload),
        )
        try:
            apdu_hex = bytes(telegram.payload.to_knx()).hex()
        except Exception:
            apdu_hex = ""
        add_log_entry(
            f"KNX Senden Diagnose telegram_type=GroupValueWrite ga={group_address} dpt={dpt} value={converted_value} encoder={encoder} payload_len={len(payload_bytes)} payload_hex={payload_bytes.hex() or '-'} apdu={apdu_hex or '-'}"
        )
        xknx.telegrams.put_nowait(telegram)
        add_log_entry(f"KNX Senden Diagnose queued GroupValueWrite ga={group_address} dpt={dpt}")
        await asyncio.wait_for(xknx.join(), timeout=5)
        add_log_entry(f"KNX Senden Diagnose after join ga={group_address} dpt={dpt}")
        if add_monitor_entry:
            add_monitor_entry(group_address, _knx_monitor_value(converted_value, dpt), "OUT", dpt, status="OK", update_live=False, source="Objektmanager")
        add_log_entry(f"KNX Senden OK ga={group_address} dpt={dpt} value={converted_value}")
        return True
    except Exception as e:
        add_log_entry(f"KNX Senden Fehler konkret: {type(e).__name__}: {e}")
        if dpt.startswith("14."):
            add_log_entry("KNX Hinweis: einige Ziele erwarten fuer Leistung/Temp. eher DPT 9.xxx statt 14.xxx")
        if add_monitor_entry:
            add_monitor_entry(group_address, value, "OUT", dpt, status="ERROR", update_live=False, source="Objektmanager")
        return False


def send_knx_value(group_address, dpt, value, load_knx_config, add_log_entry, add_monitor_entry=None):
    group_address = normalize_knx_ga(group_address)
    send_dpt = _normalize_knx_send_dpt(dpt)
    knx_cfg = load_knx_config()
    if not knx_cfg.get("enabled", False):
        add_log_entry("KNX deaktiviert - Wert nicht gesendet")
        return False
    if not group_address:
        add_log_entry("KNX Fehler: Gruppenadresse fehlt")
        return False
    if not send_dpt:
        add_log_entry(f"KNX send skipped: missing DPT for GA {group_address}")
        if add_monitor_entry:
            add_monitor_entry(group_address, value, "OUT", "", status="ERROR", update_live=False, source="Objektmanager")
        return False
    core_api = _load_core_runtime_api()
    if core_api is None:
        add_log_entry("KNX Senden fehlgeschlagen: Runtime-Service nicht geladen")
        return False
    _log_core_runtime_identity(core_api, add_log_entry, "KNX SEND")
    diagnostic = _log_knx_send_prepared(group_address, send_dpt, value, add_log_entry)
    if not diagnostic.get("ok"):
        if add_monitor_entry:
            add_monitor_entry(group_address, value, "OUT", send_dpt, status="ERROR", update_live=False, source="Objektmanager")
        return False
    # Do not create a visible PENDING monitor row here.
    # The KNX monitor records exactly one final result per send attempt:
    # OK after successful transmission or ERROR if the attempt fails.
    state = {}
    try:
        state = core_api.get_knx_runtime_state()
    except Exception:
        state = {}

    if not _knx_runtime_ready(state):
        try:
            core_api.ensure_knx_listener_started("KNX Senden")
        except Exception:
            pass
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                state = core_api.get_knx_runtime_state()
            except Exception:
                state = {}
            if _knx_runtime_ready(state):
                break
            time.sleep(0.2)

    if not _knx_runtime_ready(state):
        add_log_entry(
            "KNX Senden fehlgeschlagen: keine aktive KNX Tunnel-Verbindung "
            f"({_knx_runtime_state_text(state)})"
        )
        if add_monitor_entry:
            add_monitor_entry(
                group_address,
                _knx_monitor_value(diagnostic.get("converted_value", value), send_dpt),
                "OUT",
                send_dpt,
                status="ERROR",
                update_live=False,
                source="Objektmanager",
            )
        return False

    xknx = state.get("xknx")
    try:
        future = core_api.submit_knx_runtime_coro(
            _send_knx_runtime(group_address, send_dpt, value, xknx, add_log_entry, add_monitor_entry)
        )
        if future is None:
            if add_monitor_entry:
                add_monitor_entry(
                    group_address,
                    _knx_monitor_value(diagnostic.get("converted_value", value), send_dpt),
                    "OUT",
                    send_dpt,
                    status="ERROR",
                    update_live=False,
                    source="Objektmanager",
                )
            add_log_entry("KNX Senden fehlgeschlagen: keine aktive KNX Tunnel-Verbindung")
            return False
        result = future.result(timeout=10)
        return bool(result)
    except Exception as e:
        if add_monitor_entry:
            add_monitor_entry(
                group_address,
                _knx_monitor_value(diagnostic.get("converted_value", value), send_dpt),
                "OUT",
                send_dpt,
                status="ERROR",
                update_live=False,
                source="Objektmanager",
            )
        add_log_entry(f"KNX Senden fehlgeschlagen: {e}")
        return False


def handle_mqtt_to_knx(topic, payload, load_mqtt2knx_config, extract_mqtt_mapping_value, mqtt2knx_last_seen, send_value, add_log_entry, update_last_seen=None):
    for item in load_mqtt2knx_config():
        if not item.get("enabled", True):
            continue
        source_topic = item.get("source_topic", "").strip()
        if not source_topic or topic != source_topic:
            continue
        raw_value = extract_mqtt_mapping_value(item, payload)
        mqtt2knx_last_seen[source_topic] = {
            "value": raw_value if raw_value is not None else "-",
            "raw_payload": payload,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        if update_last_seen:
            update_last_seen("mqtt2knx", source_topic, mqtt2knx_last_seen[source_topic])
        if raw_value is None:
            add_log_entry(f"MQTT2KNX kein gueltiger Wert fuer {topic}")
            return True
        try:
            dpt = str(item.get("dpt", "") or "").strip()
            if not dpt:
                add_log_entry(f"KNX send skipped: missing DPT for GA {item.get('group_address', '')}")
                continue
            add_log_entry(
                f"MQTT2KNX TX route topic={topic} ga={item.get('group_address', '')} dpt={dpt} raw={raw_value}"
            )
            knx_value = convert_knx_value(raw_value, dpt, bool(item.get("invert", False)))
        except Exception as e:
            add_log_entry(f"MQTT2KNX Wertfehler {topic}: {e}")
            return True
        send_value(item.get("group_address", "").strip(), dpt, knx_value)
        return True
    return False


def publish_knx_to_mqtt(group_address, payload_raw, load_knx2mqtt_config, mqtt_client_getter, knx2mqtt_last_seen, add_log_entry, update_last_seen=None, received_perf=None, received_wall=None):
    start_perf = time.perf_counter()
    for item in load_knx2mqtt_config():
        if not item.get("enabled", True):
            continue
        ga = normalize_knx_ga(item.get("group_address", ""))
        mqtt_topic = build_knx_mqtt_topic(item)
        if not ga or not mqtt_topic or ga != normalize_knx_ga(group_address):
            continue
        try:
            value = parse_knx_payload_value(payload_raw, item.get("dpt", "1.001"), bool(item.get("invert", False)))
            knx2mqtt_last_seen[ga] = {"value": value, "time": datetime.now().strftime("%H:%M:%S"), "topic": mqtt_topic}
            if update_last_seen:
                update_last_seen("knx2mqtt", ga, knx2mqtt_last_seen[ga])
            mqtt_client = mqtt_client_getter() if mqtt_client_getter else None
            if mqtt_client:
                result = mqtt_client.publish(mqtt_topic, value, retain=bool(item.get("retain", True)))
                rc = getattr(result, "rc", "")
                mid = getattr(result, "mid", "")
                add_log_entry(f"MQTT PUBLISH topic={mqtt_topic} rc={rc} mid={mid}")
                if received_perf is not None:
                    add_log_entry(f"KNX PERF MQTT_PUBLISH ga={ga} topic={mqtt_topic} total_ms={(time.perf_counter() - float(received_perf)) * 1000:.2f}")
                if received_wall is not None:
                    add_log_entry(f"KNX TO MQTT ga={ga} topic={mqtt_topic} delay_ms={(time.time() - float(received_wall)) * 1000:.2f}")
                add_log_entry(f"KNX2MQTT -> {ga} => {mqtt_topic} = {value}")
            else:
                add_log_entry("KNX2MQTT Fehler: MQTT Client nicht bereit")
        except Exception as e:
            add_log_entry(f"KNX2MQTT Fehler {group_address}: {e}")
    if received_perf is not None:
        add_log_entry(f"KNX PERF KNX2MQTT_DONE ga={normalize_knx_ga(group_address)} step_ms={(time.perf_counter() - start_perf) * 1000:.2f} total_ms={(time.perf_counter() - float(received_perf)) * 1000:.2f}")


def publish_knx_to_loxone(group_address, payload_raw, load_knx2lox_config, load_config, knx2lox_last_seen, add_log_entry, requests_module=requests, update_last_seen=None):
    """Direct KNX telegram to Loxone virtual input/control."""
    ga_in = normalize_knx_ga(group_address)
    for item in load_knx2lox_config():
        if not item.get("enabled", True):
            continue
        ga = normalize_knx_ga(item.get("group_address", ""))
        loxone_io = str(item.get("loxone_io", "")).strip()
        if not ga or not loxone_io or ga != ga_in:
            continue
        try:
            value = parse_knx_payload_value(payload_raw, item.get("dpt", "1.001"), bool(item.get("invert", False)))
            knx2lox_last_seen[ga] = {"value": value, "time": datetime.now().strftime("%H:%M:%S"), "loxone_io": loxone_io}
            if update_last_seen:
                update_last_seen("knx2lox", ga, knx2lox_last_seen[ga])
            cfg = load_config()
            url = f"http://{cfg['loxone']['host']}/dev/sps/io/{loxone_io}/{value}"
            r = requests_module.get(url, auth=(cfg["loxone"]["user"], cfg["loxone"]["password"]), timeout=5)
            if r.status_code == 200:
                add_log_entry(f"KNX2LOX -> {ga} => {loxone_io} = {value}")
            else:
                add_log_entry(f"KNX2LOX Fehler HTTP {r.status_code}: {r.text}")
        except Exception as e:
            add_log_entry(f"KNX2LOX Fehler {ga_in}: {e}")


def handle_udp_to_knx(topic, value, load_udp2knx_config, udp2knx_last_seen, send_value, add_log_entry):
    """Direct UDP input topic/value to KNX mapping."""
    source_topic = str(topic or "").strip()
    if not source_topic:
        return False
    for item in load_udp2knx_config():
        if not item.get("enabled", True):
            continue
        mapped_topic = str(item.get("source_topic", "")).strip()
        if not mapped_topic or mapped_topic != source_topic:
            continue
        udp2knx_last_seen[mapped_topic] = {"value": value, "time": datetime.now().strftime("%H:%M:%S")}
        try:
            dpt = str(item.get("dpt", "") or "").strip()
            if not dpt:
                add_log_entry(f"KNX send skipped: missing DPT for GA {item.get('group_address', '')}")
                continue
            add_log_entry(
                f"UDP2KNX TX route topic={mapped_topic} ga={item.get('group_address', '')} dpt={dpt} raw={value}"
            )
            knx_value = convert_knx_value(value, dpt, bool(item.get("invert", False)))
            send_value(item.get("group_address", ""), dpt, knx_value)
            add_log_entry(f"UDP2KNX -> {mapped_topic} => {item.get('group_address','')} = {knx_value}")
        except Exception as e:
            add_log_entry(f"UDP2KNX Fehler {mapped_topic}: {e}")
        return True
    return False
