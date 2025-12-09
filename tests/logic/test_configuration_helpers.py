import sys
import types
from unittest.mock import patch, MagicMock



def setup_fake_django_settings(tmp_path):
    fake = types.ModuleType("fake_settings")
    fake.BASE_DIR = str(tmp_path)
    sys.modules["fake_settings"] = fake
    return fake




def test_load_config_calls_load_json(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    with patch("scheduler.logic.configuration_helpers._load_json") as mock_load:
        mock_load.return_value = {"ok": True}

        import scheduler.logic.configuration_helpers as cfg

        result = cfg.load_config()
        mock_load.assert_called_once()
        assert result == {"ok": True}




def test_save_config_calls_save_with_lock(tmp_path, monkeypatch):
    setup_fake_django_settings(tmp_path)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "fake_settings")

    with patch("scheduler.logic.configuration_helpers._save_json_with_lock") as mock_save:
        import scheduler.logic.configuration_helpers as cfg

        data = {"x": 1}
        cfg.save_config(data)

        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        assert "config.json" in str(args[0])
        assert args[1] == data



