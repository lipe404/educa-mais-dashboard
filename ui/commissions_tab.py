import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import constants as C
from services.commission import CommissionEngine, TEAM_CATEGORIES
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "auto-comissao",
    "instance",
    "commission_system.db",
)

def _check_authentication(access_key: str) -> bool:
    """
    Handles access control for the Commissions tab by verifying the provided access key.

    Args:
        access_key (str): The expected correct access key.

    Returns:
        bool: True if the user enters the correct key, False otherwise.
    """
    key = st.text_input(
        C.UI_LABEL_ACCESS_KEY, type="password", key="commissions_access_key"
    )
    if key != access_key:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return False
    return True


# Default Team Config (for first run)
DEFAULT_TEAM_CONFIG = [
    {
        "id": 1,
        "name": "Membro Exemplo 1",
        "roles": ["gerente_expansao"]
    },
    {
        "id": 2,
        "name": "Membro Exemplo 2",
        "roles": ["captador"]
    }
]

def _get_available_months(df: pd.DataFrame) -> list:
    if df.empty or C.COL_INT_DATA not in df.columns:
        return []
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df[C.COL_INT_DATA]):
        df[C.COL_INT_DATA] = pd.to_datetime(df[C.COL_INT_DATA], errors="coerce")
    
    dates = df[C.COL_INT_DATA].dropna().dt.to_period("M").unique()
    return sorted([d.to_timestamp() for d in dates], reverse=True)

