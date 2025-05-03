import uuid
from pathlib import Path

import pytest

from framework.tools import DEFAULT_PATH, get_config_path, parse_config
from framework.validator import ConfigValidator
from tests.conftest import VALID_BASE, VALID_DICT_CONFIG


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
    return validator.validate()


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
    del valid_config_dict["General"][param]

    with pytest.raises(ValueError, match=f"{param}.*обязательный параметр"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_missing_watchdog_param(valid_config_dict, param):
    del valid_config_dict["Watchdog"][param]

    with pytest.raises(ValueError, match=rf"{param}.*обязательный параметр"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_duplicate_param_general(valid_config_dict, param):
    with pytest.raises(KeyError, match=rf"запрещено: {param}"):
        valid_config_dict["General"][param] = "DUPLICATE"


@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_duplicate_param_watchdog(valid_config_dict, param):
    with pytest.raises(KeyError, match=rf"запрещено: {param}"):
        valid_config_dict["Watchdog"][param] = "DUPLICATE"


@pytest.mark.parametrize(
    "wrong_section, param",
    [
        ("Watchdog", "ScanMemoryLimit"),
        ("General", "ConnectTimeout"),
    ],
)
def test_param_wrong_section(valid_config_dict, wrong_section, param):
    valid_config_dict[wrong_section][param] = "WRONG"
    with pytest.raises(
        ValueError, match=rf"{param}.*не должен находиться в этой секции"
    ):
        run_validator(valid_config_dict)


def test_unknown_param_invalid(valid_config_dict):
    valid_config_dict["General"]["Foo"] = "bar"

    with pytest.raises(ValueError, match=r"Foo.*не должен находиться в этой секции"):
        run_validator(valid_config_dict)


def test_unknown_param_ignored(valid_config_dict):
    valid_config_dict["[Other]"] = {}
    valid_config_dict["[Other]"]["Foo"] = "bar"

    # Не должно быть исключения
    assert run_validator(valid_config_dict) == True


@pytest.mark.parametrize("param", ["MaxInotifyInstances", "ScanMemoryLimit"])
@pytest.mark.parametrize("value", [9000, 512, "string", True, ""])
def test_invalid_range_params(valid_config_dict, value, param):
    del valid_config_dict["General"][param]
    valid_config_dict["General"][param] = str(value)

    with pytest.raises(ValueError, match=f"{param}.*целым числом в интервале"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("value", [9000, 512, "string", 9, True, ""])
def test_invalid_exec_arg_max(valid_config_dict, value):
    del valid_config_dict["General"]["ExecArgMax"]
    valid_config_dict["General"]["ExecArgMax"] = str(value)

    with pytest.raises(ValueError, match="ExecArgMax.*целым числом в интервале"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("value", [999, 1000001, "string", True, ""])
def test_invalid_exec_arg_max(valid_config_dict, value):
    del valid_config_dict["General"]["MaxInotifyWatches"]
    valid_config_dict["General"]["MaxInotifyWatches"] = str(value)

    with pytest.raises(ValueError, match="MaxInotifyWatches.*целым числом в интервале"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["RPM", "deb", "DeB"])
def test_valid_package_type(valid_config_dict, value):
    del valid_config_dict["General"]["PackageType"]
    valid_config_dict["General"]["PackageType"] = value

    assert run_validator(valid_config_dict)


def test_invalid_package_type(valid_config_dict):
    del valid_config_dict["General"]["PackageType"]
    valid_config_dict["General"]["PackageType"] = "tar.gz"

    with pytest.raises(ValueError, match="PackageType.*должен быть одним из значений"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize(
    "param",
    [
        "AdditionalDNSLookup",
        "CoreDumps",
        "RevealSensitiveInfoInTraces",
        "UseFanotify",
        "KsvlaMode",
        "StartupTraces",
    ],
)
@pytest.mark.parametrize("value", ["string", 0])
def test_invalid_boolean_params(valid_config_dict, param, value):
    del valid_config_dict["General"][param]
    valid_config_dict["General"][param] = value

    with pytest.raises(ValueError, match=rf"{param}.*должен быть одним из значений"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize(
    "param",
    [
        "AdditionalDNSLookup",
        "CoreDumps",
        "RevealSensitiveInfoInTraces",
        "UseFanotify",
        "KsvlaMode",
        "StartupTraces",
    ],
)
@pytest.mark.parametrize("value", ["yes", "NO", "true", False, "YeS", True])
def test_valid_boolean_params(valid_config_dict, param, value):
    del valid_config_dict["General"][param]
    valid_config_dict["General"][param] = value
    assert run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["1234", "not-a-uuid"])
def test_invalid_machine_id(valid_config_dict, value):
    del valid_config_dict["General"]["MachineId"]
    valid_config_dict["General"]["MachineId"] = value
    with pytest.raises(ValueError, match="MachineId.*UUID"):
        run_validator(valid_config_dict)


def test_valid_machine_id(valid_config_dict):
    del valid_config_dict["General"]["MachineId"]
    valid_config_dict["General"]["MachineId"] = str(uuid.uuid4())
    assert run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["english_US", "en-UTF"])
def test_invalid_locale(valid_config_dict, value):
    del valid_config_dict["General"]["Locale"]
    valid_config_dict["General"]["Locale"] = value
    with pytest.raises(ValueError, match="Locale.*формат"):
        run_validator(valid_config_dict)


def test_valid_locale(valid_config_dict):
    del valid_config_dict["General"]["Locale"]
    valid_config_dict["General"]["Locale"] = "en_US.UTF-8"
    assert run_validator(valid_config_dict)


@pytest.mark.parametrize("value", [0, "str"])
def test_invalid_core_dumps_path_type(valid_config_dict, value):
    del valid_config_dict["General"]["CoreDumpsPath"]
    valid_config_dict["General"]["CoreDumpsPath"] = value
    with pytest.raises(
        ValueError, match="CoreDumpsPath.*должен быть существующим абсолютным путем"
    ):
        run_validator(valid_config_dict)


def test_core_dumps_path_not_exist(valid_config_dict, tmp_path):
    path = tmp_path / "nonexistent" / "dumps"
    del valid_config_dict["General"]["CoreDumpsPath"]
    valid_config_dict["General"]["CoreDumpsPath"] = Path(path)
    with pytest.raises(
        ValueError, match="CoreDumpsPath.*должен быть существующим абсолютным путем"
    ):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["10", "10mm", "10s", "mm", "99.9m"])
def test_invalid_connect_timeout(valid_config_dict, value):
    del valid_config_dict["Watchdog"]["ConnectTimeout"]
    valid_config_dict["Watchdog"]["ConnectTimeout"] = value

    with pytest.raises(ValueError, match="ConnectTimeout.*некорректный формат"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["121m", "0m"])
def test_invalid_range_connect_timeout(value, valid_config_dict):
    del valid_config_dict["Watchdog"]["ConnectTimeout"]
    valid_config_dict["Watchdog"]["ConnectTimeout"] = value
    with pytest.raises(ValueError, match="ConnectTimeout.*должен быть целым числом"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ["MaxMemory", "MaxVirtualMemory"])
@pytest.mark.parametrize("value", [0, -1])
def test_invalid_watchdog_memory_values(valid_config_dict, param, value):
    del valid_config_dict["Watchdog"][param]
    valid_config_dict["Watchdog"][param] = value
    with pytest.raises(ValueError, match=rf"{param}"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ["MaxMemory", "MaxVirtualMemory"])
@pytest.mark.parametrize("value", ["auto", "off", "99.9"])
def test_valid_watchdog_memory_values(valid_config_dict, param, value):
    del valid_config_dict["Watchdog"][param]
    valid_config_dict["Watchdog"][param] = value
    assert run_validator(valid_config_dict)


@pytest.mark.parametrize("value", ["string", 10001])
def test_invalid_ping_interval(valid_config_dict, value):
    del valid_config_dict["Watchdog"]["PingInterval"]
    valid_config_dict["Watchdog"]["PingInterval"] = value
    with pytest.raises(ValueError, match="PingInterval.*должен быть целым числом"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_invalid_nonetype_general_param(valid_config_dict, param):
    del valid_config_dict["General"][param]
    valid_config_dict["General"][param] = None

    with pytest.raises(TypeError, match=f"{param}"):
        run_validator(valid_config_dict)


@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_invalid_nonetype_watchdog_param(valid_config_dict, param):
    del valid_config_dict["Watchdog"][param]
    valid_config_dict["Watchdog"][param] = None

    with pytest.raises(TypeError, match=f"{param}"):
        run_validator(valid_config_dict)


def test_get_config_path_default():  # Получаем дефолтный CONFIG путь
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("CONFIG_PATH", raising=False)  # Удаляем переменную окружения
        path = get_config_path()
        assert path == DEFAULT_PATH


def test_get_config_path_custom():
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("CONFIG_PATH", raising=False)
        mp.setenv("CONFIG_PATH", "/tmp/custom_config.ini")
        path = get_config_path()
        assert path == "/tmp/custom_config.ini"


def test_get_config_path_custom_env_file(tmp_path):
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("CONFIG_PATH", raising=False)
        file = tmp_path / ".env"
        file.write_text("CONFIG_PATH=/tmp/custom_config_file.ini", encoding="utf-8")
        path = get_config_path(env_path=tmp_path / ".env")
        assert path == "/tmp/custom_config_file.ini"
