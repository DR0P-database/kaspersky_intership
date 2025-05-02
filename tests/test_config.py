from pathlib import Path
import pytest
import re

from framework.tools import get_config_path, parse_config, DEFAULT_PATH
from framework.validator import ConfigValidator


# === Общая валидная основа для тестов ===
VALID_BASE = '''
[General]
ScanMemoryLimit=2048
PackageType=deb
ExecArgMax=20
AdditionalDNSLookup=true
CoreDumps=no
RevealSensitiveInfoInTraces=yes
ExecEnvMax=50
MaxInotifyWatches=300000
CoreDumpsPath=/
UseFanotify=no
KsvlaMode=no
MachineId=7b5cc0e7-0205-48e1-bf63-347531eef193
StartupTraces=false
MaxInotifyInstances=2048
Locale=en_US.UTF-8

[Watchdog]
ConnectTimeout=30m
MaxVirtualMemory=auto
MaxMemory=off
PingInterval=3000
'''

# def test_get_config_path_default(monkeypatch):  # Получаем дефолтный путь
#     monkeypatch.delenv("CONFIG_PATH", raising=False)  # Удаляем переменную окружения
#     path = get_config_path()
#     assert path == DEFAULT_PATH

# def test_get_config_path_custom(monkeypatch):  
#     monkeypatch.setenv("CONFIG_PATH", "/tmp/custom_config.ini")
#     path = get_config_path()
#     assert path == "/tmp/custom_config.ini"

def test_parse_config_file_not_found(tmp_path):
    non_existing_path = tmp_path / "not_here.ini"
    with pytest.raises(FileNotFoundError):
        parse_config(non_existing_path)

# def test_parse_config_is_directory(tmp_path):
#     with pytest.raises(OSError):  # Можно также: IsADirectoryError, но он не во всех Python-версиях
#         parse_config(tmp_path)  # tmp_path — это директория




# === ХЕЛПЕРЫ ===
def run_validator(tmp_path, config):
    def create_config(tmp_path, content: str) -> str:
        path = tmp_path / "config.ini"
        path.write_text(content.strip())
        return Path(str(path))
    
    path = create_config(tmp_path, config)
    new_config = parse_config(path)
    validator = ConfigValidator(new_config)
    validator.validate()
    return validator.errors

# === Тесты на парсинг ===
def test_parse_config_invalid(tmp_path):
    config = """
    [General]
    InvalidLineWithoutEquals
    """

    with pytest.raises(ValueError, match=r"Неподдерживаемая строка:"):
        run_validator(tmp_path, config=config)


# Отсутствуют обязательные секции
@pytest.mark.parametrize("value", ["General", "Watchdog"])
def test_missing_section(tmp_path, value): 
    config = VALID_BASE.replace(f"{value}", "")
    errors = run_validator(tmp_path, config=config)
    assert f"Missing {value}" in errors


# Отсутствуют обязательные параметры
@pytest.mark.parametrize("value", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_missing_general_parametr(tmp_path, value): 
    config = re.sub(rf"^{value}=.*\n?", "", VALID_BASE, flags=re.MULTILINE)
    errors = run_validator(tmp_path, config=config)
    assert f"Missing General.{value}" in errors

@pytest.mark.parametrize("value", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_missing_watchdog_parametr(tmp_path, value): 
    config = re.sub(rf"^{value}=.*\n?", "", VALID_BASE, flags=re.MULTILINE)
    errors = run_validator(tmp_path, config=config)
    assert f"Missing Watchdog.{value}" in errors


# Дублируем некоторые параметры
@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_duplicate_param_in_section_general(tmp_path, param):
    pattern = rf"(\[General\](?:\n.*?)*?)\n({re.escape(param)}=.*)"
    replacement = rf"\1\n\2\n{param}=DUPLICATE"
    config = re.sub(pattern, replacement, VALID_BASE, flags=re.MULTILINE)
    
    errors = run_validator(tmp_path, config=config)
    assert f"Repeated General.{param}" in errors

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_duplicate_param_in_section_watchdog(tmp_path, param):
    pattern = rf"(\[Watchdog\](?:\n.*?)*?)\n({re.escape(param)}=.*)"
    replacement = rf"\1\n\2\n{param}=DUPLICATE"
    config = re.sub(pattern, replacement, VALID_BASE, flags=re.MULTILINE)
    
    errors = run_validator(tmp_path, config=config)
    assert f"Repeated Watchdog.{param}" in errors


# Добавим недопустимый параметр в секцию
@pytest.mark.parametrize("wrong_section, param", [
    ("Watchdog", "ScanMemoryLimit"),
    ("General", "ConnectTimeout"),
])
def test_param_in_wrong_section(tmp_path, wrong_section, param):
    pattern = rf"(\[{wrong_section}\])"
    insertion = rf"{param}=WRONG"
    config = re.sub(pattern, rf"\1\n{insertion}", VALID_BASE)

    errors = run_validator(tmp_path, config=config)
    expected_error = f"Incorrect location {wrong_section}.{param}"
    assert expected_error in errors


# Добавим неизвестный параметр foo=bar в секцию [General]
def test_unknown_param_ignored(tmp_path):
    config = re.sub(r"(\[General\])", r"\1\nfoo=bar", VALID_BASE)
    errors = run_validator(tmp_path, config=config)

    assert not errors, "Unexpected error for unknown parameter"


# === ПРИМЕР ТЕСТА НА ИЗМЕНЕНИЕ ОДНОГО ПАРАМЕТРА ===
@pytest.mark.parametrize("value", ["99999", "abc"])
def test_scanmemorylimit_invalid(tmp_path, value):
    config = VALID_BASE.replace("ScanMemoryLimit=2048", f"ScanMemoryLimit={value}")
    errors = run_validator(tmp_path, config=config)
    assert "ScanMemoryLimit" in errors


@pytest.mark.parametrize("value", ["tar.gz", "exe"])
def test_packagetype_invalid(tmp_path, value):
    config = VALID_BASE.replace("PackageType=deb", f"PackageType={value}")
    errors = run_validator(tmp_path, config=config)
    assert "PackageType" in errors


@pytest.mark.parametrize("value", ["maybe", "123"])
def test_additionaldnslookup_invalid(tmp_path, value):
    config = VALID_BASE.replace("AdditionalDNSLookup=true", f"AdditionalDNSLookup={value}")
    errors = run_validator(tmp_path, config=config)
    assert "AdditionalDNSLookup" in errors


@pytest.mark.parametrize("value", ["/nonexistent/path", "relative/path"])
def test_coredumpspath_invalid(tmp_path, value):
    config = VALID_BASE.replace("CoreDumpsPath=/", f"CoreDumpsPath={value}")
    errors = run_validator(tmp_path, config=config)
    assert "CoreDumpsPath" in errors


@pytest.mark.parametrize("value", ["1234", "not-a-uuid"])
def test_machineid_invalid(tmp_path, value):
    config = VALID_BASE.replace("MachineId=7b5cc0e7-0205-48e1-bf63-347531eef193", f"MachineId={value}")
    errors = run_validator(tmp_path, config=config)
    assert "MachineId" in errors


@pytest.mark.parametrize("value", ["english_US", "!!"])
def test_locale_invalid(tmp_path, value):
    config = VALID_BASE.replace("Locale=en_US.UTF-8", f"Locale={value}")
    errors = run_validator(tmp_path, config=config)
    assert "Locale" in errors
