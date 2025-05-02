import pytest
import copy

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
'''
VALID_DICT_CONFIG = {'General': {'__duplicates__': {'ScanMemoryLimit': 1, 'PackageType': 1, 'ExecArgMax': 1, 'AdditionalDNSLookup': 1, 'CoreDumps': 1, 'RevealSensitiveInfoInTraces': 1, 'ExecEnvMax': 1, 'MaxInotifyWatches': 1, 'CoreDumpsPath': 1, 'UseFanotify': 1, 'KsvlaMode': 1, 'MachineId': 1, 'StartupTraces': 1, 'MaxInotifyInstances': 1, 'Locale': 1}, 'ScanMemoryLimit': '2048', 'PackageType': 'deb', 'ExecArgMax': '20', 'AdditionalDNSLookup': 'true', 'CoreDumps': 'no', 'RevealSensitiveInfoInTraces': 'yes', 'ExecEnvMax': '50', 'MaxInotifyWatches': '300000', 'CoreDumpsPath': '/var/opt/kaspersky/dumps', 'UseFanotify': 'no', 'KsvlaMode': 'no', 'MachineId': '7b5cc0e7-0205-48e1-bf63-347531eef193', 'StartupTraces': 'false', 'MaxInotifyInstances': '2048', 'Locale': 'en_US.UTF-8'}, 'Watchdog': {'__duplicates__': {'ConnectTimeout': 1, 
'MaxVirtualMemory': 1, 'MaxMemory': 1, 'PingInterval': 1}, 'ConnectTimeout': '30m', 'MaxVirtualMemory': 'auto', 'MaxMemory': 'off', 'PingInterval': '3000'}}

@pytest.fixture
def valid_config_dict(tmp_path):
    # Создание копии конфига
    config = copy.deepcopy(VALID_DICT_CONFIG)
    
    # Создание временной директории
    dumps_dir = tmp_path / "dumps"
    dumps_dir.mkdir()
    
    # Обновление пути
    config['General']['CoreDumpsPath'] = str(dumps_dir)

    return config
