"""Lua-Data-Stage-Parser.

Factorio und Mods definieren ihre Prototypen in Lua-Dateien (data-stage), z. B.
ueber `data:extend{ {...}, {...} }`. Dieser Parser ist ein TOLERANTER
Teilmengen-Parser: Er liest nur die fuer die Knowledge Base relevanten Daten
(Prototyp-Name, -Typ, Icon) und ignoriert sonstige Lua-Expressions. Er ersetzt
kein Lua – er soll reale Installationsdaten ohne Lupa/lua-Praefix auslesen.
"""
from __future__ import annotations

import ast
from pathlib import Path

from app.knowledge.entities import Prototype


# ------------------------------------------------------------------------ #
# Lexer-Hilfsfunktionen (zeichenweise, string-/comment-bewusst)
# ------------------------------------------------------------------------ #
def _find_extend_contents(text: str):
    """Liefert die Inhalte aller `data:extend{ ... }`-Blöcke (ohne Klammern)."""
    results = []
    search_from = 0
    while True:
        start = text.find("extend", search_from)
        if start == -1:
            break
        # Nach "extend" darf nur Whitespace folgen, bis "{".
        cursor = text.find("{", start)
        if cursor == -1 or any(c not in " \t\n\r" for c in text[start + 6:cursor]):
            search_from = start + 6
            continue
        content, end = _capture_braces(text, cursor)
        if content is None:
            break
        results.append(content)
        search_from = end
    return results


def _capture_braces(text: str, open_index: int):
    """Gibt (innerer_content, end_index) fuer einen {…}-Block zurück."""
    depth = 0
    index = open_index
    size = len(text)
    in_str = None
    while index < size:
        char = text[index]
        if in_str:
            if char == "\\":
                index += 2
                continue
            if char == in_str:
                in_str = None
        else:
            if char in ('"', "'"):
                in_str = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[open_index + 1:index], index + 1
        index += 1
    return None, -1


def _split_top_level(content: str) -> list:
    """Teilt einen Tabellen-Inhalt an Topelement-Kommata (string-bewusst)."""
    parts = []
    start = 0
    depth = 0
    in_str = None
    index = 0
    size = len(content)
    while index < size:
        char = content[index]
        if in_str:
            if char == "\\":
                index += 2
                continue
            if char == in_str:
                in_str = None
        else:
            if char in ('"', "'"):
                in_str = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(content[start:index])
                start = index + 1
        index += 1
    if content[start:].strip():
        parts.append(content[start:])
    return parts


def _split_key_value(part: str):
    """Findet ein Topebene '=' und liefert (key_name, value_text)."""
    in_str = None
    depth = 0
    index = 0
    size = len(part)
    while index < size:
        char = part[index]
        if in_str:
            if char == "\\":
                index += 2
                continue
            if char == in_str:
                in_str = None
        else:
            if char in ('"', "'"):
                in_str = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif char == "=" and depth == 0:
                return _key_name(part[:index].strip()), part[index + 1:].strip()
        index += 1
    return None, None


def _key_name(key: str) -> str:
    key = key.strip()
    if len(key) >= 3 and key[0] == "[" and key[-1] == "]":
        inner = key[1:-1].strip()
        if (inner[:1] in ('"', "'")) and inner[-1:] == inner[:1]:
            return inner[1:-1] if len(inner) > 2 else inner
        return inner.strip('"').strip("'")
    return key.split(".")[-1].strip()
# ------------------------------------------------------------------------ #
# Wert-/Tabellen-Parsing
# ------------------------------------------------------------------------ #
def _parse_string(raw: str):
    """Parst einen Lua-String ('...' oder "..."). Fallback: roh ohne Quotes."""
    stripped = raw.strip()
    try:
        return ast.literal_eval(stripped)
    except (SyntaxError, ValueError):
        if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ('"', "'"):
            return stripped[1:-1]
        return stripped


def _parse_value(raw: str):
    text = raw.strip().rstrip(",").strip()
    if not text:
        return None
    if text.startswith("{"):
        return _parse_table(text[1:-1])
    if (text[:1] == '"' and text[-1:] == '"') or (text[:1] == "'" and text[-1:] == "'"):
        return _parse_string(text)
    low = text.lower()
    if low in ("nil", "none"):
        return None
    if low in ("true", "false"):
        return low == "true"
    try:
        if any(char in text for char in ".eE"):
            return float(text.replace("_", ""))
        return int(text.replace("_", ""))
    except ValueError:
        return text


KEY_FIELDS = ("type", "name", "icon", "icons", "icon_size", "category")


def _parse_table(content: str) -> dict:
    content = content.strip()
    if content.startswith("{"):
        matched, _ = _capture_braces(content, 0)
        content = (matched if matched is not None else content[1:-1]).strip()
    data = {}
    for part in _split_top_level(content):
        key, value_text = _split_key_value(part)
        if not key:
            continue
        data[key] = _parse_value(value_text or "")
    return data


# ------------------------------------------------------------------------ #
# Prototypen-Extraktion
# ------------------------------------------------------------------------ #
def extract_prototypes(text: str, source_mod: str = "unknown", source_file: str = "unknown") -> list:
    """Liest alle <Prototype>-Datensätze aus einem Lua-Text (data:extend)."""
    records = []
    for content in _find_extend_contents(text):
        for element in _split_top_level(content):
            data = _parse_table(element)
            if not isinstance(data, dict):
                continue
            name = data.get("name")
            prototype_type = data.get("type")
            if not name or not prototype_type:
                continue
            keep = {field: data[field] for field in KEY_FIELDS if field in data}
            keep_type = str(prototype_type).lower().replace(" ", "_")
            records.append(Prototype(str(name), keep_type, source_mod, source_file, keep))
    return records


def read_lua_prototypes(root, source_mod: str = "unknown") -> list:
    """Scannt ein Verzeichnis rekursiv auf .lua-Dateien und extrahiert Prototypen."""
    root = Path(root)
    records = []
    for path in sorted(root.rglob("*.lua")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        records.extend(extract_prototypes(text, source_mod, str(path)))
    return records