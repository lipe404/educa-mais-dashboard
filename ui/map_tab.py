from typing import Callable, Any, Dict, Tuple, List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import folium
from streamlit_folium import st_folium
import constants as C
import requests
try:
    from scipy.spatial import Voronoi

    SCIPY_AVAILABLE = True
except Exception:
    Voronoi = None
    SCIPY_AVAILABLE = False


@st.cache_data(ttl=86400, show_spinner=False)
def _get_states_lookup() -> list[dict[str, Any]]:
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        states = r.json()
        if not isinstance(states, list):
            return []
        return sorted(
            [
                {"sigla": str(s.get("sigla", "")).strip(), "id": str(s.get("id", "")).strip()}
                for s in states
                if str(s.get("sigla", "")).strip()
            ],
            key=lambda x: x["sigla"],
        )
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def _get_states_geojson() -> Dict[str, Any] | None:
    try:
        states = _get_states_lookup()
        if not states:
            return None

        features: list[dict[str, Any]] = []
        for s in states:
            sigla = s["sigla"]
            state_id = s.get("id", "")
            url = f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{sigla}?formato=application/vnd.geo+json"
            try:
                r = requests.get(url, timeout=25)
                r.raise_for_status()
                fc = r.json()
                for f in (fc.get("features") or []):
                    props = f.get("properties") or {}
                    props["sigla"] = sigla
                    if state_id:
                        props["id"] = state_id
                    f["properties"] = props
                    features.append(f)
            except Exception:
                continue

        if not features:
            return None

        return {"type": "FeatureCollection", "features": features}
    except Exception:
        return None


def _guess_featureidkey(geojson: Dict[str, Any]) -> str | None:
    try:
        features = geojson.get("features") or []
        if not features:
            return None
        props = (features[0] or {}).get("properties") or {}
        if "sigla" in props:
            return "properties.sigla"
        if "UF" in props:
            return "properties.UF"
        if "uf" in props:
            return "properties.uf"
    except Exception:
        return None
    return None


def _render_uf_choropleth(signed_unique: pd.DataFrame) -> None:
    with st.spinner("Carregando malha de estados (IBGE)..."):
        geojson = _get_states_geojson()
    if not geojson:
        st.warning("Não foi possível carregar o GeoJSON de estados do IBGE.")
        return

    featureidkey = _guess_featureidkey(geojson)
    if not featureidkey:
        st.warning("GeoJSON de estados não possui chave de UF compatível.")
        return

    counts = (
        signed_unique[C.COL_INT_STATE]
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    all_states = sorted(list(C.ESTADO_REGIAO.keys()))
    df_counts = pd.DataFrame({"uf": all_states})
    df_counts["parceiros"] = df_counts["uf"].map(counts).fillna(0).astype(int)
    df_counts["regiao"] = df_counts["uf"].map(C.ESTADO_REGIAO).fillna("")

    fig = px.choropleth_mapbox(
        df_counts,
        geojson=geojson,
        locations="uf",
        featureidkey=featureidkey,
        color="parceiros",
        hover_name="uf",
        hover_data={"regiao": True, "parceiros": True, "uf": False},
        color_continuous_scale=px.colors.sequential.Blues,
        range_color=(0, int(df_counts["parceiros"].max()) if not df_counts.empty else 0),
        opacity=0.65,
        center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT},
        zoom=3,
        title="Densidade de Parceiros por UF (Choropleth)",
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        height=600,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Parceiros"),
    )
    st.plotly_chart(fig, width="stretch")


