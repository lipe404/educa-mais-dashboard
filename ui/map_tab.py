import streamlit as st
import pandas as pd
import plotly.express as px
import constants as C
from geocoding_service import GeocodingService


geo_service = GeocodingService()


def render(df: pd.DataFrame):
    signed = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed[C.COL_INT_REGION] = signed[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna("")
    signed["_pid"] = signed[C.COL_INT_PARTNER].astype(str).str.strip()
    signed["_pid"] = signed["_pid"].where(signed["_pid"] != "", signed[C.COL_INT_CEP].astype(str).str.strip())
    signed["_pid"] = signed["_pid"].where(signed["_pid"] != "", signed[C.COL_INT_CITY].astype(str).str.strip() + "|" + signed[C.COL_INT_STATE].astype(str).str.strip())
    signed_unique = signed.drop_duplicates(subset=["_pid"]).copy()

    k1, k2 = st.columns([1, 1])
    k1.metric("Estados presentes", signed_unique[C.COL_INT_STATE].replace("", pd.NA).dropna().nunique())
    k2.metric("Cidades presentes", signed_unique[C.COL_INT_CITY].replace("", pd.NA).dropna().nunique())

    unique_locations = signed_unique[[C.COL_INT_CITY, C.COL_INT_STATE]].drop_duplicates()
    location_map = {}
    for _, row in unique_locations.iterrows():
        c, s = row[C.COL_INT_CITY], row[C.COL_INT_STATE]
        if c and s:
            lat, lon = geo_service.get_coords(c, s)
            if lat is not None and lon is not None:
                location_map[(c, s)] = (lat, lon)

    geo_rows = []
    for _, row in signed_unique.iterrows():
        k = (row.get(C.COL_INT_CITY, ""), row.get(C.COL_INT_STATE, ""))
        if k in location_map:
            lat, lon = location_map[k]
            geo_rows.append({"lat": lat, "lon": lon, "cidade": row.get(C.COL_INT_CITY, ""), "estado": row.get(C.COL_INT_STATE, "")})

    if geo_rows:
        geo_df = pd.DataFrame(geo_rows)
        fig_map = px.scatter_mapbox(geo_df, lat="lat", lon="lon", hover_name="cidade", hover_data={"estado": True, "lat": False, "lon": False}, color_discrete_sequence=[C.COLOR_SECONDARY], zoom=3, center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT}, title="Distribuição Geográfica de Contratos Assinados")
        fig_map.update_layout(mapbox_style="open-street-map", height=600, margin={"r": 0, "t": 30, "l": 0, "b": 0})
        st.plotly_chart(fig_map, width="stretch")

    counts_state = signed_unique[C.COL_INT_STATE].value_counts().reset_index()
    counts_state.columns = ["Estado", "Parceiros"]
    st.plotly_chart(px.bar(counts_state, x="Estado", y="Parceiros", title="Parceiros por estado"), width="stretch")

    counts_city = signed_unique[C.COL_INT_CITY].value_counts().reset_index()
    counts_city.columns = ["Cidade", "Parceiros"]
    st.plotly_chart(px.bar(counts_city, x="Cidade", y="Parceiros", title="Parceiros por cidade"), width="stretch")

    counts_region = signed_unique[C.COL_INT_REGION].value_counts().reset_index()
    counts_region.columns = ["Região", "Parceiros"]
    st.plotly_chart(px.bar(counts_region, x="Região", y="Parceiros", title="Parceiros por região"), width="stretch")

    all_states = sorted(list(C.ESTADO_REGIAO.keys()))
    present_states = signed_unique[C.COL_INT_STATE].replace("", pd.NA).dropna().unique().tolist()
    present_states = [s for s in present_states if s in C.ESTADO_REGIAO]
    missing_states = [s for s in all_states if s not in set(present_states)]
    if missing_states:
        df_missing = pd.DataFrame({"Estado": missing_states, "Região": [C.ESTADO_REGIAO[s] for s in missing_states]})
        st.markdown("### Estados sem parceiros")
        st.table(df_missing)

