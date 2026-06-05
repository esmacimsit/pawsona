from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    return load_yaml_text(path.read_text(encoding="utf-8"), source=str(path))


def load_yaml_text(text: str, source: str = "<yaml>") -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return _load_simple_yaml_text(text, source)

    data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a YAML mapping")
    return data


def write_yaml_mapping(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write(_dump_simple_yaml_mapping(data))


def _load_simple_yaml_mapping(path: Path) -> dict[str, Any]:
    return _load_simple_yaml_text(path.read_text(encoding="utf-8"), str(path))


def _load_simple_yaml_text(text: str, source: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_map: dict[str, Any] | None = None

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"{source}:{line_number}: expected 'key: value'")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise ValueError(f"{source}:{line_number}: missing key")

        if indent == 0:
            if raw_value == "":
                current_map = {}
                root[key] = current_map
            else:
                current_map = None
                root[key] = _parse_scalar(raw_value)
        elif indent == 2:
            if current_map is None:
                raise ValueError(f"{source}:{line_number}: nested value without a parent")
            current_map[key] = _parse_scalar(raw_value)
        else:
            raise ValueError(f"{source}:{line_number}: only two-space nesting is supported")

    return root


def _parse_scalar(value: str) -> Any:
    if value == "{}":
        return {}
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def _dump_simple_yaml_mapping(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"{key}:")
                for nested_key, nested_value in value.items():
                    lines.append(f"  {nested_key}: {_format_scalar(nested_value)}")
            else:
                lines.append(f"{key}: {{}}")
        else:
            lines.append(f"{key}: {_format_scalar(value)}")
        if key in {"neutered", "traits", "skills"}:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
