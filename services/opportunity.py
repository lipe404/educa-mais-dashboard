import requests
import pandas as pd
from typing import List, Dict
import streamlit as st

try:
    import constants as C
except Exception:
    C = None
import constants as C


IBGE_MUNICIPIOS_UF = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios?orderBy=nome"
SIDRA_POP_2022 = "https://apisidra.ibge.gov.br/values/t/6579/n6/{ids}/v/9324/p/last"
SIDRA_POP_2022_ALL = "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last"


@st.cache_data(ttl=86400, show_spinner=False)
def get_municipios_por_uf(uf: str) -> pd.DataFrame:
    try:
        r = requests.get(IBGE_MUNICIPIOS_UF.format(uf=uf), timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.DataFrame(columns=["id", "nome", "uf", "regiao"])

    rows: List[Dict] = []
    regiao = C.ESTADO_REGIAO.get(uf, "")
    for m in data:
        mid = str((m or {}).get("id", ""))
        nome = (m or {}).get("nome", "")
        rows.append({"id": mid, "nome": nome, "uf": uf, "regiao": regiao})
    return pd.DataFrame(rows)


@st.cache_data(ttl=86400, show_spinner=False)
def get_populacao_2022_municipios(ids: List[str]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame(columns=["id", "pop_2022"])
    batch = []
    for i in range(0, len(ids), 40):
        batch_ids = ids[i : i + 40]
        url = SIDRA_POP_2022.format(ids="|".join(batch_ids))
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            j = r.json()
            for row in j[1:]:
                batch.append(
                    {
                        "id": str(row.get("D1C", "")),
                        "pop_2022": int(float(row.get("V", 0))),
                    }
                )
        except Exception:
            for mid in batch_ids:
                try:
                    u = SIDRA_POP_2022.format(ids=mid)
                    rr = requests.get(u, timeout=15)
                    rr.raise_for_status()
                    jj = rr.json()
                    for row in jj[1:]:
                        batch.append(
                            {
                                "id": str(row.get("D1C", "")),
                                "pop_2022": int(float(row.get("V", 0))),
                            }
                        )
                except Exception:
                    continue
    return pd.DataFrame(batch)


@st.cache_data(ttl=86400, show_spinner=False)
def get_populacao_2022_all() -> pd.DataFrame:
    try:
        r = requests.get(SIDRA_POP_2022_ALL, timeout=30)
        r.raise_for_status()
        j = r.json()
        rows = []
        for row in j[1:]:
            rows.append(
                {"id": str(row.get("D1C", "")), "pop_2022": int(float(row.get("V", 0)))}
            )
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["id", "pop_2022"])


@st.cache_data(ttl=86400, show_spinner=False)
def get_municipios_por_uf_simple(uf: str) -> pd.DataFrame:
    try:
        r = requests.get(IBGE_MUNICIPIOS_UF.format(uf=uf), timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.DataFrame(columns=["id", "nome", "uf", "regiao"])

    if not isinstance(data, list):
        return pd.DataFrame(columns=["id", "nome", "uf", "regiao"])

    regiao = C.ESTADO_REGIAO.get(uf, "") if C is not None else ""
    rows: List[Dict] = []
    for m in data:
        mid = str((m or {}).get("id", ""))
        nome = (m or {}).get("nome", "")
        rows.append({"id": mid, "nome": nome, "uf": uf, "regiao": regiao})
    return pd.DataFrame(rows, columns=["id", "nome", "uf", "regiao"])


def build_oportunidade_por_uf(
    dados_df: pd.DataFrame, selected_ufs: List[str]
) -> pd.DataFrame:
    presentes = (
        dados_df[["_cidade", "_estado"]]
        .dropna()
        .assign(
            key=lambda d: d["_cidade"].astype(str).str.strip().str.upper()
            + "|"
            + d["_estado"].astype(str).str.strip().str.upper()
        )
    )
    presentes_keys = set(presentes["key"].unique().tolist())

    frames = []
    pop_all = get_populacao_2022_all()
    pop_all = pop_all if not pop_all.empty else None
    for uf in selected_ufs:
        mun = get_municipios_por_uf_simple(uf)
        if mun.empty or "id" not in mun.columns:
            continue
        if pop_all is not None:
            df = mun.merge(pop_all, on="id", how="left")
        else:
            pop = get_populacao_2022_municipios(mun["id"].astype(str).tolist())
            df = mun.merge(pop, on="id", how="left")
        df["pop_2022"] = df["pop_2022"].fillna(0).astype(int)
        df["presenca"] = df.apply(
            lambda r: (
                1
                if (str(r["nome"]).strip().upper() + "|" + str(r["uf"]).strip().upper())
                in presentes_keys
                else 0
            ),
            axis=1,
        )
        df["score"] = df["pop_2022"].astype(float) * (1 - df["presenca"])
        frames.append(df)
    out = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(
            columns=["id", "nome", "uf", "regiao", "pop_2022", "presenca", "score"]
        )
    )
    return out.sort_values(["uf", "score"], ascending=[True, False])
