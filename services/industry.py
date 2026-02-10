import requests
import pandas as pd
from typing import List, Dict
import streamlit as st


AGREGADO_CEMPRE = "1685"
AGREGADOS_VARIAVEIS = "https://servicodados.ibge.gov.br/api/v3/agregados/{ag}/variaveis"
SIDRA_VALUES = "https://apisidra.ibge.gov.br/values/t/{t}/n6/{ids}/v/{v}/p/last"


@st.cache_data(ttl=86400, show_spinner=False)
def get_variable_id_by_name(agregado: str, contains: str) -> str | None:
    try:
        url = AGREGADOS_VARIAVEIS.format(ag=agregado)
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        vars = r.json()
        for v in vars:
            nome = str(v.get("nome", ""))
            vid = str(v.get("id", ""))
            if contains.lower() in nome.lower():
                return vid
        return None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def get_cnae_sections() -> Dict[str, str]:
    """
    Returns a map of 'Letter Description' -> 'Category ID' for CNAE 2.0 Sections.
    Currently returns empty dict because Table 1685 metadata is flaky.
    Code kept for interface compatibility but logic disabled.
    """
    return {}


@st.cache_data(ttl=86400, show_spinner=False)
def get_unidades_locais(ids: List[str], cnae_cat_id: str = "all") -> pd.DataFrame:
    """
    Fetches local units for given municipalities.
    If cnae_cat_id is provided but fails (or is 'all'), fetches TOTAL units.
    """
    if not ids:
        return pd.DataFrame(columns=["id", "unidades_locais"])

    var_id = get_variable_id_by_name(AGREGADO_CEMPRE, "Unidades locais")
    if not var_id:
        return pd.DataFrame(columns=["id", "unidades_locais"])

    rows: List[Dict] = []

    # We ignore cnae_cat_id for now because without valid metadata we can't reliably build queries.
    # Future: Re-enable classif_param if we find static IDs for CNAE Sections.

    for i in range(0, len(ids), 40):
        batch_ids = ids[i : i + 40]
        # Standard query = Total Local Units (All Categories)
        url = SIDRA_VALUES.format(t=AGREGADO_CEMPRE, ids="|".join(batch_ids), v=var_id)

        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            j = r.json()
            for row in j[1:]:
                rows.append(
                    {
                        "id": str(row.get("D1C", "")),
                        "unidades_locais": int(float(row.get("V", 0))),
                    }
                )
        except Exception:
            continue
    return pd.DataFrame(rows)
