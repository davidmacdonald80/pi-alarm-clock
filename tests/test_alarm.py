import pytest
from src.alarm import set_volume_for_all_sinks

def test_set_volume_for_all_sinks():
    # Assume that function returns True if successful, False otherwise
    assert set_volume_for_all_sinks(10) == True, "Should return True when successful"
    assert set_volume_for_all_sinks(-1) == False, "Should return False for invalid volume"
