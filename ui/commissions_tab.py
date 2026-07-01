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

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "team_categories_config.json"
)

def _load_team_categories():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar categorias: {e}")
    return dict(TEAM_CATEGORIES)

def _save_team_categories(categories):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erro ao salvar categorias: {e}")


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

def get_assignment_key(role_name: str) -> str:
    if role_name == "captador":
        return "captador_id"
    if role_name == "suporte_performance":
        return "suporte_id"
    return f"{role_name}_id"

def nominal_to_real(key, nominal_pct, categories, tax_pct, partner_pct):
    tax_rate = tax_pct / 100.0
    liquid_factor = (1.0 - partner_pct / 100.0) * (1.0 - tax_rate) * (11.66 / 13.50)
    return nominal_pct * liquid_factor

def real_to_nominal(key, real_pct, categories, tax_pct, partner_pct):
    tax_rate = tax_pct / 100.0
    liquid_factor = (1.0 - partner_pct / 100.0) * (1.0 - tax_rate) * (11.66 / 13.50)
    if liquid_factor <= 0.0001:
        return 0.0
    return real_pct / liquid_factor

def on_nominal_change(key, tax_pct, partner_pct):
    widget_key = f"pct_{key}"
    if widget_key in st.session_state:
        new_pct = st.session_state[widget_key]
        st.session_state["team_categories"][key]["percentage"] = new_pct
        _save_team_categories(st.session_state["team_categories"])
        
        # Keep real percentage in sync
        categories = st.session_state["team_categories"]
        st.session_state[f"real_pct_{key}"] = nominal_to_real(key, new_pct, categories, tax_pct, partner_pct)

def on_real_change(key, tax_pct, partner_pct):
    widget_key = f"real_pct_{key}"
    if widget_key in st.session_state:
        new_real = st.session_state[widget_key]
        categories = st.session_state["team_categories"]
        new_nominal = real_to_nominal(key, new_real, categories, tax_pct, partner_pct)
        
        st.session_state["team_categories"][key]["percentage"] = new_nominal
        _save_team_categories(st.session_state["team_categories"])
        st.session_state[f"pct_{key}"] = new_nominal
        st.session_state[f"real_pct_{key}"] = new_real


