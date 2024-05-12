import pytest
from unittest.mock import patch, Mock
from src.alarm import set_volume_for_all_sinks

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_set_volume_success(mock_subprocess_run):
    # Simulate successful listing of sinks
    mock_subprocess_run.return_value = Mock(returncode=0, stdout="sink1\tname1\nsink2\tname2", stderr='')
    # Assume volume setting also succeeds
    assert set_volume_for_all_sinks(50) == True, "Should return True when volume setting is successful"

def test_list_sinks_failure(mock_subprocess_run):
    # Simulate failure in listing sinks
    mock_subprocess_run.return_value = Mock(returncode=1, stdout='', stderr='Error listing sinks')
    assert set_volume_for_all_sinks(50) == False, "Should return False when listing sinks fails"

def test_set_volume_failure(mock_subprocess_run):
    # Simulate successful listing but failure in setting volume
    mock_subprocess_run.side_effect = [
        Mock(returncode=0, stdout="sink1\tname1\nsink2\tname2", stderr=''),  # First call to list sinks
        Mock(returncode=1, stdout='', stderr='Error setting volume')  # Second call to set volume
    ]
    assert set_volume_for_all_sinks(50) == False, "Should return False when setting volume fails"

def test_invalid_volume_input(mock_subprocess_run):
    # Test with invalid volume input, assuming check_volume_input validates the range
    assert set_volume_for_all_sinks(101) == False, "Should return False for invalid volume input"