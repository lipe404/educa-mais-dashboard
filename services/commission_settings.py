"""Persistent configuration for the commissions dashboard.

The JSON file managed here is the single persistent source of truth.  Streamlit
session state is deliberately kept out of this module so the persistence layer
can be reused or replaced without coupling it to the UI.
"""

from __future__ import annotations

import json
import logging
import math
import os
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from services.commission import TEAM_CATEGORIES


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "commission_settings.json"
LEGACY_CONFIG_PATH = BASE_DIR / "team_categories_config.json"

CURRENT_VERSION = 1
DEFAULT_PARTNER_PCT = 50.0
DEFAULT_TAX_PCT = 30.0
VALID_ROLE_TYPES = {"fixed", "partner_based"}

DEFAULT_SETTINGS: dict[str, Any] = {
    "version": CURRENT_VERSION,
    "default_partner_pct": DEFAULT_PARTNER_PCT,
    "tax_pct": DEFAULT_TAX_PCT,
    "team_categories": deepcopy(TEAM_CATEGORIES),
    "team_members": [],
    "assignments": [],
}

_FILE_LOCK = threading.RLock()


class CommissionSettingsError(RuntimeError):
    """Raised when a validated configuration cannot be persisted."""


def get_default_commission_settings() -> dict[str, Any]:
    """Return an independent copy of the safe first-run configuration."""

    return deepcopy(DEFAULT_SETTINGS)


def _percentage(value: Any, fallback: float, field_name: str) -> float:
    """Return a percentage in the inclusive 0..100 range or its fallback."""

    try:
        if isinstance(value, bool):
            raise TypeError("boolean is not a percentage")
        parsed = float(value)
        if not math.isfinite(parsed) or not 0.0 <= parsed <= 100.0:
            raise ValueError("percentage outside 0..100")
        return parsed
    except (TypeError, ValueError, OverflowError):
        logger.warning(
            "Invalid commission setting %s=%r; using %.4f",
            field_name,
            value,
            fallback,
        )
        return float(fallback)


