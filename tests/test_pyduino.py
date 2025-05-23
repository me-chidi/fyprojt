from unittest.mock import patch, MagicMock
import pytest
import pyduino
import json


# a class whose truthiness flips after one call.
class OnceTrue:
    def __init__(self):
        self.first = True

    def __bool__(self):
        if self.first:
            self.first = False
            return True
        return False


def test_connect_arduino_failure(capsys):
    with (
        patch("pyduino.find_arduino", return_value=None),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        try:
            pyduino.connect_arduino()
        except KeyboardInterrupt:
            pass
        captured = capsys.readouterr()
        # this msg should be in the buffer
        assert "❌ No Arduino found. Retrying..." in captured.out


def test_connect_arduino_success(capsys):  # fails and then finds
    with (
        patch("pyduino.find_arduino", return_value="COM3"),
        patch("serial.Serial", return_value="fake-serial"),
        patch("time.sleep"),
    ):
        result = pyduino.connect_arduino()

    captured = capsys.readouterr()
    assert "✅ Found Arduino on COM3, connecting..." in captured.out
    assert "🔌 Connected to Arduino on COM3!" in captured.out
    assert result == "fake-serial"


class TestReadJsonData:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.fake_app = MagicMock()
        self.fake_context = self.fake_app.app_context.return_value.__enter__.return_value
        # the above line simulates the return value of a context manager
        self.fake_model = MagicMock()
        self.fake_session = MagicMock()
        self.fake_serial = MagicMock()
        self.db_obj = MagicMock(session=self.fake_session)

    def test_arduino_unavailable(self, capsys):
        # Simulate connect_arduino raising an exception
        with patch("pyduino.connect_arduino", side_effect=Exception("No Arduino found")):
            with pytest.raises(Exception, match="No Arduino found"):
                pyduino.read_json_data(self.db_obj, self.fake_model, self.fake_app)

    def test_invalid_json_received(self, capsys):
        self.fake_serial.in_waiting = 1
        self.fake_serial.readline.return_value = b"invalid_json\n"

        with (
            patch("pyduino.connect_arduino", return_value=self.fake_serial),
            patch("pyduino.serial_connection", self.fake_serial),
            patch("pyduino.flag", OnceTrue()),
        ):
            pyduino.read_json_data(self.db_obj, self.fake_model, self.fake_app)

            captured = capsys.readouterr()
            assert "⚠️ Invalid JSON received" in captured.out

    def test_valid_json_saved(self, capsys):
        json_data = json.dumps({"node1": {"sta": 1, "batt": 900, "ldr": 500}}) + "\n"

        self.fake_serial.in_waiting = 1
        self.fake_serial.readline.return_value = json_data.encode("utf-8")
        self.fake_model.query.get.return_value = None

        with (
            patch("pyduino.connect_arduino", return_value=self.fake_serial),
            patch("pyduino.serial_connection", self.fake_serial),
            patch("pyduino.flag", OnceTrue()),
        ):
            pyduino.read_json_data(self.db_obj, self.fake_model, self.fake_app)

        captured = capsys.readouterr()
        assert "📊 Received JSON:" in captured.out
        self.fake_session.add.assert_called_once()
        self.fake_session.commit.assert_called_once()

    def test_valid_json_db_failure(self, capsys):
        json_data = json.dumps({"node1": {"sta": 1, "batt": 900, "ldr": 500}}) + "\n"

        self.fake_serial.in_waiting = 1
        self.fake_serial.readline.return_value = json_data.encode("utf-8")
        self.fake_model.query.get.return_value = None
        self.fake_session.commit.side_effect = Exception("DB Error")

        with (
            patch("pyduino.connect_arduino", return_value=self.fake_serial),
            patch("pyduino.serial_connection", self.fake_serial),
            patch("pyduino.flag", OnceTrue()),
        ):
            pyduino.read_json_data(self.db_obj, self.fake_model, self.fake_app)

        captured = capsys.readouterr()
        self.fake_session.rollback.assert_called_once()
        assert "FATAL! database error while processing node1: DB Error" in captured.out
