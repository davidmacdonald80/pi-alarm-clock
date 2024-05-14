import pytest
from phue import Bridge
from unittest.mock import patch, MagicMock, Mock, call, ANY
from src.alarm import AlarmClock
from zoneinfo import ZoneInfo

TEST_TIMEZONE = ZoneInfo("America/Chicago")
TEST_LIGHT_COMMAND = {'transitiontime': 3000, 'on': True, 'bri': 254}
TEST_LIGHTGROUP = ['Lamp', 'FarWall', 'NearWall']

@pytest.fixture
def mock_subprocess_run():
    with patch('src.alarm.run') as mock_run:  # Make sure to patch at the correct location
        yield mock_run

@pytest.fixture
def alarm_clock():
    return AlarmClock(alarm_time="6:05", only_weekdays=True, volume_level=50)

def test_set_volume_success(mock_subprocess_run, alarm_clock):
    # Mock for listing sinks with successful return values
    mock_list_sinks = MagicMock(returncode=0, stdout="sink1\tname1\nsink2\tname2", stderr='')
    # Mock for setting volume also succeeds
    mock_set_volume = MagicMock(returncode=0, stdout='', stderr='')

    # Configure the mock to simulate the different subprocess calls within the function
    mock_subprocess_run.side_effect = [mock_list_sinks, mock_set_volume, mock_set_volume]

    # Execute the function with debug information
    result = alarm_clock.set_volume_for_all_sinks(10)
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
    with patch.object(AlarmClock, 'log_to_journal') as mock:
        yield mock

def test_set_lights_on_success(mock_bridge, mock_log_to_journal, alarm_clock):
    alarm_clock.bridge = mock_bridge
    alarm_clock.set_lights(on=True)  # Test setting lights on
    mock_bridge.set_light.assert_called_once_with(TEST_LIGHTGROUP, TEST_LIGHT_COMMAND)
    mock_log_to_journal.assert_called_with(ANY, level='info')

def test_set_lights_off_success(mock_bridge, mock_log_to_journal, alarm_clock):
    alarm_clock.bridge = mock_bridge
    alarm_clock.set_lights(on=False)  # Test setting lights off
    mock_bridge.set_light.assert_called_once_with(TEST_LIGHTGROUP, {'on': False})
    mock_log_to_journal.assert_called_with(ANY, level='info')

def test_set_lights_failure(mock_bridge, mock_log_to_journal, alarm_clock):
    alarm_clock.bridge = mock_bridge
    expected_exception = Exception("Connection error0")
    mock_bridge.set_light.side_effect = expected_exception
    alarm_clock.set_lights(on=True)  # Attempt to turn lights on
    mock_log_to_journal.assert_called_with(ANY, level='error', exception=expected_exception)