def _render_team_config(all_partners_list: list, tax_pct: float = 0.0, partner_pct: float = 50.0):
    with st.expander("Gestão de Equipe e Configurações", expanded=True, icon=":material/groups:"):
        # Initialize Session State
        if "team_members" not in st.session_state:
            st.session_state["team_members"] = []
        if "assignments" not in st.session_state:
            st.session_state["assignments"] = []
        if "team_categories" not in st.session_state:
            st.session_state["team_categories"] = _load_team_categories()

        tab_membros, tab_cargos = st.tabs([":material/person: Membros da Equipe", ":material/settings: Cargos e Porcentagens"])
        
        with tab_membros:
            # Layout: Add Member (Left) vs List Members (Right)
            col_form, col_list = st.columns([1, 2], gap="large")
            
            # 1. Add New Member Form
            with col_form:
                st.markdown("#### :material/person_add: Novo Membro")
                with st.container(border=True):
                    new_name = st.text_input("Nome do Membro")
                    
                    role_options = {k: v["name"] for k, v in st.session_state["team_categories"].items()}
                    selected_roles_keys = st.multiselect(
                        "Cargos",
                        options=list(role_options.keys()),
                        format_func=lambda x: role_options[x]
                    )
                    
                    if st.button("Adicionar Membro", use_container_width=True, icon=":material/add:"):
                        if new_name and selected_roles_keys:
                            new_id = 100  # Simple ID gen
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
                st.markdown("#### :material/badge: Membros da Equipe")
                
                name_to_partner_id = {str(p.get("name")): p.get("id") for p in all_partners_list}
                partner_id_to_name = {p.get("id"): str(p.get("name")) for p in all_partners_list}

                def _resolve_partner_id(value):
                    if value is None:
                        return None
                    if isinstance(value, int):
                        return value
                    if isinstance(value, str):
                        return name_to_partner_id.get(value)
                    return None

                # Build a map of current assignments by member and role
                current_assignments_map = {}
                for assign in st.session_state["assignments"]:
                    p_id = assign.get("partner_id")
                    for k, v in assign.items():
                        if k != "partner_id" and v is not None:
                            if v not in current_assignments_map:
                                current_assignments_map[v] = {}
                            if k not in current_assignments_map[v]:
                                current_assignments_map[v][k] = []
                            current_assignments_map[v][k].append(p_id)

                # Track taken partner IDs for each role key to prevent duplicate assignments
                taken_partner_ids_by_role = {}
                for assign in st.session_state["assignments"]:
                    p_id = assign.get("partner_id")
                    for k, v in assign.items():
                        if k != "partner_id" and v is not None:
                            if k not in taken_partner_ids_by_role:
                                taken_partner_ids_by_role[k] = set()
                            taken_partner_ids_by_role[k].add(p_id)

                def handle_copy_to_suporte(m_id, c_partners, all_partners):
                    target_partners = list(c_partners)
                    target_names = [p["name"] for p in all_partners if p["id"] in target_partners or p["name"] in target_partners]
                    st.session_state[f"role_suporte_performance_{m_id}"] = target_names
                    
                    for other_member in st.session_state.get("team_members", []):
                        other_id = other_member["id"]
                        if other_id != m_id:
                            other_sup_key = f"role_suporte_performance_{other_id}"
                            if other_sup_key in st.session_state:
                                st.session_state[other_sup_key] = [
                                    name for name in st.session_state[other_sup_key]
                                    if next((p["id"] for p in all_partners if p["name"] == name), name) not in target_partners
                                ]

                # Display Members
                members_to_remove = []
                
                if not st.session_state["team_members"]:
                    st.info("Nenhum membro cadastrado. Utilize o formulário ao lado para adicionar.")

                for idx, member in enumerate(st.session_state["team_members"]):
                    role_labels = [st.session_state["team_categories"].get(r, {'name': r})['name'] for r in member['roles']]
                    
                    with st.expander(f"{member['name']} ({', '.join(role_labels)})", expanded=False, icon=":material/person:"):
                        # --- Member Editing ---
                        st.markdown("##### :material/edit: Editar Membro")
                        col_edit_name, col_edit_roles = st.columns([1, 2])
                        edit_name = col_edit_name.text_input(
                            "Nome do Membro",
                            value=member["name"],
                            key=f"edit_name_val_{member['id']}"
                        )
                        role_options_edit = {k: v["name"] for k, v in st.session_state["team_categories"].items()}
                        edit_roles = col_edit_roles.multiselect(
                            "Cargos do Membro",
                            options=list(role_options_edit.keys()),
                            default=member["roles"],
                            format_func=lambda x: role_options_edit[x],
                            key=f"edit_roles_val_{member['id']}"
                        )
                        
                        if edit_name != member["name"] or set(edit_roles) != set(member["roles"]):
                            st.session_state["team_members"][idx]["name"] = edit_name
                            st.session_state["team_members"][idx]["roles"] = edit_roles
                            st.rerun()

                        st.divider()

                        # --- Assignments Logic ---
                        partner_roles = [
                            r for r in member.get("roles", [])
                            if st.session_state["team_categories"].get(r, {}).get("type") == "partner_based"
                        ]
                        
                        updated_assignments = False
                        
                        if partner_roles:
                            st.markdown("##### Atribuição de Parceiros")
                            ac_cols = st.columns(max(1, len(partner_roles)))
                            
                            for r_idx, role in enumerate(partner_roles):
                                role_info = st.session_state["team_categories"][role]
                                role_name = role_info["name"]
                                role_id_key = get_assignment_key(role)
                                
                                with ac_cols[r_idx]:
                                    st.caption(f":material/handshake: {role_name} de:")
                                    current_partners = current_assignments_map.get(member["id"], {}).get(role_id_key, [])
                                    default_options = [p["name"] for p in all_partners_list if p["id"] in current_partners or p["name"] in current_partners]
                                    current_ids = {p["id"] for p in all_partners_list if p["id"] in current_partners or p["name"] in current_partners}
                                    
                                    blocked_ids = taken_partner_ids_by_role.get(role_id_key, set()) - current_ids
                                    role_options = [
                                        p["name"] for p in all_partners_list
                                        if (p["id"] not in blocked_ids) or (p["id"] in current_ids)
                                    ]
                                    
                                    selected_partners_names = st.multiselect(
                                        f"Selecione Parceiros ({role_name})",
                                        options=role_options,
                                        default=default_options,
                                        key=f"role_{role}_{member['id']}",
                                        label_visibility="collapsed"
                                    )
                                    
                                    new_ids = [
                                        next((p["id"] for p in all_partners_list if p["name"] == name), name) 
                                        for name in selected_partners_names
                                    ]
                                    
                                    if set(new_ids) != set(current_partners):
                                        updated_assignments = True
                                        
                                    if role == "captador" and "suporte_performance" in partner_roles and current_partners:
                                        st.write("")
                                        st.button(
                                            "Copiar p/ Suporte",
                                            key=f"rep_sup_{member['id']}",
                                            icon=":material/arrow_forward:",
                                            use_container_width=True,
                                            on_click=handle_copy_to_suporte,
                                            args=(member["id"], current_partners, all_partners_list)
                                        )
                                        
                        if updated_assignments:
                            # Rebuild assignments list
                            new_global_assignments = {}
                            for p in all_partners_list:
                                new_global_assignments[p["id"]] = {"partner_id": p["id"]}
                                
                            for m in st.session_state["team_members"]:
                                m_id = m["id"]
                                for role in m.get("roles", []):
                                    role_info = st.session_state["team_categories"].get(role, {})
                                    if role_info.get("type") == "partner_based":
                                        role_id_key = get_assignment_key(role)
                                        widget_key = f"role_{role}_{m_id}"
                                        
                                        if widget_key in st.session_state:
                                            sel_partner_names = st.session_state[widget_key]
                                            for pname in sel_partner_names:
                                                pid = next((p["id"] for p in all_partners_list if p["name"] == pname), pname)
                                                if pid not in new_global_assignments:
                                                    new_global_assignments[pid] = {"partner_id": pid}
                                                new_global_assignments[pid][role_id_key] = m_id
                                                
                            final_assigns = []
                            for pid, assign in new_global_assignments.items():
                                keys = [k for k in assign.keys() if k != "partner_id" and assign[k] is not None]
                                if keys:
                                    final_assigns.append(assign)
                                    
                            st.session_state["assignments"] = final_assigns
                            st.rerun()

                        st.markdown("---")
                        if st.button("Remover Membro", key=f"del_{member['id']}", icon=":material/delete:"):
                            members_to_remove.append(idx)

                if members_to_remove:
                    for idx in sorted(members_to_remove, reverse=True):
                        del st.session_state["team_members"][idx]
                    st.rerun()

        with tab_cargos:
            st.markdown("#### :material/settings: Gerenciar Cargos")
            categories = st.session_state["team_categories"]
            
            # Initialize widget state values from config and keep real percentage synced on every run
            for k, role_info in list(categories.items()):
                nom_key = f"pct_{k}"
                real_key = f"real_pct_{k}"
                if nom_key not in st.session_state:
                    st.session_state[nom_key] = float(role_info["percentage"])
                st.session_state[real_key] = nominal_to_real(k, float(st.session_state[nom_key]), categories, tax_pct, partner_pct)

            col_add_role, col_list_roles = st.columns([1, 2], gap="large")
            
            with col_add_role:
                st.markdown("##### :material/add: Novo Cargo")
                with st.container(border=True):
                    new_role_name = st.text_input("Nome do Cargo", key="new_role_name")
                    new_role_type = st.selectbox(
                        "Tipo de Cálculo",
                        options=["fixed", "partner_based"],
                        format_func=lambda x: "Fixo (Pool 13%)" if x == "fixed" else "Baseado em Parceiro (Faturamento Individual)",
                        key="new_role_type"
                    )
                    new_role_pct = st.number_input(
                        "Porcentagem Bruta (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=1.0,
                        step=0.1,
                        format="%.1f",
                        key="new_role_pct"
                    )
                    
                    if st.button("Adicionar Cargo", use_container_width=True, icon=":material/add:"):
                        if new_role_name:
                            import unicodedata
                            import re
                            slug = unicodedata.normalize('NFKD', new_role_name).encode('ascii', 'ignore').decode('utf-8')
                            slug = re.sub(r'[^a-zA-Z0-9_]', '_', slug.lower().strip())
                            if not slug:
                                slug = "cargo_" + str(len(categories))
                            
                            original_slug = slug
                            counter = 1
                            while slug in categories:
                                slug = f"{original_slug}_{counter}"
                                counter += 1
                                
                            categories[slug] = {
                                "name": new_role_name,
                                "percentage": new_role_pct,
                                "type": new_role_type
                            }
                            st.session_state["team_categories"] = categories
                            _save_team_categories(categories)
                            st.success(f"Cargo '{new_role_name}' adicionado!")
                            st.rerun()
                        else:
                            st.error("Por favor, preencha o nome do cargo.")
                            
            with col_list_roles:
                st.markdown("##### :material/list: Cargos Cadastrados")
                
                roles_to_delete = []
                
                for key, role_info in list(categories.items()):
                    with st.container(border=True):
                        col_rname, col_rpct_nom, col_rpct_real, col_rtype, col_rdel = st.columns([2, 1.5, 1.5, 1.5, 1])
                        
                        col_rname.markdown(f"**{role_info['name']}**\n`({key})`")
                        
                        col_rpct_nom.number_input(
                            "Nominal (%)",
                            min_value=0.0,
                            max_value=100.0,
                            step=0.1,
                            format="%.1f",
                            key=f"pct_{key}",
                            on_change=on_nominal_change,
                            args=(key, tax_pct, partner_pct)
                        )
                        
                        col_rpct_real.number_input(
                            "Real Efetivo (%)",
                            min_value=0.0,
                            max_value=100.0,
                            step=0.01,
                            format="%.2f",
                            key=f"real_pct_{key}",
                            on_change=on_real_change,
                            args=(key, tax_pct, partner_pct)
                        )
                        
                        type_str = "Fixo" if role_info["type"] == "fixed" else "Baseado em Parceiro"
                        col_rtype.markdown(f"\nTipo: *{type_str}*")
                        
                        if col_rdel.button("Excluir", key=f"del_role_{key}", icon=":material/delete:", use_container_width=True):
                            roles_to_delete.append(key)
                
                # Totals general
                total_fixed_nom = sum(float(c["percentage"]) for c in categories.values() if c["type"] == "fixed")
                total_fixed_real = sum(nominal_to_real(k, float(c["percentage"]), categories, tax_pct, partner_pct) for k, c in categories.items() if c["type"] == "fixed")
                
                total_partner_nom = sum(float(c["percentage"]) for c in categories.values() if c["type"] == "partner_based")
                total_partner_real = sum(nominal_to_real(k, float(c["percentage"]), categories, tax_pct, partner_pct) for k, c in categories.items() if c["type"] == "partner_based")
                
                total_gen_nom = total_fixed_nom + total_partner_nom
                total_gen_real = total_fixed_real + total_partner_real
                
                st.markdown("---")
                st.markdown("##### :material/analytics: Totais Gerais dos Cargos")
                totals_html = f"""
                <div style="display: flex; gap: 15px; justify-content: space-between; margin-top: 10px; flex-wrap: wrap;">
                  <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
                    <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Cargos Fixos</div>
                    <div style="font-size: 1.15rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_fixed_nom:.1f}% <span style="font-size: 0.75rem; color: #8a8d9a; font-weight: normal;">Nominal</span></div>
                    <div style="font-size: 0.95rem; color: #10b981; margin-top: 3px; font-weight: 500;">Real: {total_fixed_real:.2f}%</div>
                  </div>
                  <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
                    <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Cargos de Parceiro</div>
                    <div style="font-size: 1.15rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_partner_nom:.1f}% <span style="font-size: 0.75rem; color: #8a8d9a; font-weight: normal;">Nominal</span></div>
                    <div style="font-size: 0.95rem; color: #10b981; margin-top: 3px; font-weight: 500;">Real: {total_partner_real:.2f}%</div>
                  </div>
                  <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
                    <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Total Geral</div>
                    <div style="font-size: 1.15rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_gen_nom:.1f}% <span style="font-size: 0.75rem; color: #8a8d9a; font-weight: normal;">Nominal</span></div>
                    <div style="font-size: 0.95rem; color: #10b981; margin-top: 3px; font-weight: 500;">Real: {total_gen_real:.2f}%</div>
                  </div>
                </div>
                """
                st.markdown(totals_html, unsafe_allow_html=True)
                st.write("")

                if roles_to_delete:
                    for k in roles_to_delete:
                        for m in st.session_state["team_members"]:
                            if k in m.get("roles", []):
                                m["roles"].remove(k)
                        del categories[k]
                        if f"pct_{k}" in st.session_state:
                            del st.session_state[f"pct_{k}"]
                        if f"real_pct_{k}" in st.session_state:
                            del st.session_state[f"real_pct_{k}"]
                    st.session_state["team_categories"] = categories
                    _save_team_categories(categories)
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
    tax_pct_val = summary.get("tax_rate", 0.30) * 100.0
    summary_data = [
        ["Métrica", "Valor"],
        ["Faturamento Total", f"R$ {summary['total_gross_revenue']:,.2f}"],
        ["Comissão Parceiros", f"R$ {summary['total_partners_commission']:,.2f}"],
        ["Base Restante (50%)", f"R$ {summary['team_base_value']:,.2f}"],
        [f"Imposto ({tax_pct_val:.1f}%)", f"R$ {summary.get('tax_value', 0.0):,.2f}"],
        ["Base Líquida (após Imposto)", f"R$ {summary.get('remaining_after_tax', 0.0):,.2f}"],
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
        
    # Initialize DB Data early
    if "db_partners" not in st.session_state:
        db_data = CommissionEngine.load_data_from_db(DB_PATH)
        if db_data["partners"]:
            st.session_state["db_partners"] = db_data["partners"]
        if "team_members" not in st.session_state:
            st.session_state["team_members"] = db_data.get("team_members", [])
        if "assignments" not in st.session_state:
            st.session_state["assignments"] = db_data.get("assignments", [])

    if "team_categories" not in st.session_state:
        st.session_state["team_categories"] = _load_team_categories()
        
    st.divider()

    # Tabs: Real Calculation vs Simulation
    tab_real, tab_sim = st.tabs(["Cálculo Real", "Simulação"])

    with tab_real:
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

        # Retrieve global tax rate
        global_tax_pct = st.session_state.get("global_tax_pct", 0.0)

        # Prepare Partners Data from DataFrame
        col_pct1, col_pct2 = st.columns(2)
        default_partner_pct = col_pct1.number_input("Porcentagem Padrão Parceiros (%)", value=50.0, step=5.0)
        tax_pct = col_pct2.number_input("Alíquota de Imposto (%)", value=global_tax_pct, step=1.0, key="com_tax_pct")
        # Keep global in sync if modified locally
        st.session_state["global_tax_pct"] = tax_pct
        
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
        
        all_partners_list = sorted(all_partners_list, key=lambda x: x["name"])

        _render_team_config(all_partners_list, tax_pct=tax_pct, partner_pct=default_partner_pct)

        st.write(f"Encontrados {len(partners_data_input)} parceiros com faturamento neste mês.")
        
        if st.button("Calcular Comissões", type="primary"):
            team_members = st.session_state.get("team_members", [])
            assignments = st.session_state.get("assignments", [])
            team_categories = st.session_state.get("team_categories", TEAM_CATEGORIES)
            
            result = CommissionEngine.calculate_commissions(
                partners_data=partners_data_input,
                team_members=team_members,
                assignments=assignments,
                tax_rate=tax_pct / 100.0,
                team_categories=team_categories
            )
            
            # Display Results
            summary = result["summary"]
            
            # 1. Summary Metrics
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Faturamento Total", f"R$ {summary['total_gross_revenue']:,.2f}")
            c2.metric("Comissão Parceiros", f"R$ {summary['total_partners_commission']:,.2f}")
            c3.metric(f"Imposto ({tax_pct:.1f}%)", f"R$ {summary.get('tax_value', 0.0):,.2f}")
            c4.metric("Comissão Equipe", f"R$ {summary['total_team_commission']:,.2f}")
            c5.metric("Líquido Final", f"R$ {summary['final_remaining_value']:,.2f}")
            
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
                    lambda roles: ", ".join([st.session_state.get("team_categories", TEAM_CATEGORIES).get(r, {"name": r})["name"] for r in roles]) 
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
                
            # 4. Export Reports
            st.subheader("Exportar Relatórios")
            col_pdf, col_xls_team, col_xls_partners = st.columns(3)
            
            # PDF
            pdf_bytes = _generate_pdf(result, selected_month.strftime("%B %Y"))
            col_pdf.download_button(
                label="Baixar PDF Completo",
                icon=":material/picture_as_pdf:",
                data=pdf_bytes,
                file_name=f"relatorio_comissoes_{selected_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            # Excel Team
            if result["team"]:
                buffer_team = io.BytesIO()
                df_team_xls = pd.DataFrame(result["team"])
                df_team_xls = df_team_xls[["name", "roles", "fixed_commission", "partner_commission", "total_commission"]]
                df_team_xls.columns = ["Nome", "Cargos", "Fixo (R$)", "Variável (R$)", "Total (R$)"]
                df_team_xls["Cargos"] = df_team_xls["Cargos"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
                
                # Total
                total_row = pd.DataFrame([{
                    "Nome": "TOTAL", "Cargos": "-", 
                    "Fixo (R$)": df_team_xls["Fixo (R$)"].sum(),
                    "Variável (R$)": df_team_xls["Variável (R$)"].sum(),
                    "Total (R$)": df_team_xls["Total (R$)"].sum()
                }])
                df_team_xls = pd.concat([df_team_xls, total_row], ignore_index=True)
                
                with pd.ExcelWriter(buffer_team, engine='openpyxl') as writer:
                    df_team_xls.to_excel(writer, index=False, sheet_name="Equipe")
                    
                col_xls_team.download_button(
                    label="Excel Equipe",
                    icon=":material/table_view:",
                    data=buffer_team.getvalue(),
                    file_name=f"relatorio_equipe_{selected_month.strftime('%Y_%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            # Excel Partners
            if result["partners"]:
                buffer_partners = io.BytesIO()
                df_partners_xls = pd.DataFrame(result["partners"])
                df_partners_xls = df_partners_xls[["name", "revenue", "commission_percentage", "commission_value"]]
                df_partners_xls.columns = ["Parceiro", "Faturamento", "%", "Comissão"]
                
                # Total
                total_row_p = pd.DataFrame([{
                    "Parceiro": "TOTAL", 
                    "Faturamento": df_partners_xls["Faturamento"].sum(),
                    "%": 0,
                    "Comissão": df_partners_xls["Comissão"].sum()
                }])
                df_partners_xls = pd.concat([df_partners_xls, total_row_p], ignore_index=True)
                
                with pd.ExcelWriter(buffer_partners, engine='openpyxl') as writer:
                    df_partners_xls.to_excel(writer, index=False, sheet_name="Parceiros")
                    
                col_xls_partners.download_button(
                    label="Excel Parceiros",
                    icon=":material/table_view:",
                    data=buffer_partners.getvalue(),
                    file_name=f"relatorio_parceiros_{selected_month.strftime('%Y_%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with tab_sim:
        st.subheader("Simulação de Faturamento")
        st.caption("Simule o ganho da equipe com base em um faturamento hipotético. "
                   "O cálculo considera os membros configurados acima.")
        
        global_tax_pct = st.session_state.get("global_tax_pct", 30.0)

        with st.container(border=True):
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            sim_revenue = sim_col1.number_input("Faturamento Simulado (R$)", value=100000.0, step=10000.0, format="%.2f")
            sim_partner_pct = sim_col2.number_input("Comissão Média Parceiros (%)", value=50.0, step=5.0)
            sim_tax_pct = sim_col3.number_input("Alíquota de Imposto (%)", value=global_tax_pct, step=1.0, key="sim_tab_tax_pct")
            
            st.divider()
            st.markdown("##### Atribuição de Responsáveis (Opcional)")
            st.caption("Defina quem seriam os responsáveis por esse faturamento simulado para calcular as comissões variáveis.")
            
            team_members = st.session_state.get("team_members", [])
            team_options = {m["id"]: m["name"] for m in team_members}
            
            sim_col3, sim_col4 = st.columns(2)
            
            sim_captador_id = sim_col3.selectbox(
                "Captador Responsável",
                options=[None] + list(team_options.keys()),
                format_func=lambda x: team_options[x] if x else "Nenhum / Distribuído"
            )
            
            sim_suporte_id = sim_col4.selectbox(
                "Suporte Responsável",
                options=[None] + list(team_options.keys()),
                format_func=lambda x: team_options[x] if x else "Nenhum / Distribuído"
            )

            if st.button("Simular Cenário", type="primary", icon=":material/science:"):
                # Create Fake Partner Data
                sim_partner_data = [{
                    "id": "SIM_PARTNER",
                    "name": "Parceiro Simulado",
                    "revenue": sim_revenue,
                    "commission_percentage": sim_partner_pct
                }]
                
                # Create Fake Assignment
                # Since calculate_commissions takes assignments list, we construct one
                sim_assignments = []
                if sim_captador_id:
                    sim_assignments.append({
                        "partner_id": "SIM_PARTNER",
                        "captador_id": sim_captador_id
                    })
                
                # If support is different or same, we need to merge or add
                if sim_suporte_id:
                    # Check if we already have an assignment for this partner
                    existing = next((a for a in sim_assignments if a["partner_id"] == "SIM_PARTNER"), None)
                    if existing:
                        existing["suporte_id"] = sim_suporte_id
                    else:
                        sim_assignments.append({
                            "partner_id": "SIM_PARTNER",
                            "suporte_id": sim_suporte_id
                        })
                
                team_categories = st.session_state.get("team_categories", TEAM_CATEGORIES)
                sim_result = CommissionEngine.calculate_commissions(
                    partners_data=sim_partner_data,
                    team_members=team_members,
                    assignments=sim_assignments,
                    tax_rate=sim_tax_pct / 100.0,
                    team_categories=team_categories
                )
                
                # Display Sim Results
                sim_summary = sim_result["summary"]
                
                # Metrics
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                sc1.metric("Faturamento Simulado", f"R$ {sim_summary['total_gross_revenue']:,.2f}")
                sc2.metric("Comissão Parceiros", f"R$ {sim_summary['total_partners_commission']:,.2f}")
                sc3.metric(f"Imposto ({sim_tax_pct:.1f}%)", f"R$ {sim_summary.get('tax_value', 0.0):,.2f}")
                sc4.metric("Comissão Equipe", f"R$ {sim_summary['total_team_commission']:,.2f}")
                sc5.metric("Líquido Final", f"R$ {sim_summary['final_remaining_value']:,.2f}")
                
                st.divider()
                st.subheader("Ganhos da Equipe (Simulação)")
                
                if sim_result["team"]:
                    sim_team_df = pd.DataFrame(sim_result["team"])
                    sim_display = sim_team_df[[
                        "name", "roles", "fixed_commission", "partner_commission", "total_commission"
                    ]].copy()
                    sim_display.columns = ["Nome", "Cargos", "Fixo (R$)", "Variável (R$)", "Total (R$)"]
                    
                    sim_display["Cargos"] = sim_display["Cargos"].apply(
                        lambda roles: ", ".join([st.session_state.get("team_categories", TEAM_CATEGORIES).get(r, {"name": r})["name"] for r in roles]) 
                        if isinstance(roles, list) else str(roles)
                    )
                    
                    # Add Total Row
                    s_total_fixo = sim_display["Fixo (R$)"].sum()
                    s_total_var = sim_display["Variável (R$)"].sum()
                    s_total_total = sim_display["Total (R$)"].sum()
                    
                    s_total_row = pd.DataFrame([{
                        "Nome": "TOTAL", "Cargos": "-", 
                        "Fixo (R$)": s_total_fixo, "Variável (R$)": s_total_var, "Total (R$)": s_total_total
                    }])
                    
                    sim_display_final = pd.concat([sim_display, s_total_row], ignore_index=True)
                    
                    st.dataframe(
                        sim_display_final.style.format({
                            "Fixo (R$)": "R$ {:,.2f}",
                            "Variável (R$)": "R$ {:,.2f}",
                            "Total (R$)": "R$ {:,.2f}"
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("Nenhum membro configurado para simulação.")
