import copy

import pytest

from framework.tools import SingleInsertDict

VALID_BASE = """
[General]
ScanMemoryLimit=2048
PackageType=deb
ExecArgMax=20
AdditionalDNSLookup=true
CoreDumps=no
RevealSensitiveInfoInTraces=yes
ExecEnvMax=50
MaxInotifyWatches=300000
CoreDumpsPath=/var/opt/kaspersky/dumps
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
"""
VALID_DICT_CONFIG = {
    "General": {
        "ScanMemoryLimit": "2048",
        "PackageType": "deb",
        "ExecArgMax": "20",
        "AdditionalDNSLookup": "true",
        "CoreDumps": "no",
        "RevealSensitiveInfoInTraces": "yes",
        "ExecEnvMax": "50",
        "MaxInotifyWatches": "300000",
        "CoreDumpsPath": "/var/opt/kaspersky/dumps",
        "UseFanotify": "no",
        "KsvlaMode": "no",
        "MachineId": "7b5cc0e7-0205-48e1-bf63-347531eef193",
        "StartupTraces": "false",
        "MaxInotifyInstances": "2048",
        "Locale": "en_US.UTF-8",
    },
    "Watchdog": {
        "ConnectTimeout": "30m",
        "MaxVirtualMemory": "auto",
        "MaxMemory": "off",
        "PingInterval": "3000",
    },
}


@pytest.fixture
def valid_config_dict(tmp_path):
    # Создание копии конфига
    config = copy.deepcopy(VALID_DICT_CONFIG)

    # Создание временной директории
    dumps_dir = tmp_path / "dumps"
    dumps_dir.mkdir()

    # Обновление пути
    config["General"]["CoreDumpsPath"] = str(dumps_dir)
    for k, v in config.items():
        config[k] = SingleInsertDict(v)

    return config
