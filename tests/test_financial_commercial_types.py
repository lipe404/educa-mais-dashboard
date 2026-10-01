from datetime import date, datetime
from pathlib import Path
import re
from unittest.mock import patch

import pandas as pd

import constants as C
from services import data as data_service
from ui.financial_tab import _calculate_direct_sales_kpis


@patch("services.data.load_sheet")
def test_faturamento_preserves_both_direct_commercial_types(mock_load_sheet):
    raw = pd.DataFrame(
        {
            "Partner Name": ["Venda Técnica", "Venda Pós"],
            C.COL_SRC_FINANCIAL_TYPE: [" comercial tec ", "comercial pos"],
            C.COL_SRC_VALOR: ["810", "390"],
            C.COL_SRC_COMISSAO: ["50", "50"],
            C.COL_SRC_DATA: ["21/09/2026", "30/09/2026"],
        }
    )
    mock_load_sheet.return_value = (raw, datetime(2026, 9, 30))

    loaded, _ = data_service.get_faturamento(
        "financial-commercial-types-test"
    )

    assert loaded[C.COL_INT_FINANCIAL_TYPE].tolist() == [
        C.FINANCIAL_TYPE_COMERCIAL_TEC,
        C.FINANCIAL_TYPE_COMERCIAL_POS,
    ]


def test_direct_sales_kpis_are_calculated_independently_by_channel():
    df = pd.DataFrame(
        {
            C.COL_INT_DATA: pd.to_datetime(
                ["2026-09-30", "2026-09-28", "2026-08-15"]
            ),
            C.COL_INT_VALOR: [390.0, 610.0, 500.0],
        }
    )

    result = _calculate_direct_sales_kpis(df, date(2026, 9, 30))

    assert result == {
        "total": 1500.0,
        "today": 390.0,
        "week": 1000.0,
        "month": 1000.0,
        "count": 3,
        "ticket": 500.0,
    }


def test_contract_filter_labels_distinguish_partner_and_commercial_channels():
    assert C.CONTRACT_TYPE_UI_TECNICO == "Técnico"
    assert C.CONTRACT_TYPE_UI_POS == "Pós-Graduação"
    assert C.CONTRACT_TYPE_UI_COMERCIAL_TEC == "Comercial Técnico"
    assert C.CONTRACT_TYPE_UI_COMERCIAL_POS == "Comercial Pós"
    assert C.FINANCIAL_TYPE_COMERCIAL_TEC != C.FINANCIAL_TYPE_COMERCIAL_POS
    assert set(C.FINANCIAL_TYPES_DIRECT_COMMERCIAL) == {
        C.FINANCIAL_TYPE_COMERCIAL_TEC,
        C.FINANCIAL_TYPE_COMERCIAL_POS,
    }


def test_source_text_does_not_contain_unicode_emoji():
    project_root = Path(__file__).resolve().parent.parent
    emoji_pattern = re.compile(
        "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF]"
    )
    offenders = []
    source_paths = list(project_root.rglob("*.py")) + list(
        project_root.rglob("*.md")
    )
    for path in source_paths:
        if any(part in {"venv", ".git", "__pycache__"} for part in path.parts):
            continue
        if emoji_pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(project_root)))

    assert offenders == []
