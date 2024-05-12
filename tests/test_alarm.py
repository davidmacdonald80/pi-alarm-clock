import pytest
from unittest.mock import patch, MagicMock
from src.alarm import set_volume_for_all_sinks

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_set_volume_success(mock_subprocess_run):
    # Mock for listing sinks
    mock_list_sinks = MagicMock(returncode=0, stdout="sink1\tname1\nsink2\tname2", stderr='')
    # Mock for setting volume
    mock_set_volume = MagicMock(returncode=0, stdout='', stderr='')

    # Set side_effect to simulate different calls
    mock_subprocess_run.side_effect = [mock_list_sinks, mock_set_volume, mock_set_volume]

    # Call the function
    result = set_volume_for_all_sinks(50)
    # Assertions
    assert result == True, "Should return True when volume setting is successful"
    mock_subprocess_run.assert_called()

    # Check if subprocess.run was called correctly
    calls = [
        ((['pactl', 'list', 'short', 'sinks'],), {'capture_output': True, 'text': True}),
        ((['pactl', 'set-sink-volume', 'name1', '50%'],), {'capture_output': True, 'text': True}),
        ((['pactl', 'set-sink-volume', 'name2', '50%'],), {'capture_output': True, 'text': True})
    ]
    mock_subprocess_run.assert_has_calls(calls, any_order=True)