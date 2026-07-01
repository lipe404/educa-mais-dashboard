import pytest
import pandas as pd
import numpy as np
import constants as C
from ui.captadores_tab import (
    _aggregate_partner_captador_map,
    _aggregate_revenue_by_captador,
    _aggregate_captured_partners,
    _aggregate_waiting_contracts,
    _aggregate_ticket_medio_by_captador,
    _aggregate_radar_data,
    _aggregate_revenue_per_contract,
    _aggregate_monthly_partners,
    _aggregate_cumulative_revenue,
    _aggregate_bump_chart_data,
    _aggregate_mom_growth,
    _aggregate_heatmap_data,
    _aggregate_geo_dispersion,
    _calculate_captador_commission_projection,
    _aggregate_seasonality
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

    def test_aggregate_ticket_medio_by_captador(self):
        # Sample faturamento data
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner A", "Partner B", "Partner C"],
            C.COL_INT_VALOR: [1000.0, 2000.0, 5000.0, 500.0]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_ticket_medio_by_captador(fat_df, map_df)
        
        # Leila has Partner A (3000) and Partner B (5000) -> total faturamento = 8000, 2 partners -> Ticket Médio = 4000
        # Thais has Partner C (500) -> total faturamento = 500, 1 partner -> Ticket Médio = 500
        assert len(res) == 2
        
        # Sorted descending: Leila (4000), Thais (500)
        assert res.iloc[0]["Captador"] == "Leila"
        assert res.iloc[0][C.UI_LABEL_TICKET_MEDIO_COLUMN] == 4000.0
        
        assert res.iloc[1]["Captador"] == "Thais"
        assert res.iloc[1][C.UI_LABEL_TICKET_MEDIO_COLUMN] == 500.0

    def test_aggregate_radar_data(self):
        # Sample dados
        dados_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais"],
            C.COL_INT_STATUS: [C.STATUS_ASSINADO, C.STATUS_AGUARDANDO, C.STATUS_ASSINADO]
        }
        dados_df = pd.DataFrame(dados_data)
        
        # Sample faturamento
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner C"],
            C.COL_INT_VALOR: [10000.0, 5000.0]
        }
        fat_df = pd.DataFrame(fat_data)
        
        res = _aggregate_radar_data(
            dados_filtered=dados_df,
            fat_filtered=fat_df,
            raw_dados=dados_df,
            tax_pct=30.0,
            captador_pct=1.6
        )
        
        # Leila, Thais, Ana Beatriz, Fernanda, Lorena Oliveira, Luiza Martins
        assert len(res) == 6
        
        leila_row = res[res["Captador"] == "Leila"].iloc[0]
        thais_row = res[res["Captador"] == "Thais"].iloc[0]
        
        # 1. Partners Captured (Signed)
        assert leila_row["Parceiros Captados"] == 1
        assert thais_row["Parceiros Captados"] == 1
        
        # 2. Conversion
        assert leila_row["Conversão"] == 50.0
        assert thais_row["Conversão"] == 100.0
        
        # 3. Faturamento
        assert leila_row["Faturamento"] == 10000.0
        assert thais_row["Faturamento"] == 5000.0
        
        # 4. Ticket Médio
        assert leila_row["Ticket Médio"] == 10000.0
        assert thais_row["Ticket Médio"] == 5000.0
        
        # 5. Commission
        assert leila_row["Comissão"] == 56.0
        assert thais_row["Comissão"] == 28.0

    def test_aggregate_revenue_per_contract(self):
        # Sample faturamento data
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner A", "Partner B", "Partner C"],
            C.COL_INT_VALOR: [1000.0, 2000.0, 5000.0, 500.0]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_revenue_per_contract(fat_df, map_df)
        
        # Leila faturamento = 8000, contracts = 3 -> 8000 / 3 = 2666.67
        # Thais faturamento = 500, contracts = 1 -> 500 / 1 = 500.00
        assert len(res) == 2
        
        # Sorted descending: Leila (2666.67), Thais (500)
        assert res.iloc[0]["Captador"] == "Leila"
        assert round(res.iloc[0][C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN], 2) == 2666.67
        
        assert res.iloc[1]["Captador"] == "Thais"
        assert res.iloc[1][C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN] == 500.0

    def test_aggregate_monthly_partners(self):
        # Sample data
        data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner C"],
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais"],
            C.COL_INT_STATUS: [C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_ASSINADO],
            C.COL_INT_DT: [pd.Timestamp("2026-01-10"), pd.Timestamp("2026-01-15"), pd.Timestamp("2026-02-05")]
        }
        df = pd.DataFrame(data)
        
        res = _aggregate_monthly_partners(df)
        
        # Leila in 2026-01 has 2 partners, in 2026-02 has 0 partners.
        # Thais in 2026-01 has 0 partners, in 2026-02 has 1 partner.
        # We expect a Cartesian product: 2 months * 6 captadores = 12 rows.
        assert len(res) == 12
        
        # Check values
        leila_jan = res[(res["Mês"] == "2026-01") & (res["Captador"] == "Leila")].iloc[0]
        assert leila_jan["Parceiros Captados"] == 2
        
        thais_feb = res[(res["Mês"] == "2026-02") & (res["Captador"] == "Thais")].iloc[0]
        assert thais_feb["Parceiros Captados"] == 1
        
        leila_feb = res[(res["Mês"] == "2026-02") & (res["Captador"] == "Leila")].iloc[0]
        assert leila_feb["Parceiros Captados"] == 0

    def test_aggregate_cumulative_revenue(self):
        # Sample faturamento
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B", "Partner A"],
            C.COL_INT_VALOR: [1000.0, 2000.0, 1500.0],
            C.COL_INT_DATA: [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-03")]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_CAPTADOR: ["Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_cumulative_revenue(fat_df, map_df)
        
        # 3 days * 6 captadores = 18 rows
        assert len(res) == 18
        
        # Group by Captador and check values sorted by date
        leila_res = res[res["Captador"] == "Leila"].sort_values(by="Data")
        assert leila_res.iloc[0]["Faturamento Acumulado"] == 1000.0
        assert leila_res.iloc[1]["Faturamento Acumulado"] == 1000.0
        assert leila_res.iloc[2]["Faturamento Acumulado"] == 2500.0
        
        thais_res = res[res["Captador"] == "Thais"].sort_values(by="Data")
        assert thais_res.iloc[0]["Faturamento Acumulado"] == 0.0
        assert thais_res.iloc[1]["Faturamento Acumulado"] == 2000.0
        assert thais_res.iloc[2]["Faturamento Acumulado"] == 2000.0

    def test_aggregate_bump_chart_data(self):
        # Sample faturamento
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_VALOR: [5000.0, 2000.0],
            C.COL_INT_DATA: [pd.Timestamp("2026-01-10"), pd.Timestamp("2026-01-15")]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_CAPTADOR: ["Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_bump_chart_data(fat_df, map_df)
        
        # Leila has 5000 (Rank 1), Thais has 2000 (Rank 2) in Jan 2026.
        # Since it ranks the 6 captadores, the other 4 will have faturamento 0 (Rank 3).
        # Total rows = 1 month * 6 captadores = 6 rows.
        assert len(res) == 6
        
        leila_row = res[res["Captador"] == "Leila"].iloc[0]
        thais_row = res[res["Captador"] == "Thais"].iloc[0]
        
        assert leila_row["rank"] == 1
        assert thais_row["rank"] == 2

    def test_aggregate_mom_growth(self):
        # Sample monthly revenue data
        data = {
            "_ano": [2026, 2026, 2026, 2026],
            "_mes": [1, 2, 1, 2],
            "Mês Extenso": ["Janeiro 2026", "Fevereiro 2026", "Janeiro 2026", "Fevereiro 2026"],
            "Captador": ["Leila", "Leila", "Thais", "Thais"],
            "Faturamento": [1000.0, 1500.0, 500.0, 250.0]
        }
        df = pd.DataFrame(data)
        
        res = _aggregate_mom_growth(df)
        
        # Leila MoM in Feb = (1500 - 1000) / 1000 * 100 = 50%
        # Thais MoM in Feb = (250 - 500) / 500 * 100 = -50%
        leila_feb = res[(res["Mês Extenso"] == "Fevereiro 2026") & (res["Captador"] == "Leila")].iloc[0]
        thais_feb = res[(res["Mês Extenso"] == "Fevereiro 2026") & (res["Captador"] == "Thais")].iloc[0]
        
        assert leila_feb["Crescimento MoM (%)"] == 50.0
        assert thais_feb["Crescimento MoM (%)"] == -50.0

    def test_aggregate_heatmap_data(self):
        # Sample faturamento
        fat_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_VALOR: [5000.0, 2000.0],
            C.COL_INT_DATA: [pd.Timestamp("2026-01-10"), pd.Timestamp("2026-01-15")]
        }
        fat_df = pd.DataFrame(fat_data)
        
        # Mapping
        map_data = {
            C.COL_INT_PARTNER: ["Partner A", "Partner B"],
            C.COL_INT_CAPTADOR: ["Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)
        
        res = _aggregate_heatmap_data(pd.DataFrame(), fat_df, map_df, "Faturamento")
        
        # 6 captadores index, 1 month column
        assert res.shape == (6, 1)
        assert res.loc["Leila"].iloc[0] == 5000.0
        assert res.loc["Thais"].iloc[0] == 2000.0
        assert res.loc["Fernanda"].iloc[0] == 0.0

    def test_aggregate_geo_dispersion(self):
        # Sample dados with geographic info
        data = {
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais", "Thais", "Thais"],
            C.COL_INT_STATE: ["SP", "SP", "SP", "RJ", "RJ"],
            C.COL_INT_CITY: ["São Paulo", "Guarulhos", "São Paulo", "Rio de Janeiro", "Niterói"],
            C.COL_INT_STATUS: [C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_ASSINADO],
            C.COL_INT_PARTNER: ["P1", "P2", "P3", "P4", "P5"]
        }
        df = pd.DataFrame(data)

        res = _aggregate_geo_dispersion(df)

        # 6 main captadores
        assert len(res) == 6

        leila_row = res[res["Captador"] == "Leila"].iloc[0]
        thais_row = res[res["Captador"] == "Thais"].iloc[0]

        # Leila: SP (2 partners)
        # States: 1, Cities: 2. HHI = 1.0^2 * 10000 = 10000
        assert leila_row["Estados Atingidos"] == 1
        assert leila_row["Cidades Atingidas"] == 2
        assert leila_row["HHI Regional"] == 10000.0

        # Thais: SP (1 partner), RJ (2 partners)
        # States: 2, Cities: 3.
        # State shares: SP = 1/3, RJ = 2/3. HHI = ((1/3)^2 + (2/3)^2) * 10000 = (1/9 + 4/9) * 10000 = 5/9 * 10000 = 5555.6
        assert thais_row["Estados Atingidos"] == 2
        assert thais_row["Cidades Atingidas"] == 3
        assert thais_row["HHI Regional"] == 5555.6

    def test_calculate_captador_commission_projection(self):
        # Sample faturamento data in month of June 2026
        # Say June 30 is the max date (30 elapsed days, 30 total days in June)
        fat_data = {
            C.COL_INT_PARTNER: ["P1", "P2"],
            C.COL_INT_VALOR: [10000.0, 20000.0],
            C.COL_INT_DATA: [pd.Timestamp("2026-06-15"), pd.Timestamp("2026-06-20")]
        }
        fat_df = pd.DataFrame(fat_data)

        # Partner-Captador Map
        map_data = {
            C.COL_INT_PARTNER: ["P1", "P2"],
            C.COL_INT_CAPTADOR: ["Leila", "Thais"]
        }
        map_df = pd.DataFrame(map_data)

        res = _calculate_captador_commission_projection(fat_df, map_df, 1.6)

        # 6 main captadores
        assert len(res) == 6

        leila_row = res[res["Captador"] == "Leila"].iloc[0]
        thais_row = res[res["Captador"] == "Thais"].iloc[0]

        # Leila: June has 30 days, elapsed = 20 (since max date is June 20th in the dataset)
        # Realizado = 10000. Daily rate = 10000 / 20 = 500. Projected = 10000 + 500 * (30 - 20) = 15000
        # Commission Realizada = 10000 * 0.016 = 160. Commission Projected = 15000 * 0.016 = 240
        assert leila_row["Realizado (R$)"] == 10000.0
        assert leila_row["Comissão Realizada (R$)"] == 160.0
        assert leila_row["Projetado (R$)"] == 15000.0
        assert leila_row["Comissão Projetada (R$)"] == 240.0

    def test_aggregate_seasonality(self):
        # Sample dados
        data = {
            C.COL_INT_CAPTADOR: ["Leila", "Leila", "Thais"],
            C.COL_INT_STATUS: [C.STATUS_ASSINADO, C.STATUS_ASSINADO, C.STATUS_ASSINADO],
            C.COL_INT_PARTNER: ["P1", "P2", "P3"],
            C.COL_INT_DT: [pd.Timestamp("2026-01-15"), pd.Timestamp("2026-02-15"), pd.Timestamp("2026-03-15")]
        }
        df = pd.DataFrame(data)

        res_monthly = _aggregate_seasonality(df, "Mensal")
        # 12 calendar months * 6 captadores = 72 rows
        assert len(res_monthly) == 72
        
        leila_jan = res_monthly[(res_monthly["Captador"] == "Leila") & (res_monthly["Nome Periodo"] == "Jan")].iloc[0]
        assert leila_jan["Parceiros"] == 1

        res_quarterly = _aggregate_seasonality(df, "Trimestral")
        # 4 quarters * 6 captadores = 24 rows
        assert len(res_quarterly) == 24

        leila_q1 = res_quarterly[(res_quarterly["Captador"] == "Leila") & (res_quarterly["Nome Periodo"] == "T1")].iloc[0]
        # Jan & Feb are Q1 -> 2 unique partners
        assert leila_q1["Parceiros"] == 2


