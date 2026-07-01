import pytest
import pandas as pd
import numpy as np
import constants as C
from ui.captadores_tab import (
    _aggregate_partner_captador_map,
    _aggregate_revenue_by_captador,
    _aggregate_captured_partners,
    _aggregate_waiting_contracts
)

class TestCaptadoresTab:
    """
    Unit tests for Captadores Tab aggregation functions.
    """

    def test_aggregate_partner_captador_map(self):
        # Sample data
        data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner A", "  "],
            C.COL_INT_CAPTADOR: ["Leila", "Thais", "Leila", "Fernanda"]
        }
        df = pd.DataFrame(data)
        
        res = _aggregate_partner_captador_map(df)
        
        # Verify mapping deduplication
        assert len(res) == 2
        assert set(res[C.COL_INT_PARTNER]) == {"Partner A", "Partner B"}
        
        # Leila is mapped to Partner A, Thais to Partner B
        map_dict = dict(zip(res[C.COL_INT_PARTNER], res[C.COL_INT_CAPTADOR]))
        assert map_dict["Partner A"] == "Leila"
        assert map_dict["Partner B"] == "Thais"

    def test_aggregate_revenue_by_captador(self):
        # Sample faturamento data
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C"],
            C.COL_INT_VALOR: [1000.0, 2000.0, 500.0]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_CAPTADOR: ["leila", "thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_revenue_by_captador(fat_df, map_df)
        
        # We expect Leila, Thais, and "Não identificado" (for Partner C)
        assert len(res) == 3
        
        # Check sort by revenue descending (Thais has 2000, Leila 1000, Unidentified 500)
        assert res.iloc[0]["Captador"] == "Thais"
        assert res.iloc[0][C.UI_LABEL_REVENUE_COLUMN] == 2000.0
        
        assert res.iloc[1]["Captador"] == "Leila"
        assert res.iloc[1][C.UI_LABEL_REVENUE_COLUMN] == 1000.0
        
        assert res.iloc[2]["Captador"] == C.UI_LABEL_UNIDENTIFIED
        assert res.iloc[2][C.UI_LABEL_REVENUE_COLUMN] == 500.0

    def test_aggregate_captured_partners_signed_only(self):
        # Sample data with ASSINADO and other statuses
        data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner A", "Partner C"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais", "Thais"],
            C.COL_INT_STATUS: [C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_AGUARDANDO, C.STATUS_CANCELADO]
        }
        df = pd.DataFrame(data)
        
        res = _aggregate_captured_partners(df)
        
        # Only Leila's Partner A and B should be counted because they are ASSINADO.
        # Thais's Partner A is AGUARDANDO, and Partner C is CANCELADO, so they won't count.
        assert len(res) == 1
        assert res.iloc[0]["Captador"] == "Leila"
        assert res.iloc[0]["Parceiros Captados"] == 2

    def test_aggregate_waiting_contracts(self):
        # Sample data with AGUARDANDO and other statuses
        data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C", "Partner D"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais", "Thais"],
            C.COL_INT_STATUS: [C.STATUS_AGUARDANDO, C.STATUS_ASSINADO, C.STATUS_AGUARDANDO, C.STATUS_AGUARDANDO]
        }
        df = pd.DataFrame(data)
        
        res = _aggregate_waiting_contracts(df)
        
        # Leila has 1 AGUARDANDO contract (Partner A)
        # Thais has 2 AGUARDANDO contracts (Partner C and D)
        assert len(res) == 2
        
        # Sorted descending: Thais (2), Leila (1)
        assert res.iloc[0]["Captador"] == "Thais"
        assert res.iloc[0]["Contratos Aguardando"] == 2
        
        assert res.iloc[1]["Captador"] == "Leila"
        assert res.iloc[1]["Contratos Aguardando"] == 1
