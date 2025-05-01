from framework.settings import get_config

config: dict = get_config()

template: dict = {
    'General': ['ScanMemoryLimit', 'PackageType', 'ExecArgMax', 'AdditionalDNSLookup',  'CoreDumps', 'RevealSensitiveInfoInTraces', 'ExecEnvMax', 'MaxInotifyWatches', 'CoreDumpsPath', 'UseFanotify', 'KsvlaMode', 'MachineId', 'StartupTraces', 'MaxInotifyInstances', 'Locale'],
    'Watchdog': ['ConnectTimeout', 'MaxVirtualMemory', 'MaxMemory', 'PingInterval']
}

def test_ini_file_exists():
    assert config, "config.ini is empty or missing"

# def test_ini_has_database_section():
#     with open("config.ini", "r") as f:
#         content = f.read()
#     assert "database" in config, "Missing [database] section"

def test_ini_database_keys():
    required_keys = ["host", "port", "user", "password"]
    with open("config.ini", "r") as f:
        lines = f.readlines()

    in_database = False
    keys_found = set()

    for line in lines:
        line = line.strip()

        if line.startswith("[") and line.endswith("]"):
            in_database = (line == "[database]")
            continue

        if in_database and "=" in line:
            key, _ = map(str.strip, line.split("=", 1))
            keys_found.add(key)

    for key in required_keys:
        assert key in keys_found, f"Missing key: {key} in [database]"
