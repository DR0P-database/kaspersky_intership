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
VALID_DICT_CONFIG = {'General': {'__duplicates__': {'ScanMemoryLimit': 1, 'PackageType': 1, 'ExecArgMax': 1, 'AdditionalDNSLookup': 1, 'CoreDumps': 1, 'RevealSensitiveInfoInTraces': 1, 'ExecEnvMax': 1, 'MaxInotifyWatches': 1, 'CoreDumpsPath': 1, 'UseFanotify': 1, 'KsvlaMode': 1, 'MachineId': 1, 'StartupTraces': 1, 'MaxInotifyInstances': 1, 'Locale': 1}, 'ScanMemoryLimit': '2048', 'PackageType': 'rpm', 'ExecArgMax': '20', 'AdditionalDNSLookup': 'false', 'CoreDumps': 'no', 'RevealSensitiveInfoInTraces': 'true', 'ExecEnvMax': '50', 'MaxInotifyWatches': '300000', 'CoreDumpsPath': '/Users/macbookpro/Documents/kaspersky_intership/dumps', 'UseFanotify': 'yes', 'KsvlaMode': 'no', 'MachineId': '7b5cc0e7-0205-48e1-bf63-347531eef193', 'StartupTraces': 'false', 'MaxInotifyInstances': '2048', 'Locale': 'en_US.UTF-8'}, 'Watchdog': {'__duplicates__': {'ConnectTimeout': 1, 'MaxVirtualMemory': 1, 'MaxMemory': 1, 'PingInterval': 1}, 'ConnectTimeout': '20m', 'MaxVirtualMemory': 'auto', 'MaxMemory': '70.5', 'PingInterval': '3000'}}

def test_parse_config_file_not_found(tmp_path):
    non_existing_path = tmp_path / "not_here.ini"
    with pytest.raises(FileNotFoundError):
        parse_config(non_existing_path)

def run_validator(tmp_path, config):
    path = tmp_path / "config.ini"
    path.write_text(config.strip())
    parsed = parse_config(path)
    validator = ConfigValidator(parsed)
    validator.validate()

def test_parse_config_invalid(tmp_path):
    config = """
    [General]
    InvalidLineWithoutEquals
    """
    with pytest.raises(ValueError, match=r"Неподдерживаемая строка:"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("section", ["General", "Watchdog"])
def test_missing_section(tmp_path, section): 
    config = VALID_BASE.replace(f"[{section}]", "")
    with pytest.raises(ValueError, match=f"Отсутствует секция: {section}"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_missing_general_param(tmp_path, param): 
    config = re.sub(rf"^{param}=.*\n?", "", VALID_BASE, flags=re.MULTILINE)
    with pytest.raises(ValueError, match=f"{param}.*обязательный параметр"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_missing_watchdog_param(tmp_path, param): 
    config = re.sub(rf"^{param}=.*\n?", "", VALID_BASE, flags=re.MULTILINE)
    with pytest.raises(ValueError, match=f"{param}.*обязательный параметр"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_GENERAL)
def test_duplicate_param_general(tmp_path, param):
    pattern = rf"(\[General\](?:\n.*?)*?)\n({re.escape(param)}=.*)"
    replacement = rf"\1\n\2\n{param}=DUPLICATE"
    config = re.sub(pattern, replacement, VALID_BASE, flags=re.MULTILINE)
    with pytest.raises(ValueError, match=fr"{param}.*указан 2 раз"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("param", ConfigValidator.REQUIRED_PARAMS_WATCHDOG)
def test_duplicate_param_watchdog(tmp_path, param):
    pattern = rf"(\[Watchdog\](?:\n.*?)*?)\n({re.escape(param)}=.*)"
    replacement = rf"\1\n\2\n{param}=DUPLICATE"
    config = re.sub(pattern, replacement, VALID_BASE, flags=re.MULTILINE)
    with pytest.raises(ValueError, match=fr"{param}.*указан 2 раз"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("wrong_section, param", [
    ("Watchdog", "ScanMemoryLimit"),
    ("General", "ConnectTimeout"),
])
def test_param_wrong_section(tmp_path, wrong_section, param):
    config = re.sub(rf"\[{wrong_section}\]", rf"[{wrong_section}]\n{param}=WRONG", VALID_BASE)
    with pytest.raises(ValueError, match=fr"{param}.*не должен находиться в этой секции"):
        run_validator(tmp_path, config)

def test_unknown_param_ignored(tmp_path):
    config = re.sub(r"(\[General\])", r"\1\nfoo=bar", VALID_BASE)
    # Не должно быть исключения
    assert run_validator(tmp_path, config) == True

@pytest.mark.parametrize("value", ["99999", "abc"])
def test_scanmemorylimit_invalid(tmp_path, value):
    config = VALID_BASE.replace("ScanMemoryLimit=2048", f"ScanMemoryLimit={value}")
    with pytest.raises(ValueError, match="ScanMemoryLimit.*целым числом"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("value", ["tar.gz", "exe"])
def test_packagetype_invalid(tmp_path, value):
    config = VALID_BASE.replace("PackageType=deb", f"PackageType={value}")
    with pytest.raises(ValueError, match="PackageType.*одним из значений"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("value", ["maybe", "123"])
def test_additionaldnslookup_invalid(tmp_path, value):
    config = VALID_BASE.replace("AdditionalDNSLookup=true", f"AdditionalDNSLookup={value}")
    with pytest.raises(ValueError, match="AdditionalDNSLookup.*одним из значений"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("value", ["/nonexistent/path", "relative/path"])
def test_coredumpspath_invalid(tmp_path, value):
    config = VALID_BASE.replace("CoreDumpsPath=/", f"CoreDumpsPath={value}")
    with pytest.raises(ValueError, match="CoreDumpsPath.*абсолютным путем"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("value", ["1234", "not-a-uuid"])
def test_machineid_invalid(tmp_path, value):
    config = VALID_BASE.replace("MachineId=7b5cc0e7-0205-48e1-bf63-347531eef193", f"MachineId={value}")
    with pytest.raises(ValueError, match="MachineId.*UUID"):
        run_validator(tmp_path, config)

@pytest.mark.parametrize("value", ["english_US", "!!"])
def test_locale_invalid(tmp_path, value):
    config = VALID_BASE.replace("Locale=en_US.UTF-8", f"Locale={value}")
    with pytest.raises(ValueError, match="Locale.*RFC 3066"):
        run_validator(tmp_path, config)



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