def _prepare_map_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepares the dataframe for map visualization.

    Filters for signed contracts and enriches the data with a unique identifier (`_pid`)
    based on partner, CEP, or City/State.

    Args:
        df (pd.DataFrame): The input dataframe containing all contract data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing:
            - signed (pd.DataFrame): The filtered dataframe with only signed contracts.
            - signed_unique (pd.DataFrame): A dataframe with unique locations/partners.
    """
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
    """
    Renders the top KPIs for the map tab (States and Cities present).

    Args:
        signed_unique (pd.DataFrame): The dataframe containing unique signed contract locations.
    """
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
    """
    Renders the Folium map with municipality boundaries (GeoJSON).

    Args:
        unique_locations (pd.DataFrame): Dataframe with unique city/state combinations.
        get_ibge_code (Callable[[str, str], str]): Function to retrieve IBGE code for a city.
        get_municipality_geojson (Callable[[str], Dict[str, Any]]): Function to retrieve GeoJSON for a city.
    """
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
    """
    Renders the Plotly scatter mapbox with points representing partner locations.

    Args:
        unique_locations (pd.DataFrame): Dataframe with unique city/state combinations.
        signed_unique (pd.DataFrame): Dataframe with unique signed contract locations.
        get_coords (Callable[[str, str], Tuple[float | None, float | None]]): Function to get lat/lon for a city.
    """
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


def _render_geo_expansion_timeline(
    signed: pd.DataFrame,
    unique_locations: pd.DataFrame,
    get_coords: Callable[[str, str], Tuple[float | None, float | None]],
) -> None:
    if signed.empty or C.COL_INT_DT not in signed.columns:
        return

    base = signed.dropna(subset=[C.COL_INT_DT]).copy()
    if "_pid" not in base.columns:
        base["_pid"] = base[C.COL_INT_PARTNER].astype(str).str.strip()
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "", base[C.COL_INT_CEP].astype(str).str.strip()
        )
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "",
            base[C.COL_INT_CITY].astype(str).str.strip()
            + "|"
            + base[C.COL_INT_STATE].astype(str).str.strip(),
        )

    base[C.COL_INT_CITY] = base[C.COL_INT_CITY].astype(str).str.strip()
    base[C.COL_INT_STATE] = base[C.COL_INT_STATE].astype(str).str.strip()
    base = base[(base["_pid"] != "") & (base[C.COL_INT_CITY] != "") & (base[C.COL_INT_STATE] != "")]
    if base.empty:
        return

    first = (
        base.sort_values(C.COL_INT_DT)
        .drop_duplicates(subset=["_pid"])
        .loc[:, ["_pid", C.COL_INT_DT, C.COL_INT_CITY, C.COL_INT_STATE]]
        .rename(columns={C.COL_INT_DT: "first_dt"})
        .copy()
    )
    if first.empty:
        return

    first[C.COL_INT_REGION] = (
        first[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna("")
    )

    location_map: dict[tuple[str, str], tuple[float, float]] = {}
    for _, row in unique_locations.iterrows():
        c, s = str(row.get(C.COL_INT_CITY, "")).strip(), str(row.get(C.COL_INT_STATE, "")).strip()
        if c and s and (c, s) not in location_map:
            lat, lon = get_coords(c, s)
            if lat is not None and lon is not None:
                location_map[(c, s)] = (float(lat), float(lon))

    first["lat"] = first.apply(
        lambda r: location_map.get((r[C.COL_INT_CITY], r[C.COL_INT_STATE]), (None, None))[0],
        axis=1,
    )
    first["lon"] = first.apply(
        lambda r: location_map.get((r[C.COL_INT_CITY], r[C.COL_INT_STATE]), (None, None))[1],
        axis=1,
    )
    first = first.dropna(subset=["lat", "lon"]).copy()
    if first.empty:
        return

    first["frame_ts"] = pd.to_datetime(first["first_dt"]).dt.normalize()
    unique_days = first["frame_ts"].nunique()

    if unique_days <= 60:
        min_ts = first["frame_ts"].min()
        max_ts = first["frame_ts"].max()
        frames = pd.date_range(start=min_ts, end=max_ts, freq="D")
        first["frame_key"] = first["frame_ts"].dt.strftime("%Y-%m-%d")
        frame_keys = [d.strftime("%Y-%m-%d") for d in frames]
    else:
        first["frame_key"] = first["frame_ts"].dt.to_period("M").astype(str)
        start = first["frame_ts"].min().to_period("M")
        end = first["frame_ts"].max().to_period("M")
        frame_keys = [str(p) for p in pd.period_range(start=start, end=end, freq="M")]

    key_to_idx = {k: i for i, k in enumerate(frame_keys)}
    first["_frame_idx"] = first["frame_key"].map(key_to_idx).fillna(0).astype(int)

    frames_rows = []
    for i, k in enumerate(frame_keys):
        snap = first[first["_frame_idx"] <= i].copy()
        if snap.empty:
            continue
        snap["frame"] = k
        frames_rows.append(snap)

    if not frames_rows:
        return

    anim_df = pd.concat(frames_rows, ignore_index=True)
    anim_df["marker_size"] = 7

    st.markdown("### Linha do tempo de expansão geográfica")
    fig = px.scatter_mapbox(
        anim_df,
        lat="lat",
        lon="lon",
        animation_frame="frame",
        animation_group="_pid",
        color=C.COL_INT_REGION,
        size="marker_size",
        size_max=12,
        hover_name=C.COL_INT_CITY,
        hover_data={C.COL_INT_STATE: True, C.COL_INT_REGION: True, "first_dt": True, "lat": False, "lon": False},
        zoom=3,
        center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT},
        title="Parceiros aparecendo na data do primeiro contrato (acumulado)",
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        height=650,
        margin={"r": 0, "t": 35, "l": 0, "b": 0},
        legend_title_text="Região",
    )
    if fig.layout.updatemenus and len(fig.layout.updatemenus) > 0:
        try:
            fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 450
            fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 0
        except Exception:
            pass
    st.plotly_chart(fig, width="stretch")


def _voronoi_finite_polygons_2d(vor: Voronoi, radius: float | None = None):
    if vor.points.shape[1] != 2:
        raise ValueError("Voronoi supports only 2D input")

    new_regions: list[list[int]] = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = float(np.ptp(vor.points, axis=0).max()) * 2.0

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region_idx in enumerate(vor.point_region):
        vertices = vor.regions[region_idx]

        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges.get(p1, [])
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v1 >= 0 and v2 >= 0:
                continue
            if v1 < 0:
                v1, v2 = v2, v1

            t = vor.points[p2] - vor.points[p1]
            t = t / (t**2).sum() ** 0.5
            n = np.array([-t[1], t[0]])

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v1] + direction * radius

            new_vertices.append(far_point.tolist())
            new_region.append(len(new_vertices) - 1)

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = [v for _, v in sorted(zip(angles, new_region))]

        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)


def _clip_polygon_to_bbox(
    polygon: list[tuple[float, float]],
    bbox: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    min_x, min_y, max_x, max_y = bbox

    def clip(poly: list[tuple[float, float]], edge: str) -> list[tuple[float, float]]:
        if not poly:
            return []

        def inside(p: tuple[float, float]) -> bool:
            x, y = p
            if edge == "left":
                return x >= min_x
            if edge == "right":
                return x <= max_x
            if edge == "bottom":
                return y >= min_y
            return y <= max_y

        def intersect(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float]:
            x1, y1 = p1
            x2, y2 = p2
            if edge in ("left", "right"):
                x_edge = min_x if edge == "left" else max_x
                if x2 == x1:
                    return x_edge, y1
                t = (x_edge - x1) / (x2 - x1)
                return x_edge, y1 + t * (y2 - y1)
            y_edge = min_y if edge == "bottom" else max_y
            if y2 == y1:
                return x1, y_edge
            t = (y_edge - y1) / (y2 - y1)
            return x1 + t * (x2 - x1), y_edge

        output: list[tuple[float, float]] = []
        prev = poly[-1]
        for curr in poly:
            if inside(curr):
                if inside(prev):
                    output.append(curr)
                else:
                    output.append(intersect(prev, curr))
                    output.append(curr)
            else:
                if inside(prev):
                    output.append(intersect(prev, curr))
            prev = curr
        return output

    out = polygon
    for e in ("left", "right", "bottom", "top"):
        out = clip(out, e)
        if not out:
            return []
    return out


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    s = str(hex_color).lstrip("#")
    if len(s) != 6:
        return f"rgba(0,0,0,{alpha})"
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _color_to_rgba(color: str, alpha: float) -> str:
    c = str(color).strip()
    if c.startswith("rgb(") and c.endswith(")"):
        parts = c[4:-1].split(",")
        if len(parts) == 3:
            try:
                r = int(float(parts[0].strip()))
                g = int(float(parts[1].strip()))
                b = int(float(parts[2].strip()))
                return f"rgba({r},{g},{b},{alpha})"
            except Exception:
                return f"rgba(0,0,0,{alpha})"
    if c.startswith("#"):
        return _hex_to_rgba(c, alpha)
    if len(c) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in c):
        return _hex_to_rgba("#" + c, alpha)
    return f"rgba(0,0,0,{alpha})"


def _extract_outer_rings_from_geojson(geojson: Dict[str, Any]) -> list[list[tuple[float, float]]]:
    rings: list[list[tuple[float, float]]] = []
    for f in geojson.get("features") or []:
        geom = (f or {}).get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        if gtype == "Polygon":
            outer = coords[0] if coords and len(coords) > 0 else None
            if outer:
                rings.append([(float(x), float(y)) for x, y in outer])
        elif gtype == "MultiPolygon":
            for poly in coords:
                if not poly:
                    continue
                outer = poly[0] if len(poly) > 0 else None
                if outer:
                    rings.append([(float(x), float(y)) for x, y in outer])
    return rings


def _rings_bbox(rings: list[list[tuple[float, float]]]) -> tuple[float, float, float, float] | None:
    if not rings:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for ring in rings:
        for x, y in ring:
            xs.append(float(x))
            ys.append(float(y))
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _sample_boundary_points(
    rings: list[list[tuple[float, float]]],
    step: int,
    max_points: int,
) -> np.ndarray:
    pts: list[tuple[float, float]] = []
    for ring in rings:
        if not ring:
            continue
        pts.extend(ring[:: max(step, 1)])
        if len(pts) >= max_points:
            break
    if len(pts) > max_points:
        pts = pts[:max_points]
    return np.asarray(pts, dtype="float64")


def _point_in_ring(x: float, y: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    x1, y1 = ring[0]
    for i in range(1, n + 1):
        x2, y2 = ring[i % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1):
            inside = not inside
        x1, y1 = x2, y2
    return inside


def _point_in_any_ring(x: float, y: float, rings: list[list[tuple[float, float]]]) -> bool:
    for ring in rings:
        if _point_in_ring(x, y, ring):
            return True
    return False


def _haversine_km(
    lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    r = 6371.0
    lat1r = np.deg2rad(lat1)
    lon1r = np.deg2rad(lon1)
    lat2r = np.deg2rad(lat2)
    lon2r = np.deg2rad(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return r * c


def _render_voronoi_map(
    unique_locations: pd.DataFrame,
    signed_unique: pd.DataFrame,
    get_coords: Callable[[str, str], Tuple[float | None, float | None]],
) -> None:
    if not SCIPY_AVAILABLE or Voronoi is None:
        st.warning("Biblioteca 'scipy' não disponível para gerar Voronoi.")
        return

    base = signed_unique.copy()
    base[C.COL_INT_CITY] = base[C.COL_INT_CITY].astype(str).str.strip()
    base[C.COL_INT_STATE] = base[C.COL_INT_STATE].astype(str).str.strip()
    base = base[(base[C.COL_INT_CITY] != "") & (base[C.COL_INT_STATE] != "")]
    if base.empty:
        st.info("Sem dados suficientes para gerar Voronoi.")
        return

    if "_pid" not in base.columns:
        base["_pid"] = base[C.COL_INT_PARTNER].astype(str).str.strip()
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "", base[C.COL_INT_CEP].astype(str).str.strip()
        )
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "",
            base[C.COL_INT_CITY].astype(str).str.strip()
            + "|"
            + base[C.COL_INT_STATE].astype(str).str.strip(),
        )

    city_counts = (
        base.groupby([C.COL_INT_CITY, C.COL_INT_STATE])["_pid"]
        .nunique()
        .reset_index(name="parceiros")
    )
    if city_counts.empty:
        st.info("Sem dados suficientes para gerar Voronoi.")
        return

    location_map: dict[tuple[str, str], tuple[float, float]] = {}
    for _, row in unique_locations.iterrows():
        c, s = str(row.get(C.COL_INT_CITY, "")).strip(), str(row.get(C.COL_INT_STATE, "")).strip()
        if c and s:
            lat, lon = get_coords(c, s)
            if lat is not None and lon is not None:
                location_map[(c, s)] = (float(lat), float(lon))

    rows = []
    for _, r in city_counts.iterrows():
        key = (str(r[C.COL_INT_CITY]).strip(), str(r[C.COL_INT_STATE]).strip())
        if key in location_map:
            lat, lon = location_map[key]
            rows.append(
                {
                    "cidade": key[0],
                    "estado": key[1],
                    "parceiros": int(r["parceiros"]),
                    "lat": lat,
                    "lon": lon,
                }
            )

    if len(rows) < 3:
        st.info("Voronoi requer ao menos 3 pontos com coordenadas.")
        return

    pts = pd.DataFrame(rows)
    pts = pts.drop_duplicates(subset=["lat", "lon"]).copy()
    if len(pts) < 3:
        st.info("Voronoi requer ao menos 3 pontos distintos.")
        return

    states_geojson = _get_states_geojson()
    rings = _extract_outer_rings_from_geojson(states_geojson) if states_geojson else []
    bbox_from_states = _rings_bbox(rings)

    if bbox_from_states:
        min_lon, min_lat, max_lon, max_lat = bbox_from_states
        pad_lon = max((max_lon - min_lon) * 0.03, 0.5)
        pad_lat = max((max_lat - min_lat) * 0.03, 0.5)
        bbox = (min_lon - pad_lon, min_lat - pad_lat, max_lon + pad_lon, max_lat + pad_lat)
    else:
        bbox = (-74.0, -34.0, -34.0, 6.0)
        min_lon, min_lat, max_lon, max_lat = bbox

    boundary_pts = _sample_boundary_points(rings, step=25, max_points=900) if rings else np.empty((0, 2))
    partner_coords = pts[["lon", "lat"]].to_numpy(dtype="float64")
    if len(boundary_pts) > 0:
        all_coords = np.vstack([partner_coords, boundary_pts])
    else:
        all_coords = partner_coords

    vor = Voronoi(all_coords)
    radius = float(max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * 2.5)
    regions, vertices = _voronoi_finite_polygons_2d(vor, radius=radius)

    palette = px.colors.sequential.Blues
    min_v = float(pts["parceiros"].min())
    max_v = float(pts["parceiros"].max())
    denom = max(max_v - min_v, 1.0)

    features: list[dict[str, Any]] = []
    n_partners = len(pts)
    for i in range(n_partners):
        region = regions[i]
        poly = vertices[region]
        polygon = [(float(x), float(y)) for x, y in poly.tolist()]
        clipped = _clip_polygon_to_bbox(polygon, bbox)
        if len(clipped) < 3:
            continue

        if clipped[0] != clipped[-1]:
            clipped.append(clipped[0])

        count = int(pts.iloc[i]["parceiros"])
        t = (count - min_v) / denom
        idx = int(round(t * (len(palette) - 1)))
        idx = max(0, min(idx, len(palette) - 1))
        fill = _color_to_rgba(palette[idx], 0.28)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "cidade": str(pts.iloc[i]["cidade"]),
                    "estado": str(pts.iloc[i]["estado"]),
                    "parceiros": count,
                    "fill": fill,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[x, y] for x, y in clipped]],
                },
            }
        )

    if not features:
        st.info("Não foi possível gerar polígonos de Voronoi com os pontos disponíveis.")
        return

    gap_km = st.slider(
        "Cobertura inadequada se a distância ao parceiro mais próximo for ≥ (km)",
        min_value=50,
        max_value=800,
        value=250,
        step=10,
        key="voronoi_gap_km",
    )
    st.info("Mapa Voronoi pode levar alguns segundos, pois depende de geocodificação por cidade.")
    m = folium.Map(location=[C.MAP_LAT_DEFAULT, C.MAP_LON_DEFAULT], zoom_start=4, tiles="OpenStreetMap")
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    def style_fn(feature):
        props = feature.get("properties") or {}
        return {
            "fillColor": props.get("fill", "rgba(45,159,255,0.18)"),
            "color": "rgba(255,255,255,0.22)",
            "weight": 1,
            "fillOpacity": 1.0,
        }

    folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=["cidade", "estado", "parceiros"], aliases=["Cidade", "UF", "Parceiros"]),
        name="Voronoi",
    ).add_to(m)

    if states_geojson:
        folium.GeoJson(
            states_geojson,
            style_function=lambda x: {
                "fillColor": "rgba(0,0,0,0)",
                "color": "rgba(0,0,0,0.45)",
                "weight": 1,
                "fillOpacity": 0.0,
            },
            name="Brasil (UFs)",
        ).add_to(m)

    partners_lat = pts["lat"].to_numpy(dtype="float64")
    partners_lon = pts["lon"].to_numpy(dtype="float64")
    gap_points: list[tuple[float, float, float]] = []
    lat_grid = np.linspace(min_lat, max_lat, 55)
    lon_grid = np.linspace(min_lon, max_lon, 75)
    for lat in lat_grid:
        for lon in lon_grid:
            if rings and not _point_in_any_ring(float(lon), float(lat), rings):
                continue
            d = _haversine_km(float(lat), float(lon), partners_lat, partners_lon)
            md = float(np.min(d)) if d.size else 0.0
            if md >= float(gap_km):
                gap_points.append((float(lat), float(lon), md))

    if gap_points:
        if len(gap_points) > 900:
            gap_points = gap_points[:: max(len(gap_points) // 900, 1)]

        st.caption(f"Pontos sem cobertura adequada (amostra): {len(gap_points)}")
        for lat, lon, md in gap_points:
            folium.CircleMarker(
                location=[lat, lon],
                radius=2,
                color="rgba(255, 77, 77, 0.9)",
                fill=True,
                fill_opacity=0.45,
                weight=0,
                tooltip=f"Gap ~ {md:.0f} km",
            ).add_to(m)

    for _, r in pts.iterrows():
        folium.CircleMarker(
            location=[float(r["lat"]), float(r["lon"])],
            radius=4,
            color=C.COLOR_SECONDARY,
            fill=True,
            fill_opacity=0.9,
            tooltip=f"{r['cidade']} - {r['estado']} ({int(r['parceiros'])})",
        ).add_to(m)

    st_folium(m, width="100%", height=650, returned_objects=[])


def _render_region_state_city_sunburst(signed_unique: pd.DataFrame) -> None:
    if signed_unique.empty:
        return
    required = [C.COL_INT_STATE, C.COL_INT_CITY]
    if any(c not in signed_unique.columns for c in required):
        return

    base = signed_unique.copy()
    if C.COL_INT_REGION not in base.columns:
        base[C.COL_INT_REGION] = (
            base[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna("")
        )

    base[C.COL_INT_REGION] = base[C.COL_INT_REGION].astype(str).str.strip()
    base[C.COL_INT_STATE] = base[C.COL_INT_STATE].astype(str).str.strip()
    base[C.COL_INT_CITY] = base[C.COL_INT_CITY].astype(str).str.strip()

    base = base[
        (base[C.COL_INT_REGION] != "")
        & (base[C.COL_INT_STATE] != "")
        & (base[C.COL_INT_CITY] != "")
    ]
    if base.empty:
        return

    if "_pid" not in base.columns:
        base["_pid"] = base[C.COL_INT_PARTNER].astype(str).str.strip()
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "", base[C.COL_INT_CEP].astype(str).str.strip()
        )
        base["_pid"] = base["_pid"].where(
            base["_pid"] != "",
            base[C.COL_INT_CITY].astype(str).str.strip()
            + "|"
            + base[C.COL_INT_STATE].astype(str).str.strip(),
        )

    g = (
        base.groupby([C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CITY])["_pid"]
        .nunique()
        .reset_index(name=C.UI_LABEL_COL_PARTNERS)
    )
    if g.empty:
        return

    max_leaves = 1500
    if len(g) > max_leaves:
        st.info(
            f"Sunburst resumido para {max_leaves} cidades por performance."
        )
        g = g.sort_values(C.UI_LABEL_COL_PARTNERS, ascending=False).head(max_leaves)

    st.markdown("### Sunburst: Região → Estado → Cidade")
    fig = px.sunburst(
        g,
        path=[C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CITY],
        values=C.UI_LABEL_COL_PARTNERS,
        color=C.UI_LABEL_COL_PARTNERS,
        color_continuous_scale=["#fde8ef", "#e6165d"],
        title="Distribuição de Parceiros (Assinados) por Região/Estado/Cidade",
    )
    st.plotly_chart(fig, width="stretch")


def _render_city_search(signed_unique: pd.DataFrame) -> None:
    """
    Renders the city search functionality to check for partner presence.

    Args:
        signed_unique (pd.DataFrame): The dataframe containing unique signed contract locations.
    """
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
    """
    Renders distribution charts (by state, partners per state, city, region).

    Args:
        signed_unique (pd.DataFrame): The dataframe containing unique signed contract locations.
    """
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
    """
    Renders table of states without partners.

    Args:
        signed_unique (pd.DataFrame): The dataframe containing unique signed contract locations.
    """
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
    """
    Main render function for the Map Tab.

    Orchestrates the preparation of data, rendering of KPIs, maps (boundary or point),
    search functionality, and distribution charts.

    Args:
        df (pd.DataFrame): The input dataframe containing all contract data.
        get_ibge_code (Callable): Service function to get IBGE codes.
        get_municipality_geojson (Callable): Service function to get GeoJSON boundaries.
        get_coords (Callable): Service function to get lat/lon coordinates.
    """
    
    # 1. Prepare Data
    signed, signed_unique = _prepare_map_data(df)

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
    use_uf_choropleth = st.toggle(
        "Ativar Choropleth por UF (Densidade de Parceiros)",
        value=False,
        help="Coloriza cada UF pela quantidade de parceiros (ASSINADO).",
    )
    use_voronoi = st.toggle(
        "Ativar Voronoi de Cobertura Territorial",
        value=False,
        help="Divide o território em zonas de influência (mais próximo) usando pontos de cidades com parceiros.",
    )

    if use_voronoi:
        _render_voronoi_map(unique_locations, signed_unique, get_coords)
    elif use_uf_choropleth:
        _render_uf_choropleth(signed_unique)
    elif use_boundary_map:
        _render_boundary_map(unique_locations, get_ibge_code, get_municipality_geojson)
    else:
        _render_point_map(unique_locations, signed_unique, get_coords)

    _render_geo_expansion_timeline(signed, unique_locations, get_coords)
    _render_region_state_city_sunburst(signed_unique)
    st.divider()

    # 4. Render City Search
    _render_city_search(signed_unique)

    # 5. Render Distribution Charts
    _render_distribution_charts(signed_unique)

    # 6. Render Missing States Table
    _render_missing_states_table(signed_unique)
