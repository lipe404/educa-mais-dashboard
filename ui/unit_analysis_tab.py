import streamlit as st
import pandas as pd
import plotly.express as px
import os
import constants as C
from geocoding_service import GeocodingService
from services.opportunity import build_oportunidade_por_uf
from dotenv import load_dotenv

def render(dados_df: pd.DataFrame):
    st.header(C.TAB_NAME_UNIT_ANALYSIS)
    
    # --- Authentication ---
    if "unit_analysis_access" not in st.session_state:
        st.session_state["unit_analysis_access"] = False

    if not st.session_state["unit_analysis_access"]:
        st.info(C.UI_LABEL_ENTER_KEY_MSG)
        key = st.text_input(C.UI_LABEL_ACCESS_KEY, type="password", key="unit_analysis_access_key")
        if st.button("Acessar", key="btn_unit_access"):
            # Load env vars
            load_dotenv()
            real_key = os.getenv("KEY_API")
            
            if not real_key:
                st.error("Erro de configuração: KEY_API não definida no ambiente.")
                return

            if key == real_key:
                st.session_state["unit_analysis_access"] = True
                st.rerun()
            else:
                st.error("Chave de acesso inválida.")
        return

    # --- Main Content ---
    
    # 1. Partner Selection
    # Get unique partners sorted
    partners = sorted([str(p) for p in dados_df[C.COL_INT_PARTNER].unique() if p and str(p).strip()])
    
    if not partners:
        st.warning(C.UI_LABEL_NO_PARTNERS_FOUND)
        return

    col_sel, col_info = st.columns([1, 2])
    
    with col_sel:
        selected_partner = st.selectbox("Selecione o Parceiro", partners)
    
    # Get Partner Data
    partner_data = dados_df[dados_df[C.COL_INT_PARTNER] == selected_partner]
    if partner_data.empty:
        st.error("Dados do parceiro não encontrados.")
        return

    # Determine Base Location (Latest contract)
    partner_data_sorted = partner_data.sort_values(C.COL_INT_DT, ascending=False)
    latest_entry = partner_data_sorted.iloc[0]
    
    city = str(latest_entry.get(C.COL_INT_CITY, "")).strip()
    state = str(latest_entry.get(C.COL_INT_STATE, "")).strip()
    
    with col_info:
        st.markdown(f"### {selected_partner}")
        st.markdown(f" **Localização Base:** {city} - {state}")
        st.markdown(f" **Total de Contratos:** {len(partner_data)}")
    
    st.divider()

    # 2. AI Analysis Trigger
    st.markdown("####  Inteligência de Mercado")
    st.write("Utilize nossa IA para cruzar dados geográficos, demográficos e de contratos para gerar insights personalizados.")
    
    if st.button("✨ Gerar Análise Unitária (IA)"):
        if not city or not state:
            st.error("Cidade ou Estado não identificados para este parceiro.")
            return
            
        with st.spinner(f"Analisando contexto de {city}-{state} e buscando oportunidades..."):
            
            # A. Geolocation of Partner
            geo = GeocodingService()
            lat_p, lon_p = geo.get_coords(city, state)
            
            if not lat_p or not lon_p:
                st.error(f"Não foi possível geocodificar a cidade base: {city}-{state}")
                # Fallback to State center? No, user needs specific context.
            else:
                # B. Build Opportunity Context for the State
                opp_df = build_oportunidade_por_uf(dados_df, [state])
                
                # Filter: High score, not present
                # We want cities close to the partner?
                # Without distance matrix for all, we pick top score cities in the state 
                # and if possible, we could filter by proximity if we had coords for all.
                # For now, we show "Top Oportunidades no Estado" highlighting those with high population.
                
                opportunities = opp_df[opp_df["presenca"] == 0].sort_values("score", ascending=False).head(15)
                
                # C. Generate Insights
                st.markdown("###  Insights Estratégicos")
                
                # Metric 1: Local Market Saturation
                # Check if there are other partners in the same city
                partners_in_city = dados_df[
                    (dados_df[C.COL_INT_CITY] == city) & 
                    (dados_df[C.COL_INT_STATE] == state)
                ][C.COL_INT_PARTNER].nunique()
                
                saturation_msg = ""
                if partners_in_city > 1:
                    saturation_msg = f" **Alta Concorrência Local**: Existem {partners_in_city} parceiros atuando em {city}."
                else:
                    saturation_msg = " **Domínio Local**: Você é o único parceiro registrado nesta cidade."
                
                # Metric 2: State Potential
                total_pop_opp = opportunities["pop_2022"].sum()
                
                st.info(f"""
                **Análise de Perfil:**
                - {saturation_msg}
                - **Potencial de Expansão**: Identificamos **{len(opportunities)} cidades** prioritárias no estado com um público potencial de **{total_pop_opp:,.0f}** habitantes sem cobertura.
                """)
                
                # D. Map Visualization
                st.markdown("####  Mapa de Expansão Sugerida")
                
                map_data = []
                # Add Partner
                map_data.append({
                    "lat": lat_p, "lon": lon_p, "nome": f"BASE: {city}", 
                    "type": "Sua Base", "size": 15, "color": "blue"
                })
                
                # Geocode Opportunities
                progress_text = "Mapeando oportunidades próximas..."
                my_bar = st.progress(0, text=progress_text)
                
                valid_opps = 0
                for i, row in enumerate(opportunities.itertuples()):
                    # Simple limit to avoid long wait
                    if valid_opps >= 10: 
                        break
                        
                    o_city = row.nome
                    o_uf = row.uf
                    o_pop = row.pop_2022
                    
                    olat, olon = geo.get_coords(o_city, o_uf)
                    if olat and olon:
                        map_data.append({
                            "lat": olat, "lon": olon, 
                            "nome": f"{o_city} (Pop: {o_pop})", 
                            "type": "Oportunidade", "size": 10, "color": "green"
                        })
                        valid_opps += 1
                    
                    my_bar.progress((i + 1) / len(opportunities), text=progress_text)
                
                my_bar.empty()
                
                map_df = pd.DataFrame(map_data)
                
                if not map_df.empty:
                    fig = px.scatter_mapbox(
                        map_df, lat="lat", lon="lon", hover_name="nome", color="type", size="size",
                        color_discrete_map={"Sua Base": "#2d9fff", "Oportunidade": "#00ff7f"},
                        zoom=6, center={"lat": lat_p, "lon": lon_p},
                        title="Sua Base vs. Polos de Oportunidade"
                    )
                    fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
                    st.plotly_chart(fig, use_container_width=True)
                
                # E. Course Recommendations
                st.markdown("#### Cursos Recomendados para a Região")
                
                # Logic: If city pop > 100k, suggest technical/health. If < 50k, EJA/Agro.
                # Use the population of the Partner's city for local demand.
                # Need to find population of partner's city.
                
                # Try to find partner city pop in opp_df (it might be there with presenca=1)
                partner_city_pop_row = opp_df[
                    (opp_df["nome"] == city) & (opp_df["uf"] == state)
                ]
                
                # If not in opp_df (maybe filtered out?), fetch it?
                # opp_df usually contains all municipalities of the state.
                
                pop_val = 0
                if not partner_city_pop_row.empty:
                    pop_val = partner_city_pop_row.iloc[0]["pop_2022"]
                
                st.write(f"Baseado no perfil demográfico de **{city}** (Pop. est: {pop_val:,.0f}):")
                
                cols = st.columns(3)
                recommendations = []
                
                if pop_val > 100000:
                    recommendations = [
                        ("Técnico em Enfermagem", "Alta demanda em centros urbanos."),
                        ("Técnico em Radiologia", "Setor de saúde em expansão."),
                        ("Técnico em Administração", "Empresas locais necessitam de gestão.")
                    ]
                elif pop_val > 40000:
                    recommendations = [
                        ("Técnico em Vendas", "Comércio local ativo."),
                        ("Técnico em Farmácia", "Drogarias em expansão."),
                        ("EJA Médio", "Qualificação básica necessária.")
                    ]
                else:
                    recommendations = [
                        ("EJA Fundamental/Médio", "Alta demanda de regularização escolar."),
                        ("Técnico em Agropecuária", "Forte vocação regional."),
                        ("Agente Comunitário de Saúde", "Programas municipais.")
                    ]
                
                for idx, (course, reason) in enumerate(recommendations):
                    with cols[idx % 3]:
                        st.success(f"**{course}**\n\n_{reason}_")

                st.markdown("---")
                st.caption("Análise gerada automaticamente com base em dados do IBGE (Censo 2022) e histórico de vendas.")
