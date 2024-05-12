import pytest
from unittest.mock import patch, MagicMock
from src.alarm import set_volume_for_all_sinks

@pytest.fixture
def mock_subprocess_run():
    with patch('src.alarm.run') as mock_run:  # Make sure to patch at the correct location
        yield mock_run

def test_set_volume_success(mock_subprocess_run):
    # Mock for listing sinks with successful return values
    mock_list_sinks = MagicMock(returncode=0, stdout="sink1\tname1\nsink2\tname2", stderr='')
    # Mock for setting volume also succeeds
    mock_set_volume = MagicMock(returncode=0, stdout='', stderr='')

    # Configure the mock to simulate the different subprocess calls within the function
    mock_subprocess_run.side_effect = [mock_list_sinks, mock_set_volume, mock_set_volume]

    # Execute the function with debug information
    result = set_volume_for_all_sinks(50)
    print("Mock calls made:", mock_subprocess_run.mock_calls)  # Debug output

    # Assertions
    assert result == True, "Should return True when volume setting is successful"

    # Ensure the subprocess.run was called with the correct parameters
    expected_calls = [
        ((['pactl', 'list', 'short', 'sinks'],), {'capture_output': True, 'text': True}),
        ((['pactl', 'set-sink-volume', 'name1', '50%'],), {'capture_output': True, 'text': True}),
        ((['pactl', 'set-sink-volume', 'name2', '50%'],), {'capture_output': True, 'text': True})
    ]
    mock_subprocess_run.assert_has_calls(expected_calls, any_order=True)
