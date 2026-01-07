import streamlit as st
import pandas as pd
import plotly.express as px
import constants as C
from geocoding_service import GeocodingService


geo_service = GeocodingService()


def render(df: pd.DataFrame):
    signed = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    # Region is already in df from data service
    signed["_pid"] = signed[C.COL_INT_PARTNER].astype(str).str.strip()
    signed["_pid"] = signed["_pid"].where(
        signed["_pid"] != "", signed[C.COL_INT_CEP].astype(str).str.strip()
    )
    signed["_pid"] = signed["_pid"].where(
        signed["_pid"] != "",
        signed[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + signed[C.COL_INT_STATE].astype(str).str.strip(),
    )
    signed_unique = signed.drop_duplicates(subset=["_pid"]).copy()

    k1, k2 = st.columns([1, 1])
    k1.metric(
        C.UI_LABEL_STATES_PRESENT,
        signed_unique[C.COL_INT_STATE].replace("", pd.NA).dropna().nunique(),
    )
    k2.metric(
        C.UI_LABEL_CITIES_PRESENT,
        signed_unique[C.COL_INT_CITY].replace("", pd.NA).dropna().nunique(),
    )

    unique_locations = signed_unique[
        [C.COL_INT_CITY, C.COL_INT_STATE]
    ].drop_duplicates()
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
            geo_rows.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "cidade": row.get(C.COL_INT_CITY, ""),
                    "estado": row.get(C.COL_INT_STATE, ""),
                }
            )

    if geo_rows:
        geo_df = pd.DataFrame(geo_rows)
        fig_map = px.scatter_mapbox(
            geo_df,
            lat="lat",
            lon="lon",
            hover_name="cidade",
            hover_data={"estado": True, "lat": False, "lon": False},
            color_discrete_sequence=[C.COLOR_SECONDARY],
            zoom=3,
            center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT},
            title=C.UI_LABEL_MAP_DISTRIBUTION_TITLE,
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            height=600,
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
        )
        st.plotly_chart(fig_map, width="stretch")

    # --- New Feature: City Search ---
    st.markdown("### Pesquisar Cidade")
    search_col1, search_col2 = st.columns([2, 1])
    with search_col1:
        search_city = st.text_input("Digite o nome da cidade para verificar se há polo parceiro:")
    
    if search_city:
        # Normalize search and data for comparison
        search_term = search_city.strip().lower()
        cities_normalized = signed_unique[C.COL_INT_CITY].astype(str).str.strip().str.lower()
        
        # Check for exact match (case insensitive)
        matches = signed_unique[cities_normalized == search_term]
        
        if not matches.empty:
            found_states = matches[C.COL_INT_STATE].unique().tolist()
            st.success(f"✅ A cidade '{search_city}' possui polo parceiro! (Estado(s): {', '.join(found_states)})")
        else:
            # Optional: Partial match suggestion
            partial_matches = signed_unique[cities_normalized.str.contains(search_term, regex=False)]
            if not partial_matches.empty:
                suggestions = partial_matches[C.COL_INT_CITY].unique().tolist()[:5] # Limit to 5
                st.warning(f"❌ Cidade exata não encontrada. Você quis dizer: {', '.join(suggestions)}?")
            else:
                st.error(f"❌ A cidade '{search_city}' não possui polo parceiro registrado.")
    
    st.divider()
    # --------------------------------

    counts_state = signed_unique[C.COL_INT_STATE].value_counts().reset_index()
    counts_state.columns = [C.UI_LABEL_COL_STATE, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(counts_state, x=C.UI_LABEL_COL_STATE, y=C.UI_LABEL_COL_PARTNERS, title=C.UI_LABEL_PARTNERS_BY_STATE),
        width="stretch",
    )

    # --- New Feature: Partner Distribution Chart ---
    # Group by number of partners to see how many states have 1, 2, 3... partners
    dist_data = counts_state[C.UI_LABEL_COL_PARTNERS].value_counts().reset_index()
    dist_data.columns = [C.UI_LABEL_COL_PARTNERS, "Qtd Estados"]
    dist_data = dist_data.sort_values(C.UI_LABEL_COL_PARTNERS)
    
    # Add list of states for tooltip
    state_lists = []
    for count in dist_data[C.UI_LABEL_COL_PARTNERS]:
        states = counts_state[counts_state[C.UI_LABEL_COL_PARTNERS] == count][C.UI_LABEL_COL_STATE].tolist()
        state_lists.append(", ".join(states))
    dist_data["Estados"] = state_lists

    fig_dist = px.bar(
        dist_data,
        x=C.UI_LABEL_COL_PARTNERS,
        y="Qtd Estados",
        hover_data={"Estados": True},
        text="Qtd Estados",
        title="Distribuição de Parceiros por Estado (Quantos estados têm X parceiros)",
        labels={C.UI_LABEL_COL_PARTNERS: "Quantidade de Parceiros", "Qtd Estados": "Quantidade de Estados"}
    )
    fig_dist.update_traces(textposition='outside')
    fig_dist.update_xaxes(type='category') # Treat number of partners as categories
    st.plotly_chart(fig_dist, width="stretch")
    # -----------------------------------------------

    counts_city = signed_unique[C.COL_INT_CITY].value_counts().reset_index()
    counts_city.columns = [C.UI_LABEL_COL_CITY, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(counts_city, x=C.UI_LABEL_COL_CITY, y=C.UI_LABEL_COL_PARTNERS, title=C.UI_LABEL_PARTNERS_BY_CITY),
        width="stretch",
    )

    counts_region = signed_unique[C.COL_INT_REGION].value_counts().reset_index()
    counts_region.columns = [C.UI_LABEL_COL_REGION, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(counts_region, x=C.UI_LABEL_COL_REGION, y=C.UI_LABEL_COL_PARTNERS, title=C.UI_LABEL_PARTNERS_BY_REGION),
        width="stretch",
    )

    all_states = sorted(list(C.ESTADO_REGIAO.keys()))
    present_states = (
        signed_unique[C.COL_INT_STATE].replace("", pd.NA).dropna().unique().tolist()
    )
    present_states = [s for s in present_states if s in C.ESTADO_REGIAO]
    missing_states = [s for s in all_states if s not in set(present_states)]
    if missing_states:
        df_missing = pd.DataFrame(
            {
                C.UI_LABEL_COL_STATE: missing_states,
                C.UI_LABEL_COL_REGION: [C.ESTADO_REGIAO[s] for s in missing_states],
            }
        )
        st.markdown(C.UI_LABEL_STATES_WITHOUT_PARTNERS)
        st.table(df_missing)
