from typing import List, Dict, Any, Optional
import pandas as pd
import json
import sqlite3
import os

# Constants mirrored from TypeScript
TEAM_CATEGORIES = {
    "gerente_expansao": {
        "name": "Gerente de Expansão",
        "percentage": 3.0,
        "type": "fixed",
    },
    "coordenador_suporte": {
        "name": "Coordenador/Suporte Administrativo",
        "percentage": 2.5,
        "type": "fixed",
    },
    "gestor_tecnologia": {
        "name": "Gestor de Tecnologia",
        "percentage": 1.5,
        "type": "fixed",
    },
    "gestor_trafego": {
        "name": "Gestor de Tráfego",
        "percentage": 1.0,
        "type": "fixed",
    },
    "designer": {"name": "Designer", "percentage": 1.0, "type": "fixed"},
    "captador": {"name": "Captador", "percentage": 1.0, "type": "partner_based"},
    "suporte_performance": {
        "name": "Suporte de Performance",
        "percentage": 3.0,
        "type": "partner_based",
    },
}

MAX_FIXED_TEAM_PERCENTAGE = 13.0


class CommissionEngine:
    """
    Engine to calculate commissions based on the logic from auto-comissao.
    """

    @staticmethod
    def load_data_from_db(db_path: str) -> Dict[str, Any]:
        """
        Loads team members, partners, and assignments from the SQLite database.
        """
        if not os.path.exists(db_path):
            return {"partners": {}, "team_members": [], "assignments": []}
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Load Partners
        # Schema assumption: table 'partners' (id, name, commission_percentage, ...)
        partners_map = {}
        try:
            cursor.execute("SELECT id, name, commission_percentage FROM partners WHERE active = 1")
            for row in cursor.fetchall():
                partners_map[row["name"]] = {
                    "id": row["id"],
                    "name": row["name"],
                    "percentage": row["commission_percentage"]
                }
        except Exception as e:
            print(f"Error loading partners: {e}")

        # 2. Load Team Members
        # Schema assumption: table 'expansion_team_members' (id, name, categories, active)
        team_members = []
        try:
            cursor.execute("SELECT id, name, categories FROM expansion_team_members WHERE active = 1")
            for row in cursor.fetchall():
                try:
                    roles = json.loads(row["categories"])
                except:
                    roles = []
                
                team_members.append({
                    "id": row["id"],
                    "name": row["name"],
                    "roles": roles
                })
        except Exception as e:
            print(f"Error loading team members: {e}")
            
        # 3. Load Assignments
        # Schema assumption: table 'member_partner_assignments' (member_id, partner_id, category)
        assignments_map = {} # partner_id -> {partner_id, captador_id, suporte_id}
        try:
            cursor.execute("SELECT member_id, partner_id, category FROM member_partner_assignments")
            for row in cursor.fetchall():
                p_id = row["partner_id"]
                m_id = row["member_id"]
                cat = row["category"] # 'captador' or 'suporte_performance'
                
                if p_id not in assignments_map:
                    assignments_map[p_id] = {"partner_id": p_id}
                
                if cat == "captador":
                    assignments_map[p_id]["captador_id"] = m_id
                elif cat == "suporte_performance":
                    assignments_map[p_id]["suporte_id"] = m_id
        except Exception as e:
            print(f"Error loading assignments: {e}")
            
        conn.close()
        
        return {
            "partners": partners_map,
            "team_members": team_members,
            "assignments": list(assignments_map.values())
        }

    @staticmethod
    def calculate_commissions(
        partners_data: List[Dict[str, Any]],
        team_members: List[Dict[str, Any]],
        assignments: List[Dict[str, Any]],
        tax_rate: float = 0.30,
        team_categories: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates the comprehensive commission report.

        Args:
            partners_data: List of dicts with keys: id, name, revenue, commission_percentage
            team_members: List of dicts with keys: id, name, roles (list of strings)
            assignments: List of dicts mapping partner_id to captador_id and suporte_id
                         e.g. [{'partner_id': 1, 'captador_id': 10, 'suporte_id': 11}]
            tax_rate: The rate of tax applied to the remaining 50% revenue (defaults to 30% / 0.30)
            team_categories: Custom dictionary of team categories/roles and percentages

        Returns:
            Dict containing summary, partners_calculated, and team_calculated.
        """
        if team_categories is None:
            team_categories = TEAM_CATEGORIES
        
        # 1. Calculate Partners Data
        partners_calculated = []
        for p in partners_data:
            commission_val = p["revenue"] * (p["commission_percentage"] / 100.0)
            partners_calculated.append({
                **p,
                "commission_value": commission_val
            })

        total_partners_revenue = sum(p["revenue"] for p in partners_calculated)
        total_partners_commission = sum(p["commission_value"] for p in partners_calculated)

        # 2. Remaining Value for Team Base
        remaining_value_for_team_fixed = total_partners_revenue - total_partners_commission
        
        # Calculate Tax
        tax_value = remaining_value_for_team_fixed * tax_rate
        remaining_after_tax = remaining_value_for_team_fixed - tax_value

        # 3. Team Calculations
        
        # Calculate total theoretical fixed percentage
        total_theoretical_fixed = 0.0
        
        # Parse team members roles
        # team_members expected structure: [{'id': 1, 'name': 'John', 'roles': ['gerente_expansao']}]
        
        for member in team_members:
            for role in member.get("roles", []):
                cat_info = team_categories.get(role)
                if cat_info and cat_info["type"] == "fixed":
                    total_theoretical_fixed += cat_info["percentage"]

        team_calculated = []
        sum_fixed_pre_norm = 0.0
        total_partner_based_commission_value = 0.0

        # Helper map for assignments
        # partner_id -> {'captador_id': x, 'suporte_id': y}
        assignments_map = {a["partner_id"]: a for a in assignments}

        for member in team_members:
            member_id = member["id"]
            roles = member.get("roles", [])
            
            # Calculate Fixed Component Share
            member_fixed_percentage = 0.0
            for role in roles:
                cat_info = team_categories.get(role)
                if cat_info and cat_info["type"] == "fixed":
                    member_fixed_percentage += cat_info["percentage"]
            
            fixed_commission_for_pool = 0.0
            if member_fixed_percentage > 0:
                fixed_commission_for_pool = (remaining_after_tax * member_fixed_percentage) / 100.0
            
            # Calculate Partner-Based Component
            partner_commission = 0.0
            
            for p_data in partners_calculated:
                p_id = p_data["id"]
                p_revenue = p_data["revenue"]
                assignment = assignments_map.get(p_id, {})
                
                # Check all roles of type partner_based assigned to this member
                for role in roles:
                    cat_info = team_categories.get(role)
                    if cat_info and cat_info.get("type") == "partner_based":
                        role_id_key = f"{role}_id" if role != "suporte_performance" else "suporte_id"
                        assigned_member_id = assignment.get(role_id_key) or assignment.get(role)
                        if assigned_member_id == member_id:
                            partner_commission += p_revenue * (cat_info["percentage"] / 100.0) * (1.0 - tax_rate)

            team_calculated.append({
                "member_id": member_id,
                "name": member["name"],
                "roles": roles,
                "original_fixed_commission": fixed_commission_for_pool,
                "fixed_commission": fixed_commission_for_pool, # Will be normalized later
                "partner_commission": partner_commission,
                "total_commission": 0.0 # Will be calc later
            })
            
            sum_fixed_pre_norm += fixed_commission_for_pool
            total_partner_based_commission_value += partner_commission

        # 4. Normalization
        # target team commission is 13% of remainder after tax
        target_team_commission = remaining_after_tax * 0.13
        available_for_fixed = target_team_commission - total_partner_based_commission_value
        
        if available_for_fixed < 0:
            available_for_fixed = 0.0
            
        normalization_factor = 1.0
        if sum_fixed_pre_norm > 0:
            if available_for_fixed < sum_fixed_pre_norm:
                 normalization_factor = available_for_fixed / sum_fixed_pre_norm
        
        # Apply normalization
        for m_data in team_calculated:
            if available_for_fixed < sum_fixed_pre_norm:
                m_data["fixed_commission"] *= normalization_factor
            
            m_data["total_commission"] = m_data["fixed_commission"] + m_data["partner_commission"]

        # 5. Final Totals
        total_fixed_commission_final = sum(m["fixed_commission"] for m in team_calculated)
        total_team_commission_final = total_fixed_commission_final + total_partner_based_commission_value
        final_remaining_value = remaining_after_tax - total_team_commission_final
        
        avg_partner_commission_pct = 0.0
        if partners_calculated:
            avg_partner_commission_pct = sum(p["commission_percentage"] for p in partners_calculated) / len(partners_calculated)

        summary = {
            "total_gross_revenue": total_partners_revenue,
            "total_partners_commission": total_partners_commission,
            "team_base_value": remaining_value_for_team_fixed,
            "tax_rate": tax_rate,
            "tax_value": tax_value,
            "remaining_after_tax": remaining_after_tax,
            "total_theoretical_fixed_percentage": total_theoretical_fixed,
            "total_team_commission": total_team_commission_final,
            "total_fixed_commission": total_fixed_commission_final,
            "total_partner_based_commission": total_partner_based_commission_value,
            "final_remaining_value": final_remaining_value,
            "average_partner_commission_pct": avg_partner_commission_pct,
            "is_over_fixed_limit": total_theoretical_fixed > MAX_FIXED_TEAM_PERCENTAGE,
            "pool_13_percent_value": target_team_commission,
            "normalization_factor": normalization_factor
        }

        return {
            "summary": summary,
            "partners": partners_calculated,
            "team": team_calculated
        }
