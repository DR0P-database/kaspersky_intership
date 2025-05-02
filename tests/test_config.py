from pathlib import Path
import pytest

from framework.tools import parse_config
from framework.validator import ConfigValidator
from tests.conftest import VALID_BASE, VALID_DICT_CONFIG


# === Общая валидная основа для тестов ===


def test_config_file_not_found(tmp_path):
    non_existing_path = tmp_path / "not_here.ini"
    with pytest.raises(FileNotFoundError):
        parse_config(non_existing_path)

def test_parsing(tmp_path):
    config_path = tmp_path / "config.ini"
    config_path.write_text(VALID_BASE.strip())

    parsed = parse_config(config_path)
    assert parsed == VALID_DICT_CONFIG, "Парсинг дал неожиданный результат"

def test_validator(valid_config_dict):
    validator = ConfigValidator(valid_config_dict)
    validator.validate()  # Не должно быть исключений

def run_validator(config_dict):
    validator = ConfigValidator(config_dict)
    validator.validate()

def test_parse_config_invalid(tmp_path):
    config = """
    [General]
    InvalidLineWithoutEquals
    """
    path = tmp_path / "config.ini"
    path.write_text(config.strip())

    with pytest.raises(ValueError, match=r"Неподдерживаемая строка:"):
         parse_config(path)

@pytest.mark.parametrize("section", ["General", "Watchdog"])
def test_missing_section(valid_config_dict, section): 
    del valid_config_dict[section]

    with pytest.raises(ValueError, match=f"Отсутствует секция: {section}"):
        run_validator(valid_config_dict)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_missing_general_param(valid_config_dict, param):
    del valid_config_dict['General'][param]

    with pytest.raises(ValueError, match=f"{param}.*обязательный параметр"):
        run_validator(valid_config_dict)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_missing_watchdog_param(valid_config_dict, param):
    del valid_config_dict['Watchdog'][param]

    with pytest.raises(ValueError, match=fr"{param}.*обязательный параметр"):
        run_validator(valid_config_dict)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_duplicate_param_general(valid_config_dict, param):
    valid_config_dict['General']['__duplicates__'][param] = 2
    with pytest.raises(ValueError, match=f"{param}.*указан 2 раз"):
        run_validator(valid_config_dict)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_duplicate_param_watchdog(valid_config_dict, param):
    valid_config_dict['Watchdog']['__duplicates__'][param] = 2
    with pytest.raises(ValueError, match=f"{param}.*указан 2 раз"):
        run_validator(valid_config_dict)

@pytest.mark.parametrize("wrong_section, param", [
    ("Watchdog", "ScanMemoryLimit"),
    ("General", "ConnectTimeout"),
])
def test_param_wrong_section(valid_config_dict, wrong_section, param):
    valid_config_dict[wrong_section][param] = 'WRONG'
    with pytest.raises(ValueError, match=fr"{param}.*не должен находиться в этой секции"):
        run_validator(valid_config_dict)

def test_unknown_param_invalid(valid_config_dict):
    valid_config_dict['General']['Foo'] = 'bar'

    with pytest.raises(ValueError, match=r"Foo.*не должен находиться в этой секции"):
        run_validator(valid_config_dict)

# def test_unknown_param_ignored(valid_config_dict):
#     valid_config_dict['Other'] = {}
#     valid_config_dict['Other']['Foo'] = 'bar'
#     # Не должно быть исключения
#     assert run_validator(valid_config_dict) == True
# @pytest.mark.parametrize("value", ["99999", "abc"])
# def test_scanmemorylimit_invalid(tmp_path, value):
#     config = VALID_BASE.replace("ScanMemoryLimit=2048", f"ScanMemoryLimit={value}")
#     with pytest.raises(ValueError, match="ScanMemoryLimit.*целым числом"):
#         run_validator(tmp_path, config)

# @pytest.mark.parametrize("value", ["tar.gz", "exe"])
# def test_packagetype_invalid(tmp_path, value):
#     config = VALID_BASE.replace("PackageType=deb", f"PackageType={value}")
#     with pytest.raises(ValueError, match="PackageType.*одним из значений"):
#         run_validator(tmp_path, config)

# @pytest.mark.parametrize("value", ["maybe", "123"])
# def test_additionaldnslookup_invalid(tmp_path, value):
#     config = VALID_BASE.replace("AdditionalDNSLookup=true", f"AdditionalDNSLookup={value}")
#     with pytest.raises(ValueError, match="AdditionalDNSLookup.*одним из значений"):
#         run_validator(tmp_path, config)

# @pytest.mark.parametrize("value", ["/nonexistent/path", "relative/path"])
# def test_coredumpspath_invalid(tmp_path, value):
#     config = VALID_BASE.replace("CoreDumpsPath=/", f"CoreDumpsPath={value}")
#     with pytest.raises(ValueError, match="CoreDumpsPath.*абсолютным путем"):
#         run_validator(tmp_path, config)

# @pytest.mark.parametrize("value", ["1234", "not-a-uuid"])
# def test_machineid_invalid(tmp_path, value):
#     config = VALID_BASE.replace("MachineId=7b5cc0e7-0205-48e1-bf63-347531eef193", f"MachineId={value}")
#     with pytest.raises(ValueError, match="MachineId.*UUID"):
#         run_validator(tmp_path, config)

# @pytest.mark.parametrize("value", ["english_US", "!!"])
# def test_locale_invalid(tmp_path, value):
#     config = VALID_BASE.replace("Locale=en_US.UTF-8", f"Locale={value}")
#     with pytest.raises(ValueError, match="Locale.*RFC 3066"):
#         run_validator(tmp_path, config)



# def test_get_config_path_default(monkeypatch):  # Получаем дефолтный путь
#     monkeypatch.delenv("CONFIG_PATH", raising=False)  # Удаляем переменную окружения
#     path = get_config_path()
#     assert path == DEFAULT_PATH

# def test_get_config_path_custom(monkeypatch):  
#     monkeypatch.setenv("CONFIG_PATH", "/tmp/custom_config.ini")
#     path = get_config_path()
#     assert path == "/tmp/custom_config.ini"


# def test_parse_config_is_directory(tmp_path):
#     with pytest.raises(OSError):  # Можно также: IsADirectoryError, но он не во всех Python-версиях
#         parse_config(tmp_path)  # tmp_path — это директория
