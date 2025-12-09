import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List
import os
from dotenv import load_dotenv
import constants as C
from geocoding_service import GeocodingService
from services.opportunity import build_oportunidade_por_uf


load_dotenv()
API_KEY = os.getenv("KEY_API") or "@educamais@123"
geo_service = GeocodingService()


def render(dados_df: pd.DataFrame):
    key = st.text_input("Chave de acesso", type="password")
    if key != API_KEY:
        st.warning("Digite a chave de acesso para visualizar a análise.")
        return

    ufs_all = sorted([s for s in dados_df[C.COL_INT_STATE].unique() if s]) or sorted(list(C.ESTADO_REGIAO.keys()))
    ufs_selected: List[str] = st.multiselect("Estados", ufs_all, default=ufs_all)

    with st.spinner("Carregando análise de oportunidade..."):
        df = build_oportunidade_por_uf(dados_df, ufs_selected)

    min_pop = st.slider("População mínima (2022)", min_value=0, max_value=int(df["pop_2022"].max() if not df.empty else 1000000), value=min(100000, int(df["pop_2022"].max() if not df.empty else 1000000)))
    only_missing = st.checkbox("Somente cidades sem parceiros", value=True)

    mask = (df["pop_2022"] >= min_pop)
    if only_missing:
        mask &= df["presenca"] == 0
    ranked = df.loc[mask].copy()
    if ranked.empty:
        st.info("Nenhuma cidade encontrada com os filtros atuais.")
        return

    st.metric("Total de cidades candidatas", len(ranked))

    st.plotly_chart(
        px.bar(
            ranked.sort_values("score", ascending=False).head(30),
            x="nome",
            y="pop_2022",
            color="uf",
            title="Top 30 cidades por população sem presença",
        ),
        width="stretch",
    )

    top_n = st.slider("Cidades no mapa (geocodificação)", min_value=10, max_value=200, value=50, step=10)
    geo_rows = []
    for _, row in ranked.sort_values("score", ascending=False).head(top_n).iterrows():
        lat, lon = geo_service.get_coords(row.get("nome", ""), row.get("uf", ""))
        if lat is not None and lon is not None:
            geo_rows.append({"lat": lat, "lon": lon, "cidade": row.get("nome", ""), "estado": row.get("uf", ""), "pop": int(row.get("pop_2022", 0))})

    if geo_rows:
        geo_df = pd.DataFrame(geo_rows)
        fig = px.scatter_mapbox(
            geo_df,
            lat="lat",
            lon="lon",
            size="pop",
            hover_name="cidade",
            hover_data={"estado": True, "pop": True, "lat": False, "lon": False},
            color_discrete_sequence=[C.COLOR_PRIMARY],
            zoom=3,
            center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT},
            title="Mapa de oportunidade por população",
        )
        fig.update_layout(mapbox_style="open-street-map", height=600, margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig, width="stretch")

    st.markdown("### Ranking de cidades")
    st.dataframe(ranked.sort_values(["uf", "score"], ascending=[True, False]).reset_index(drop=True))
