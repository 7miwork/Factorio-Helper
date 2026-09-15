import base64
import json
import zlib


def encode(blueprint: dict) -> str:
    payload = json.dumps(blueprint, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "0" + base64.b64encode(zlib.compress(payload, level=9)).decode("ascii")