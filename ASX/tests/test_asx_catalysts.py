import pytest
from scripts.asx_catalysts import export_catalysts
from scripts.db_manager import db
from scripts.db_models import CatalystMaster
from scripts.db_schemas import CatalystSchema

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

# --- 2. Rating Logic ---

def test_catalyst_schema_rating_default():
    """Verify that CatalystSchema defaults to '观望'."""
    data = {
        "Ticker": "MSB",
        "Company": "Mesoblast",
        "CR_Risk": "低",
        "Core_Notes": "Testing"
    }
    v = CatalystSchema(**data)
    assert v.Rating == "观望"

def test_catalyst_schema_rating_explicit():
    """Verify that CatalystSchema accepts explicit ratings."""
    data = {
        "Ticker": "MSB",
        "Company": "Mesoblast",
        "CR_Risk": "低",
        "Core_Notes": "Testing",
        "Rating": "强力买入"
    }
    v = CatalystSchema(**data)
    assert v.Rating == "强力买入"

def test_sorting_logic_simulation():
    """Simulate the sorting logic used in run.py."""
    r_scores = {"强力买入": -10, "买入": -5, "观望": 0, "卖出": 5, "强力卖出": 10}
    
    items = [
        {"Ticker": "A", "Rating": "卖出"},
        {"Ticker": "B", "Rating": "强力买入"},
        {"Ticker": "C", "Rating": "观望"},
        {"Ticker": "D", "Rating": "买入"}
    ]
    
    sorted_items = sorted(items, key=lambda x: r_scores.get(x["Rating"], 0))
    
    assert sorted_items[0]["Ticker"] == "B" # Strong Buy
    assert sorted_items[1]["Ticker"] == "D" # Buy
    assert sorted_items[2]["Ticker"] == "C" # Hold
    assert sorted_items[3]["Ticker"] == "A" # Sell
