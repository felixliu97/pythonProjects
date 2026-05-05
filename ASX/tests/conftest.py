import os
import sys
from unittest.mock import patch

import pytest

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True)
def mock_yaml_data():
    """Mock YAML data loading and saving for all tests."""
    yaml_store = {}

    def mock_load(filename):
        return yaml_store.get(filename, [])

    def mock_save(filename, data):
        yaml_store[filename] = data

    with (
        patch("scripts.utils.load_yaml_data", side_effect=mock_load),
        patch("scripts.utils.save_yaml_data", side_effect=mock_save),
        patch("scripts.asx_announcements.load_yaml_data", side_effect=mock_load, create=True),
        patch("scripts.asx_announcements.save_yaml_data", side_effect=mock_save, create=True),
        patch("scripts.asx_placements.load_yaml_data", side_effect=mock_load, create=True),
        patch("scripts.asx_placements.save_yaml_data", side_effect=mock_save, create=True),
        patch("scripts.asx_analyzer.load_yaml_data", side_effect=mock_load, create=True),
        patch("scripts.asx_analyzer.save_yaml_data", side_effect=mock_save, create=True),
    ):
        yield yaml_store
