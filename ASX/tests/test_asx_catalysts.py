import pytest
from scripts.asx_catalysts import export_catalysts
from scripts.db_manager import db
from scripts.db_models import CatalystMaster

# --- 1. Catalyst Management ---

def test_catalyst_export_function():
    """Verify that asx_catalysts has the core export function."""
    assert callable(export_catalysts)

def test_field_validity():
    """Verify that all live records in the database have valid, separated fields."""
    valid_levels = ["极低", "低", "中低", "中", "中高", "高", "极高", "Unknown", "N/A"]
    
    with db.session_scope() as sess:
        masters = sess.query(CatalystMaster).all()
        for m in masters:
            # Check for combined content (parentheses are the signature of un-migrated data)
            assert "(" not in (m.cr_risk or ""), f"Ticker {m.symbol} has un-migrated CR Risk: {m.cr_risk}"
            assert "(" not in (m.breakout_probability or ""), f"Ticker {m.symbol} has un-migrated Probability: {m.breakout_probability}"
            
            # Check for valid categories (stripped)
            cr_lvl = m.cr_risk.strip() if m.cr_risk else "Unknown"
            prob_lvl = m.breakout_probability.strip() if m.breakout_probability else "N/A"
            
            assert cr_lvl in valid_levels, f"Ticker {m.symbol} has invalid CR Risk level: {cr_lvl}"
            assert prob_lvl in valid_levels, f"Ticker {m.symbol} has invalid Probability level: {prob_lvl}"

            # Ensure reasons are not combined in the level
            if cr_lvl not in ["Unknown", "N/A"]:
                assert len(cr_lvl) <= 4, f"Ticker {m.symbol} CR Risk level seems too long: {cr_lvl}"
            if prob_lvl not in ["Unknown", "N/A"]:
                assert len(prob_lvl) <= 4, f"Ticker {m.symbol} Probability level seems too long: {prob_lvl}"
