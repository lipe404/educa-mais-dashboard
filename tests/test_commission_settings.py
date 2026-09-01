import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from services.commission_settings import (
    DEFAULT_PARTNER_PCT,
    DEFAULT_TAX_PCT,
    get_default_commission_settings,
    load_commission_settings,
    normalize_commission_settings,
    save_commission_settings,
)
from ui import commissions_tab
from ui.commissions_tab import nominal_to_real, real_to_nominal


def test_first_load_creates_default_file(tmp_path):
    config_path = tmp_path / "commission_settings.json"
    settings = load_commission_settings(
        config_path=config_path,
        legacy_path=tmp_path / "missing_legacy.json",
    )

    assert config_path.exists()
    assert settings["default_partner_pct"] == DEFAULT_PARTNER_PCT
    assert settings["tax_pct"] == DEFAULT_TAX_PCT
    assert settings["team_members"] == []
    assert settings["assignments"] == []


def test_round_trip_persists_all_editable_configuration(tmp_path):
    config_path = tmp_path / "commission_settings.json"
    settings = get_default_commission_settings()
    settings["default_partner_pct"] = 45.0
    settings["tax_pct"] = 27.0
    settings["team_categories"]["captador"]["percentage"] = 2.25
    settings["team_members"] = [
        {"id": 100, "name": "Pessoa Teste", "roles": ["captador"]}
    ]
    settings["assignments"] = [
        {"partner_id": "Parceiro A", "captador_id": 100}
    ]

    save_commission_settings(settings, config_path)
    loaded = load_commission_settings(
        config_path=config_path,
        legacy_path=tmp_path / "missing_legacy.json",
    )

    assert loaded == settings
    assert not (tmp_path / "commission_settings.json.tmp").exists()


def test_old_partial_settings_are_merged_without_losing_values(tmp_path):
    config_path = tmp_path / "commission_settings.json"
    config_path.write_text(
        json.dumps({"version": 1, "default_partner_pct": 45}),
        encoding="utf-8",
    )

    loaded = load_commission_settings(
        config_path=config_path,
        legacy_path=tmp_path / "missing_legacy.json",
    )

    assert loaded["default_partner_pct"] == 45.0
    assert loaded["tax_pct"] == DEFAULT_TAX_PCT
    assert loaded["team_categories"]
    assert loaded["team_members"] == []
    assert loaded["assignments"] == []


def test_legacy_categories_are_migrated_exactly(tmp_path):
    config_path = tmp_path / "commission_settings.json"
    legacy_path = tmp_path / "team_categories_config.json"
    legacy_categories = {
        "cargo_personalizado": {
            "name": "Cargo Personalizado",
            "percentage": 7.5,
            "type": "fixed",
        }
    }
    legacy_path.write_text(json.dumps(legacy_categories), encoding="utf-8")

    loaded = load_commission_settings(config_path, legacy_path)

    assert loaded["team_categories"] == legacy_categories
    assert json.loads(config_path.read_text(encoding="utf-8"))["team_categories"] == legacy_categories
    assert legacy_path.exists()


def test_corrupt_json_falls_back_without_overwriting_the_corrupt_file(tmp_path):
    config_path = tmp_path / "commission_settings.json"
    corrupt_contents = "{not-valid-json"
    config_path.write_text(corrupt_contents, encoding="utf-8")

    loaded = load_commission_settings(
        config_path=config_path,
        legacy_path=tmp_path / "missing_legacy.json",
    )

    assert loaded == get_default_commission_settings()
    assert config_path.read_text(encoding="utf-8") == corrupt_contents


def test_invalid_values_use_safe_fallbacks_and_future_fields_survive():
    normalized = normalize_commission_settings(
        {
            "version": 2,
            "default_partner_pct": "abc",
            "global_tax_pct": 27,
            "future_setting": {"enabled": True},
            "team_categories": {
                "captador": {
                    "name": "Captador",
                    "percentage": 500,
                    "type": "partner_based",
                }
            },
            "team_members": "invalid",
            "assignments": [None, {"partner_id": None}],
        }
    )

    assert normalized["version"] == 2
    assert normalized["default_partner_pct"] == DEFAULT_PARTNER_PCT
    assert normalized["tax_pct"] == 27.0
    assert "global_tax_pct" not in normalized
    assert normalized["team_categories"]["captador"]["percentage"] == 1.0
    assert normalized["team_members"] == []
    assert normalized["assignments"] == []
    assert normalized["future_setting"] == {"enabled": True}


@pytest.mark.parametrize("tax_pct,partner_pct", [(0.0, 50.0), (27.0, 45.0), (30.0, 50.0)])
def test_real_percentage_round_trip_preserves_financial_formula(tax_pct, partner_pct):
    nominal = 3.496569468267581
    real = nominal_to_real("cargo", nominal, {}, tax_pct, partner_pct)

    assert real_to_nominal("cargo", real, {}, tax_pct, partner_pct) == pytest.approx(nominal)


def test_real_percentage_callback_recalculates_and_persists_complete_settings(
    monkeypatch,
):
    settings = get_default_commission_settings()
    state = {
        "commission_settings": deepcopy(settings),
        "default_partner_pct": 45.0,
        "global_tax_pct": 27.0,
        "team_categories": deepcopy(settings["team_categories"]),
        "team_members": [
            {"id": 100, "name": "Pessoa Teste", "roles": ["captador"]}
        ],
        "assignments": [{"partner_id": "Parceiro A", "captador_id": 100}],
        "real_pct_captador": 0.75,
    }
    persisted = {}

    def fake_save(snapshot):
        persisted.update(deepcopy(snapshot))
        return deepcopy(snapshot)

    monkeypatch.setattr(
        commissions_tab,
        "st",
        SimpleNamespace(session_state=state, error=lambda _message: None),
    )
    monkeypatch.setattr(commissions_tab, "save_commission_settings", fake_save)

    commissions_tab.on_real_change("captador", 27.0, 45.0)

    expected_nominal = real_to_nominal("captador", 0.75, {}, 27.0, 45.0)
    assert state["team_categories"]["captador"]["percentage"] == pytest.approx(
        expected_nominal
    )
    assert persisted["team_categories"]["captador"]["percentage"] == pytest.approx(
        expected_nominal
    )
    assert persisted["default_partner_pct"] == 45.0
    assert persisted["tax_pct"] == 27.0
    assert persisted["team_members"] == state["team_members"]
    assert persisted["assignments"] == state["assignments"]
