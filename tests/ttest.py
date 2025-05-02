import os
import pytest
from unittest.mock import patch
from config_validator import ConfigValidator, get_config_path, parse_config, get_config, DEFAULT_CONFIG_PATH

# Фикстура для создания временного конфигурационного файла
@pytest.fixture
def temp_config_file(tmp_path):
    def create_config(content):
        config_path = tmp_path / "config.ini"
        config_path.write_text(content, encoding='utf-8')
        return str(config_path)
    return create_config

def test_get_config_path_default():
    with patch.dict(os.environ, {}, clear=True):
        assert get_config_path() == DEFAULT_CONFIG_PATH

def test_get_config_path_from_env():
    custom_path = "/custom/path/config.ini"
    with patch.dict(os.environ, {"CONFIG_PATH": custom_path}):
        assert get_config_path() == custom_path

def test_parse_config_valid(temp_config_file):
    content = """
    [General]
    ScanMemoryLimit = 2048
    PackageType = rpm

    [Watchdog]
    ConnectTimeout = 60m
    """
    config_path = temp_config_file(content)
    config = parse_config(config_path)
    assert config == {
        "General": {"ScanMemoryLimit": "2048", "PackageType": "rpm"},
        "Watchdog": {"ConnectTimeout": "60m"}
    }

def test_parse_config_file_not_found():
    with pytest.raises(FileNotFoundError, match="Конфигурационный файл не найден"):
        parse_config("/non/existent/path.ini")

def test_parse_config_invalid_line(temp_config_file):
    content = """
    [General]
    InvalidLine
    """
    config_path = temp_config_file(content)
    with pytest.raises(ValueError, match="Неподдерживаемая строка: InvalidLine"):
        parse_config(config_path)

def test_validator_missing_sections():
    config = {}
    validator = ConfigValidator(config)
    assert not validator.validate()
    assert sorted(validator.errors) == [
        "Отсутствует секция: General",
        "Отсутствует секция: Watchdog"
    ]

def test_validator_missing_params():
    config = {
        "General": {},
        "Watchdog": {}
    }
    validator = ConfigValidator(config)
    assert not validator.validate()
    assert sorted(validator.errors) == [
        "General.PackageType обязательный параметр, отсутствует",
        "General.ScanMemoryLimit обязательный параметр, отсутствует",
        "Watchdog.ConnectTimeout обязательный параметр, отсутствует"
    ]

def test_validator_valid_config():
    config = {
        "General": {
            "ScanMemoryLimit": "2048",
            "PackageType": "rpm"
        },
        "Watchdog": {
            "ConnectTimeout": "60m"
        }
    }
    validator = ConfigValidator(config)
    assert validator.validate()
    assert validator.errors == []

def test_validator_invalid_scan_memory_limit():
    config = {
        "General": {
            "ScanMemoryLimit": "500",  # Меньше 1024
            "PackageType": "rpm"
        },
        "Watchdog": {
            "ConnectTimeout": "60m"
        }
    }
    validator = ConfigValidator(config)
    assert not validator.validate()
    assert "General.ScanMemoryLimit должен быть целым числом в интервале [1024-8192]" in validator.errors

def test_validator_invalid_package_type():
    config = {
        "General": {
            "ScanMemoryLimit": "2048",
            "PackageType": "invalid"
        },
        "Watchdog": {
            "ConnectTimeout": "60m"
        }
    }
    validator = ConfigValidator(config)
    assert not validator.validate()
    assert "General.PackageType должен быть одним из значений {'rpm', 'deb'}" in validator.errors

def test_validator_invalid_connect_timeout():
    config = {
        "General": {
            "ScanMemoryLimit": "2048",
            "PackageType": "rpm"
        },
        "Watchdog": {
            "ConnectTimeout": "invalid"
        }
    }
    validator = ConfigValidator(config)
    assert not validator.validate()
    assert "Watchdog.ConnectTimeout должен быть в формате \"<число>m\", например \"60m\"" in validator.errors

def test_validator_file_not_found(temp_config_file):
    config = {
        "General": {
            "ScanMemoryLimit": "2048",
            "PackageType": "rpm"
        }
    }
    non_existent_path = "/non/existent/config.ini"
    validator = ConfigValidator(config, config_path=non_existent_path)
    assert not validator.validate()
    assert f"Конфигурационный файл не найден по пути: {non_existent_path}" in validator.errors

def test_get_config_integration(temp_config_file):
    content = """
    [General]
    ScanMemoryLimit = 2048
    PackageType = rpm

    [Watchdog]
    ConnectTimeout = 60m
    """
    config_path = temp_config_file(content)
    with patch.dict(os.environ, {"CONFIG_PATH": config_path}):
        config = get_config()
        assert config == {
            "General": {"ScanMemoryLimit": "2048", "PackageType": "rpm"},
            "Watchdog": {"ConnectTimeout": "60m"}
        }