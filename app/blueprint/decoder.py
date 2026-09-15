import base64
import json
import zlib


def decode(value: str) -> dict:
    if not value or value[0] != "0":
        raise ValueError("Blueprint string must start with version prefix 0")
    try:
        return json.loads(zlib.decompress(base64.b64decode(value[1:])).decode("utf-8"))
    except (ValueError, zlib.error, json.JSONDecodeError) as error:
        raise ValueError("Invalid Factorio blueprint string") from error