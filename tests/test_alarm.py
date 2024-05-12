import pytest
from phue import Bridge
from unittest.mock import patch, MagicMock, Mock, call, ANY
from src.alarm import set_volume_for_all_sinks, set_lights, log_to_journal

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

@pytest.fixture
def mock_bridge():
    with patch('phue.Bridge') as mock:
        mock.return_value = Mock(set_light=Mock())
        yield mock.return_value

@pytest.fixture
def mock_log_to_journal():
    with patch('src.alarm.log_to_journal') as mock:
        yield mock

def test_set_lights_on_success(mock_bridge, mock_log_to_journal):
    # mock_bridge.set_light.return_value = None  # Assume success doesn't return anything
    set_lights(mock_bridge, True)  # Test setting lights on
    mock_bridge.set_light.assert_called_once_with(['Lamp', 'FarWall', 'NearWall'], {'transitiontime': 3000, 'on': True, 'bri': 254})
    mock_log_to_journal.assert_called_with("Lights on at ...", level='info')
    mock_log_to_journal.assert_has_calls([call(ANY, level='info')])

def test_set_lights_off_success(mock_bridge, mock_log_to_journal):
    # mock_bridge.set_light.return_value = None  # Assume success doesn't return anything
    set_lights(mock_bridge, False)  # Test setting lights off
    mock_bridge.set_light.assert_called_once_with(['Lamp', 'FarWall', 'NearWall'], {'on': False})
    mock_log_to_journal.assert_called_with("Lights off at ...", level='info')

def test_set_lights_failure(mock_bridge, mock_log_to_journal):
    expected_exception = Exception("Connection error0")
    mock_bridge.set_light.side_effect = expected_exception
    set_lights(mock_bridge, True)  # Attempt to turn lights on
    mock_log_to_journal.assert_called_with("Failed to control lights.", level='error', exception=expected_exception)