def _render_team_config(all_partners_list: list):
    with st.expander("👥 Gestão de Equipe e Configurações", expanded=True):
        # Initialize Session State
        if "team_members" not in st.session_state:
            st.session_state["team_members"] = []
        if "assignments" not in st.session_state:
            st.session_state["assignments"] = []

        # Layout: Add Member (Left) vs List Members (Right)
        col_form, col_list = st.columns([1, 2], gap="large")
        
        # 1. Add New Member Form
        with col_form:
            st.markdown("#### ➕ Novo Membro")
            with st.container(border=True):
                new_name = st.text_input("Nome do Membro")
                
                role_options = {k: v["name"] for k, v in TEAM_CATEGORIES.items()}
                selected_roles_keys = st.multiselect(
                    "Cargos",
                    options=list(role_options.keys()),
                    format_func=lambda x: role_options[x]
                )
                
                if st.button("Adicionar Membro", use_container_width=True):
                    if new_name and selected_roles_keys:
                        new_id = len(st.session_state["team_members"]) + 100  # Simple ID gen
                        # Check for max ID to avoid collisions if loaded from DB
                        existing_ids = [m.get("id", 0) for m in st.session_state["team_members"]]
                        if existing_ids:
                            new_id = max(existing_ids) + 1
                            
                        st.session_state["team_members"].append({
                            "id": new_id,
                            "name": new_name,
                            "roles": selected_roles_keys
                        })
                        st.rerun()
                    else:
                        st.error("Preencha nome e selecione pelo menos um cargo.")

        # 2. List Members and Assignments
        with col_list:
            st.markdown("#### 📋 Membros da Equipe")
            
            # We need to manage assignments in a Member-Centric way for UI, 
            # but store/convert to Partner-Centric for logic.
            current_assignments_map = {} 
            for assign in st.session_state["assignments"]:
                p_id = assign.get("partner_id")
                c_id = assign.get("captador_id")
                s_id = assign.get("suporte_id")
                
                if c_id:
                    if c_id not in current_assignments_map: current_assignments_map[c_id] = {}
                    if "captador" not in current_assignments_map[c_id]: current_assignments_map[c_id]["captador"] = []
                    current_assignments_map[c_id]["captador"].append(p_id)
                    
                if s_id:
                    if s_id not in current_assignments_map: current_assignments_map[s_id] = {}
                    if "suporte_performance" not in current_assignments_map[s_id]: current_assignments_map[s_id]["suporte_performance"] = []
                    current_assignments_map[s_id]["suporte_performance"].append(p_id)

            # Display Members
            members_to_remove = []
            
            if not st.session_state["team_members"]:
                st.info("Nenhum membro cadastrado. Utilize o formulário ao lado para adicionar.")

            for idx, member in enumerate(st.session_state["team_members"]):
                role_labels = [TEAM_CATEGORIES.get(r, {'name': r})['name'] for r in member['roles']]
                
                with st.expander(f"👤 {member['name']} ({', '.join(role_labels)})", expanded=False):
                    
                    # Roles Editing (Simplified: just Delete for now, or re-add)
                    # Assignments Logic
                    has_captador = "captador" in member["roles"]
                    has_suporte = "suporte_performance" in member["roles"]
                    
                    updated_assignments = False
                    
                    # Layout for assignments
                    ac1, ac2 = st.columns(2)
                    
                    with ac1:
                        if has_captador:
                            st.caption("📢 Captador de:")
                            current_partners = current_assignments_map.get(member["id"], {}).get("captador", [])
                            default_options = [p["name"] for p in all_partners_list if p["id"] in current_partners or p["name"] in current_partners]
                            
                            selected_partners_names = st.multiselect(
                                "Selecione Parceiros (Captador)",
                                options=[p["name"] for p in all_partners_list],
                                default=default_options,
                                key=f"capt_{member['id']}",
                                label_visibility="collapsed"
                            )
                            
                            new_ids = [
                                next((p["id"] for p in all_partners_list if p["name"] == name), name) 
                                for name in selected_partners_names
                            ]
                            
                            if set(new_ids) != set(current_partners):
                                if member["id"] not in current_assignments_map: current_assignments_map[member["id"]] = {}
                                current_assignments_map[member["id"]]["captador"] = new_ids
                                updated_assignments = True
                    
                    with ac2:
                        if has_suporte:
                            st.caption("🤝 Suporte de:")
                            current_partners = current_assignments_map.get(member["id"], {}).get("suporte_performance", [])
                            default_options = [p["name"] for p in all_partners_list if p["id"] in current_partners or p["name"] in current_partners]
                            
                            selected_partners_names = st.multiselect(
                                "Selecione Parceiros (Suporte)",
                                options=[p["name"] for p in all_partners_list],
                                default=default_options,
                                key=f"sup_{member['id']}",
                                label_visibility="collapsed"
                            )
                            
                            new_ids = [
                                next((p["id"] for p in all_partners_list if p["name"] == name), name) 
                                for name in selected_partners_names
                            ]
                            
                            if set(new_ids) != set(current_partners):
                                if member["id"] not in current_assignments_map: current_assignments_map[member["id"]] = {}
                                current_assignments_map[member["id"]]["suporte_performance"] = new_ids
                                updated_assignments = True

                    if updated_assignments:
                        # Rebuild global assignments list from map
                        new_global_assignments = {}
                        for m_id, roles_map in current_assignments_map.items():
                            for p_id in roles_map.get("captador", []):
                                if p_id not in new_global_assignments: new_global_assignments[p_id] = {"partner_id": p_id}
                                new_global_assignments[p_id]["captador_id"] = m_id
                            for p_id in roles_map.get("suporte_performance", []):
                                if p_id not in new_global_assignments: new_global_assignments[p_id] = {"partner_id": p_id}
                                new_global_assignments[p_id]["suporte_id"] = m_id
                        
                        st.session_state["assignments"] = list(new_global_assignments.values())

                    st.markdown("---")
                    if st.button("❌ Remover Membro", key=f"del_{member['id']}"):
                        members_to_remove.append(idx)

            if members_to_remove:
                for idx in sorted(members_to_remove, reverse=True):
                    del st.session_state["team_members"][idx]
                st.rerun()

