from typing import Callable, Any, Dict, Tuple, List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import constants as C


def _prepare_map_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepares the dataframe for map visualization."""
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
    return signed, signed_unique


def _render_map_kpis(signed_unique: pd.DataFrame) -> None:
    """Renders the top KPIs for the map tab."""
    k1, k2 = st.columns([1, 1])
    k1.metric(
        C.UI_LABEL_STATES_PRESENT,
        signed_unique[C.COL_INT_STATE].replace("", pd.NA).dropna().nunique(),
    )
    k2.metric(
        C.UI_LABEL_CITIES_PRESENT,
        signed_unique[C.COL_INT_CITY].replace("", pd.NA).dropna().nunique(),
    )
    st.divider()


def _render_boundary_map(
    unique_locations: pd.DataFrame,
    get_ibge_code: Callable[[str, str], str],
    get_municipality_geojson: Callable[[str], Dict[str, Any]],
) -> None:
    """Renders the Folium map with municipality boundaries."""
    st.info(
        "Carregando limites territoriais... Isso pode levar alguns segundos na primeira execução."
    )

    # Center map on Brazil
    m = folium.Map(location=[C.MAP_LAT_DEFAULT, C.MAP_LON_DEFAULT], zoom_start=4)

    # Progress bar
    prog_bar = st.progress(0, text="Buscando geometrias...")
    total_cities = len(unique_locations)

    # Limit to avoid freezing if too many cities
    LIMIT_CITIES = 100
    if total_cities > LIMIT_CITIES:
        st.warning(
            f"Muitas cidades encontradas ({total_cities}). Exibindo apenas as primeiras {LIMIT_CITIES} para performance."
        )
        unique_locations = unique_locations.head(LIMIT_CITIES)
        total_cities = LIMIT_CITIES

    success_count = 0

    for i, (idx, row) in enumerate(unique_locations.iterrows()):
        city, state = row[C.COL_INT_CITY], row[C.COL_INT_STATE]
        if city and state:
            # 1. Get IBGE Code
            ibge_code = get_ibge_code(city, state)
            if ibge_code:
                # 2. Get GeoJSON
                geo_data = get_municipality_geojson(ibge_code)
                if geo_data:
                    # 3. Add to Map
                    folium.GeoJson(
                        geo_data,
                        style_function=lambda x: {
                            "fillColor": "#ff2d95",
                            "color": "#0b1437",
                            "weight": 1,
                            "fillOpacity": 0.4,
                        },
                        tooltip=f"{city} - {state}",
                    ).add_to(m)
                    success_count += 1

        # Update progress
        prog_bar.progress(
            min((i + 1) / total_cities, 1.0), text=f"Carregando {city}..."
        )

    prog_bar.empty()

    if success_count == 0:
        st.warning(
            "Não foi possível carregar os limites dos municípios. Verifique a conexão ou os nomes das cidades."
        )
    else:
        st_folium(m, width="100%", height=600, returned_objects=[])


def _render_point_map(
    unique_locations: pd.DataFrame,
    signed_unique: pd.DataFrame,
    get_coords: Callable[[str, str], Tuple[float | None, float | None]],
) -> None:
    """Renders the Plotly scatter mapbox with points."""
    location_map = {}
    for _, row in unique_locations.iterrows():
        c, s = row[C.COL_INT_CITY], row[C.COL_INT_STATE]
        if c and s:
            lat, lon = get_coords(c, s)
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


def _render_city_search(signed_unique: pd.DataFrame) -> None:
    """Renders the city search functionality."""
    st.markdown("### Pesquisar Cidade")
    search_col1, search_col2 = st.columns([2, 1])
    with search_col1:
        search_city = st.text_input(
            "Digite o nome da cidade para verificar se há polo parceiro:"
        )

    if search_city:
        # Normalize search and data for comparison
        search_term = search_city.strip().lower()
        cities_normalized = (
            signed_unique[C.COL_INT_CITY].astype(str).str.strip().str.lower()
        )

        # Check for exact match (case insensitive)
        matches = signed_unique[cities_normalized == search_term]

        if not matches.empty:
            found_states = matches[C.COL_INT_STATE].unique().tolist()
            st.success(
                f"✅ A cidade '{search_city}' possui polo parceiro! (Estado(s): {', '.join(found_states)})"
            )
        else:
            # Optional: Partial match suggestion
            partial_matches = signed_unique[
                cities_normalized.str.contains(search_term, regex=False)
            ]
            if not partial_matches.empty:
                suggestions = (
                    partial_matches[C.COL_INT_CITY].unique().tolist()[:5]
                )  # Limit to 5
                st.warning(
                    f"❌ Cidade exata não encontrada. Você quis dizer: {', '.join(suggestions)}?"
                )
            else:
                st.error(
                    f"❌ A cidade '{search_city}' não possui polo parceiro registrado."
                )
    st.divider()


def _render_distribution_charts(signed_unique: pd.DataFrame) -> None:
    """Renders distribution charts (by state, partners per state, city, region)."""
    # 1. Partners by State
    counts_state = signed_unique[C.COL_INT_STATE].value_counts().reset_index()
    counts_state.columns = [C.UI_LABEL_COL_STATE, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(
            counts_state,
            x=C.UI_LABEL_COL_STATE,
            y=C.UI_LABEL_COL_PARTNERS,
            title=C.UI_LABEL_PARTNERS_BY_STATE,
        ),
        width="stretch",
    )
    st.divider()

    # 2. Partner Distribution (How many states have X partners)
    dist_data = counts_state[C.UI_LABEL_COL_PARTNERS].value_counts().reset_index()
    dist_data.columns = [C.UI_LABEL_COL_PARTNERS, "Qtd Estados"]
    dist_data = dist_data.sort_values(C.UI_LABEL_COL_PARTNERS)

    # Add list of states for tooltip
    state_lists = []
    for count in dist_data[C.UI_LABEL_COL_PARTNERS]:
        states = counts_state[counts_state[C.UI_LABEL_COL_PARTNERS] == count][
            C.UI_LABEL_COL_STATE
        ].tolist()
        state_lists.append(", ".join(states))
    dist_data["Estados"] = state_lists

    fig_dist = px.bar(
        dist_data,
        x=C.UI_LABEL_COL_PARTNERS,
        y="Qtd Estados",
        hover_data={"Estados": True},
        text="Qtd Estados",
        title="Distribuição de Parceiros por Estado (Quantos estados têm X parceiros)",
        labels={
            C.UI_LABEL_COL_PARTNERS: "Quantidade de Parceiros",
            "Qtd Estados": "Quantidade de Estados",
        },
    )
    fig_dist.update_traces(textposition="outside")
    fig_dist.update_xaxes(type="category")
    st.plotly_chart(fig_dist, width="stretch")
    st.divider()

    # 3. Partners by City
    counts_city = signed_unique[C.COL_INT_CITY].value_counts().reset_index()
    counts_city.columns = [C.UI_LABEL_COL_CITY, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(
            counts_city,
            x=C.UI_LABEL_COL_CITY,
            y=C.UI_LABEL_COL_PARTNERS,
            title=C.UI_LABEL_PARTNERS_BY_CITY,
        ),
        width="stretch",
    )
    st.divider()

    # 4. Partners by Region
    counts_region = signed_unique[C.COL_INT_REGION].value_counts().reset_index()
    counts_region.columns = [C.UI_LABEL_COL_REGION, C.UI_LABEL_COL_PARTNERS]
    st.plotly_chart(
        px.bar(
            counts_region,
            x=C.UI_LABEL_COL_REGION,
            y=C.UI_LABEL_COL_PARTNERS,
            title=C.UI_LABEL_PARTNERS_BY_REGION,
        ),
        width="stretch",
    )
    st.divider()


def _render_missing_states_table(signed_unique: pd.DataFrame) -> None:
    """Renders table of states without partners."""
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


def render(
    df: pd.DataFrame,
    get_ibge_code: Callable[[str, str], str],
    get_municipality_geojson: Callable[[str], Dict[str, Any]],
    get_coords: Callable[[str, str], Tuple[float | None, float | None]],
) -> None:
    """Main render function for the Map Tab."""
    
    # 1. Prepare Data
    _, signed_unique = _prepare_map_data(df)

    # 2. Render KPIs
    _render_map_kpis(signed_unique)

    # 3. Render Map
    unique_locations = signed_unique[
        [C.COL_INT_CITY, C.COL_INT_STATE]
    ].drop_duplicates()

    # Map Toggle
    use_boundary_map = st.toggle(
        "Ativar Mapa de Limites (GeoJSON)",
        value=False,
        help="Exibe os limites territoriais dos municípios. Pode ser mais lento para carregar.",
    )

    if use_boundary_map:
        _render_boundary_map(unique_locations, get_ibge_code, get_municipality_geojson)
    else:
        _render_point_map(unique_locations, signed_unique, get_coords)

    st.divider()

    # 4. Render City Search
    _render_city_search(signed_unique)

    # 5. Render Distribution Charts
    _render_distribution_charts(signed_unique)

    # 6. Render Missing States Table
    _render_missing_states_table(signed_unique)