def _normalize_categories(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        logger.warning("Invalid team_categories value; using defaults")
        return deepcopy(TEAM_CATEGORIES)

    categories: dict[str, dict[str, Any]] = {}
    for raw_key, raw_category in value.items():
        if not isinstance(raw_key, str) or not raw_key.strip():
            logger.warning("Ignoring commission role with invalid key %r", raw_key)
            continue
        key = raw_key.strip()
        if not isinstance(raw_category, Mapping):
            logger.warning("Ignoring invalid commission role %s", key)
            continue

        role_default = TEAM_CATEGORIES.get(key, {})
        default_name = str(role_default.get("name", key))
        default_type = str(role_default.get("type", "fixed"))
        default_percentage = float(role_default.get("percentage", 0.0))

        name = raw_category.get("name", default_name)
        if not isinstance(name, str) or not name.strip():
            logger.warning("Invalid name for commission role %s; using %r", key, default_name)
            name = default_name

        role_type = raw_category.get("type", default_type)
        if role_type not in VALID_ROLE_TYPES:
            logger.warning(
                "Invalid type for commission role %s; using %s", key, default_type
            )
            role_type = default_type

        category = deepcopy(dict(raw_category))
        category.update(
            {
                "name": name.strip(),
                "percentage": _percentage(
                    raw_category.get("percentage"),
                    default_percentage,
                    f"team_categories.{key}.percentage",
                ),
                "type": role_type,
            }
        )
        categories[key] = category

    return categories


def _is_json_identifier(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return not isinstance(value, str) or bool(value.strip())


def _normalize_members(
    value: Any, categories: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        logger.warning("Invalid team_members value; using an empty list")
        return []

    members: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    for raw_member in value:
        if not isinstance(raw_member, Mapping):
            logger.warning("Ignoring invalid team member %r", raw_member)
            continue

        member_id = raw_member.get("id")
        name = raw_member.get("name")
        if not _is_json_identifier(member_id) or member_id in seen_ids:
            logger.warning("Ignoring team member with invalid or duplicate id %r", member_id)
            continue
        if not isinstance(name, str) or not name.strip():
            logger.warning("Ignoring team member %r with invalid name", member_id)
            continue

        raw_roles = raw_member.get("roles", [])
        if not isinstance(raw_roles, list):
            logger.warning("Invalid roles for team member %r; using an empty list", member_id)
            raw_roles = []
        roles = list(
            dict.fromkeys(
                role
                for role in raw_roles
                if isinstance(role, str) and role in categories
            )
        )

        member = deepcopy(dict(raw_member))
        member.update({"id": member_id, "name": name.strip(), "roles": roles})
        members.append(member)
        seen_ids.add(member_id)

    return members


def _normalize_assignments(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        logger.warning("Invalid assignments value; using an empty list")
        return []

    assignments: list[dict[str, Any]] = []
    for raw_assignment in value:
        if not isinstance(raw_assignment, Mapping):
            logger.warning("Ignoring invalid assignment %r", raw_assignment)
            continue
        partner_id = raw_assignment.get("partner_id")
        if not _is_json_identifier(partner_id):
            logger.warning("Ignoring assignment with invalid partner_id %r", partner_id)
            continue

        assignment = {"partner_id": partner_id}
        for key, member_id in raw_assignment.items():
            if key == "partner_id" or member_id is None:
                continue
            if isinstance(key, str) and key and _is_json_identifier(member_id):
                assignment[key] = member_id
            else:
                logger.warning("Ignoring invalid field %r in assignment %r", key, partner_id)
        if len(assignment) > 1:
            assignments.append(assignment)

    return assignments


def normalize_commission_settings(raw_settings: Any) -> dict[str, Any]:
    """Validate known fields while preserving unknown future top-level fields."""

    if not isinstance(raw_settings, Mapping):
        logger.warning("Commission settings root must be an object; using defaults")
        return get_default_commission_settings()

    settings = deepcopy(dict(raw_settings))

    version = raw_settings.get("version", CURRENT_VERSION)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        logger.warning("Invalid commission settings version %r; using %d", version, CURRENT_VERSION)
        version = CURRENT_VERSION

    # global_tax_pct and com_tax_pct are accepted only as migration aliases.
    tax_value = raw_settings.get(
        "tax_pct",
        raw_settings.get("global_tax_pct", raw_settings.get("com_tax_pct", DEFAULT_TAX_PCT)),
    )
    categories = _normalize_categories(
        raw_settings.get("team_categories", DEFAULT_SETTINGS["team_categories"])
    )

    settings.pop("global_tax_pct", None)
    settings.pop("com_tax_pct", None)
    settings.update(
        {
            "version": version,
            "default_partner_pct": _percentage(
                raw_settings.get("default_partner_pct", DEFAULT_PARTNER_PCT),
                DEFAULT_PARTNER_PCT,
                "default_partner_pct",
            ),
            "tax_pct": _percentage(tax_value, DEFAULT_TAX_PCT, "tax_pct"),
            "team_categories": categories,
            "team_members": _normalize_members(
                raw_settings.get("team_members", []), categories
            ),
            "assignments": _normalize_assignments(
                raw_settings.get("assignments", [])
            ),
        }
    )
    return settings


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_commission_settings(
    settings: Mapping[str, Any], config_path: Path | str = CONFIG_PATH
) -> dict[str, Any]:
    """Validate and atomically write the complete commission configuration."""

    path = Path(config_path)
    normalized = normalize_commission_settings(settings)
    temp_path = path.with_name(f"{path.name}.tmp")

    with _FILE_LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with temp_path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(
                    normalized,
                    file,
                    indent=4,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, path)
        except (OSError, TypeError, ValueError) as exc:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove temporary settings file %s", temp_path)
            logger.exception("Could not save commission settings to %s", path)
            raise CommissionSettingsError(
                f"Não foi possível salvar as configurações de comissões em {path}"
            ) from exc

    return deepcopy(normalized)


def load_commission_settings(
    config_path: Path | str = CONFIG_PATH,
    legacy_path: Path | str = LEGACY_CONFIG_PATH,
) -> dict[str, Any]:
    """Load, validate and, when needed, create or migrate the settings file."""

    path = Path(config_path)
    old_path = Path(legacy_path)

    with _FILE_LOCK:
        if path.exists():
            try:
                raw_settings = _read_json(path)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                logger.error(
                    "Could not load commission settings from %s; using safe defaults: %s",
                    path,
                    exc,
                )
                return get_default_commission_settings()

            normalized = normalize_commission_settings(raw_settings)
            if normalized != raw_settings:
                try:
                    save_commission_settings(normalized, path)
                except CommissionSettingsError:
                    logger.warning("Normalized commission settings could not be written back")
            return normalized

        settings = get_default_commission_settings()
        if old_path.exists():
            try:
                legacy_categories = _read_json(old_path)
                if isinstance(legacy_categories, Mapping):
                    settings["team_categories"] = deepcopy(dict(legacy_categories))
                    logger.info("Migrating commission categories from %s", old_path)
                else:
                    logger.warning("Legacy team categories root is invalid; using defaults")
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                logger.error(
                    "Could not load legacy commission categories from %s: %s",
                    old_path,
                    exc,
                )

        normalized = normalize_commission_settings(settings)
        try:
            return save_commission_settings(normalized, path)
        except CommissionSettingsError:
            # The dashboard remains usable with in-memory defaults, while the
            # explicit error is still recorded by save_commission_settings.
            return normalized
