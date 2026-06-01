import pytest
from services.commission import CommissionEngine

def test_calculate_commissions_zero_tax():
    # Setup test data: one partner with 10000 faturamento at 50% commission
    partners_data = [
        {"id": "partner1", "name": "Parceiro 1", "revenue": 10000.0, "commission_percentage": 50.0}
    ]
    
    # 2 team members, one with fixed gerente role (3%), another with coordinated support (2.5%)
    team_members = [
        {"id": 1, "name": "Membro 1", "roles": ["gerente_expansao"]},
        {"id": 2, "name": "Membro 2", "roles": ["coordenador_suporte"]}
    ]
    assignments = []

    # 1. Test with 0% tax (old behavior)
    res_zero = CommissionEngine.calculate_commissions(
        partners_data=partners_data,
        team_members=team_members,
        assignments=assignments,
        tax_rate=0.0
    )
    
    summary = res_zero["summary"]
    # Total revenue = 10000
    # Partner commission = 50% of 10000 = 5000
    # Base remaining = 5000
    # Tax = 0% of 5000 = 0
    # Remaining after tax = 5000
    # Target team commission = 13% of 5000 = 650
    # Total fixed roles = 3.0 + 2.5 = 5.5%
    # Since total fixed percentage (5.5%) is less than team limit (13%), no normalisation needed.
    # Membro 1 fixed = (3/5.5) * 13% of 5000 = 354.5454... (Wait: TS logic says: 
    # effective_percentage = 13.0 if total_theoretical_fixed > 0 else 0.0
    # proportional_share = (member_fixed_percentage / total_theoretical_fixed) * effective_percentage
    # Membro 1: (3 / 5.5) * 13 = 7.090909%
    # Fixed commission = 5000 * 7.090909% / 100 = 354.545
    # Membro 2: (2.5 / 5.5) * 13 = 5.90909%
    # Fixed commission = 5000 * 5.90909% / 100 = 295.454
    # Total team commission = 354.545 + 295.454 = 650.0
    # final_remaining_value = 5000 - 650 = 4350.0
    
    assert summary["total_gross_revenue"] == 10000.0
    assert summary["total_partners_commission"] == 5000.0
    assert summary["tax_value"] == 0.0
    assert summary["remaining_after_tax"] == 5000.0
    assert summary["total_team_commission"] == pytest.approx(650.0)
    assert summary["final_remaining_value"] == pytest.approx(4350.0)


def test_calculate_commissions_default_tax():
    partners_data = [
        {"id": "partner1", "name": "Parceiro 1", "revenue": 10000.0, "commission_percentage": 50.0}
    ]
    team_members = [
        {"id": 1, "name": "Membro 1", "roles": ["gerente_expansao"]},
        {"id": 2, "name": "Membro 2", "roles": ["coordenador_suporte"]}
    ]
    assignments = []

    # 2. Test with 30% tax (new behavior)
    res_tax = CommissionEngine.calculate_commissions(
        partners_data=partners_data,
        team_members=team_members,
        assignments=assignments,
        tax_rate=0.30
    )
    
    summary = res_tax["summary"]
    # Total revenue = 10000
    # Partner commission = 5000
    # Base remaining = 5000
    # Tax = 30% of 5000 = 1500
    # Remaining after tax = 5000 - 1500 = 3500
    # Target team commission = 13% of 3500 = 455
    # Membro 1: (3 / 5.5) * 13% of 3500 = 248.1818...
    # Membro 2: (2.5 / 5.5) * 13% of 3500 = 206.8181...
    # Total team commission = 455
    # final_remaining_value = 3500 - 455 = 3045
    
    assert summary["total_gross_revenue"] == 10000.0
    assert summary["total_partners_commission"] == 5000.0
    assert summary["tax_value"] == 1500.0
    assert summary["remaining_after_tax"] == 3500.0
    assert summary["total_team_commission"] == pytest.approx(455.0)
    assert summary["final_remaining_value"] == pytest.approx(3045.0)