def _generate_pdf(report_data: dict, month_str: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(f"Relatório de Comissões - {month_str}", styles['Title']))
    elements.append(Spacer(1, 20))
    
    # Summary Table
    summary = report_data["summary"]
    summary_data = [
        ["Métrica", "Valor"],
        ["Faturamento Total", f"R$ {summary['total_gross_revenue']:,.2f}"],
        ["Comissão Parceiros", f"R$ {summary['total_partners_commission']:,.2f}"],
        ["Base para Equipe", f"R$ {summary['team_base_value']:,.2f}"],
        ["Comissão Fixa Equipe", f"R$ {summary['total_fixed_commission']:,.2f}"],
        ["Comissão Variável Equipe", f"R$ {summary['total_partner_based_commission']:,.2f}"],
        ["Total Equipe", f"R$ {summary['total_team_commission']:,.2f}"],
        ["Líquido Final", f"R$ {summary['final_remaining_value']:,.2f}"],
    ]
    
    t_summary = Table(summary_data, colWidths=[200, 150])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 20))
    
    # Team Details
    elements.append(Paragraph("Detalhamento da Equipe", styles['Heading2']))
    team_header = ["ID", "Nome", "Cargos", "Fixa (R$)", "Variável (R$)", "Total (R$)"]
    team_rows = []
    for m in report_data["team"]:
        roles_str = ", ".join(m["roles"])
        team_rows.append([
            str(m["member_id"]),
            m["name"],
            roles_str,
            f"R$ {m['fixed_commission']:,.2f}",
            f"R$ {m['partner_commission']:,.2f}",
            f"R$ {m['total_commission']:,.2f}"
        ])
    
    t_team = Table([team_header] + team_rows, colWidths=[30, 150, 200, 80, 80, 80])
    t_team.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(t_team)
    
    # Partners Details
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Detalhamento dos Parceiros", styles['Heading2']))
    partner_header = ["Parceiro", "Faturamento (R$)", "%", "Comissão (R$)"]
    partner_rows = []
    for p in report_data["partners"]:
        partner_rows.append([
            p["name"],
            f"R$ {p['revenue']:,.2f}",
            f"{p['commission_percentage']}%",
            f"R$ {p['commission_value']:,.2f}"
        ])
        
    t_partners = Table([partner_header] + partner_rows, colWidths=[250, 100, 50, 100])
    t_partners.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_partners)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def render(dados_df: pd.DataFrame, access_key: str):
    st.header("Cálculo de Comissões")
    
    if not _check_authentication(access_key):
        return
        
    # Initialize DB Data and Team Config early
    if "db_partners" not in st.session_state:
        db_data = CommissionEngine.load_data_from_db(DB_PATH)
        if db_data["partners"]:
            st.session_state["db_partners"] = db_data["partners"]
    
    # Prepare global partners list for Team Config (DB + potentially from DF later)
    # At this stage, we only have DB partners guaranteed
    db_partners = st.session_state.get("db_partners", {})
    all_partners_list = [{"id": p["id"], "name": p["name"]} for p in db_partners.values()]
    
    # If we have DataFrame data, we can merge unique partners from it (but we don't have month selected yet)
    # Ideally, we should list all unique partners from the whole DataFrame too
    if not dados_df.empty and C.COL_INT_PARTNER in dados_df.columns:
        df_unique_partners = dados_df[C.COL_INT_PARTNER].dropna().unique()
        for p_name in df_unique_partners:
            # Avoid duplicates by name (if name matches DB partner name)
            if p_name not in db_partners:
                # Add if not in DB list already (by ID/Name check?)
                # Since we used p_name as key for DB map, this check is efficient
                all_partners_list.append({"id": p_name, "name": p_name})
    
    # Sort for UI
    all_partners_list = sorted(all_partners_list, key=lambda x: x["name"])
    
    # Render Team Config Sidebar ALWAYS
    _render_team_config(all_partners_list)
    
    st.divider()
    
    # Filter Data
    months = _get_available_months(dados_df)
    if not months:
        st.warning("Sem dados de data disponíveis.")
        return

    selected_month = st.selectbox(
        "Selecione o Mês de Referência",
        months,
        format_func=lambda x: x.strftime("%B %Y")
    )
    
    # Filter DataFrame for selected month
    mask = (dados_df[C.COL_INT_DATA].dt.month == selected_month.month) & \
           (dados_df[C.COL_INT_DATA].dt.year == selected_month.year)
    df_filtered = dados_df[mask]
    
    if df_filtered.empty:
        st.info("Nenhum dado financeiro para o mês selecionado.")
        return

    # Prepare Partners Data from DataFrame
    default_partner_pct = st.number_input("Porcentagem Padrão Parceiros (%)", value=50.0, step=5.0)
    
    # Grouping
    partner_groups = df_filtered.groupby(C.COL_INT_PARTNER)[C.COL_INT_VALOR].sum().reset_index()
    
    # Get DB partners for lookup
    db_partners = st.session_state.get("db_partners", {})
    
    partners_data_input = []
    
    # Helper list for UI dropdowns
    all_partners_list = []
    
    for _, row in partner_groups.iterrows():
        p_name = row[C.COL_INT_PARTNER]
        if not p_name or str(p_name).strip() == "":
            continue
            
        # Defaults
        p_id = p_name
        p_pct = default_partner_pct
        
        # Lookup in DB
        if p_name in db_partners:
            p_data = db_partners[p_name]
            p_id = p_data["id"]
            p_pct = p_data["percentage"]
            
        partners_data_input.append({
            "id": p_id, 
            "name": p_name,
            "revenue": float(row[C.COL_INT_VALOR]),
            "commission_percentage": p_pct
        })
        
        all_partners_list.append({"id": p_id, "name": p_name})
    
    # Sort for UI
    # all_partners_list = sorted(all_partners_list, key=lambda x: x["name"]) # Already sorted above and passed to config

    # Render Sidebar with updated list
    # _render_team_config(all_partners_list) # Moved to top

    st.write(f"Encontrados {len(partners_data_input)} parceiros com faturamento neste mês.")
    
    if st.button("Calcular Comissões", type="primary"):
        # Run Calculation
        team_members = st.session_state.get("team_members", [])
        assignments = st.session_state.get("assignments", [])
        
        result = CommissionEngine.calculate_commissions(
            partners_data=partners_data_input,
            team_members=team_members,
            assignments=assignments
        )
        
        # Display Results
        summary = result["summary"]
        
        # 1. Summary Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faturamento Total", f"R$ {summary['total_gross_revenue']:,.2f}")
        c2.metric("Comissão Parceiros", f"R$ {summary['total_partners_commission']:,.2f}")
        c3.metric("Comissão Equipe", f"R$ {summary['total_team_commission']:,.2f}")
        c4.metric("Líquido Final", f"R$ {summary['final_remaining_value']:,.2f}")
        
        st.divider()
        
        # 2. Team Table
        st.subheader("Equipe")
        if result["team"]:
            team_df = pd.DataFrame(result["team"])
            # Format columns
            display_team = team_df[[
                "name", "roles", "fixed_commission", "partner_commission", "total_commission"
            ]].copy()
            display_team.columns = ["Nome", "Cargos", "Fixo (R$)", "Variável (R$)", "Total (R$)"]
            
            # Convert roles list to string to avoid PyArrow error (cannot mix list and string)
            # And also use friendly names
            display_team["Cargos"] = display_team["Cargos"].apply(
                lambda roles: ", ".join([TEAM_CATEGORIES.get(r, {"name": r})["name"] for r in roles]) 
                if isinstance(roles, list) else str(roles)
            )
            
            # Add Total Row
            total_fixo = display_team["Fixo (R$)"].sum()
            total_var = display_team["Variável (R$)"].sum()
            total_total = display_team["Total (R$)"].sum()
            
            # Create a total row DataFrame
            total_row = pd.DataFrame([{
                "Nome": "TOTAL",
                "Cargos": "-",
                "Fixo (R$)": total_fixo,
                "Variável (R$)": total_var,
                "Total (R$)": total_total
            }])
            
            # Concatenate
            display_team_final = pd.concat([display_team, total_row], ignore_index=True)
            
            # Format for display (optional: format as string with R$)
            # But st.dataframe handles floats well. Let's formatting just for final view
            # Or keep as floats for sorting.
            # User asked for a row with sum total.
            
            st.dataframe(
                display_team_final.style.format({
                    "Fixo (R$)": "R$ {:,.2f}",
                    "Variável (R$)": "R$ {:,.2f}",
                    "Total (R$)": "R$ {:,.2f}"
                }), 
                use_container_width=True
            )
        else:
            st.info("Nenhum membro da equipe configurado.")
            
        # 3. Partners Table
        st.subheader("Parceiros")
        if result["partners"]:
            partners_res_df = pd.DataFrame(result["partners"])
            display_partners = partners_res_df[[
                "name", "revenue", "commission_percentage", "commission_value"
            ]].copy()
            display_partners.columns = ["Parceiro", "Faturamento", "%", "Comissão"]
            
            # Total Row
            total_fat = display_partners["Faturamento"].sum()
            total_com = display_partners["Comissão"].sum()
            
            total_row_p = pd.DataFrame([{
                "Parceiro": "TOTAL",
                "Faturamento": total_fat,
                "%": "-",
                "Comissão": total_com
            }])
            
            display_partners_final = pd.concat([display_partners, total_row_p], ignore_index=True)
            
            st.dataframe(
                display_partners_final.style.format({
                    "Faturamento": "R$ {:,.2f}",
                    "Comissão": "R$ {:,.2f}",
                    "%": lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else str(x)
                }),
                use_container_width=True
            )
            
        # 4. PDF Export
        pdf_bytes = _generate_pdf(result, selected_month.strftime("%B %Y"))
        st.download_button(
            label="📄 Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=f"relatorio_comissoes_{selected_month.strftime('%Y_%m')}.pdf",
            mime="application/pdf"
        )
