import os
import re
import uuid

class ConfigValidator:
    BOOL_VALUES = {'true', 'false', 'yes', 'no'}
    RFC_3066_REGEX = re.compile(r'^[a-zA-Z]{1,3}(_[a-zA-Z0-9]{1,3})?(\.[a-zA-Z0-9-]+)?$')

    REQUIRED_SECTIONS = ['General', 'Watchdog']
    REQUIRED_PARAMS_GENERAL = ['ScanMemoryLimit', 'PackageType', 'ExecArgMax', 'AdditionalDNSLookup',
                               'CoreDumps', 'RevealSensitiveInfoInTraces', 'ExecEnvMax',
                               'MaxInotifyWatches', 'CoreDumpsPath', 'UseFanotify', 'KsvlaMode',
                               'MachineId', 'StartupTraces', 'MaxInotifyInstances', 'Locale']
    REQUIRED_PARAMS_WATCHDOG = ['ConnectTimeout', 'MaxVirtualMemory', 'MaxMemory', 'PingInterval']

    def __init__(self, config: dict):
        self.config = config

    def validate(self):
        for section in self.REQUIRED_SECTIONS:
            if section not in self.config:
                raise ValueError(f"Отсутствует секция: {section}")
        
        self._check_unexpected_parameters_and_duplicates()
        self._validate_general()
        self._validate_watchdog()
        return True

    def _check_unexpected_parameters_and_duplicates(self):
        expected = {
            'General': set(self.REQUIRED_PARAMS_GENERAL),
            'Watchdog': set(self.REQUIRED_PARAMS_WATCHDOG),
        }

        for section, params in self.config.items():
            if not isinstance(params, dict):
                continue

            duplicates = params.get('__duplicates__', {})
            for key, count in duplicates.items():
                if count > 1:
                    raise ValueError(f"{section}.{key} указан {count} раз(а)")

            for key in params:
                if key == '__duplicates__':
                    continue
                if section in expected and key not in expected[section]:
                    raise ValueError(f"{section}.{key} не должен находиться в этой секции")

    def _validate_general(self):
        section = 'General'
        if section not in self.config:
            return

        for param in self.REQUIRED_PARAMS_GENERAL:
            if param not in self.config[section]:
                raise ValueError(f"{section}.{param} обязательный параметр, отсутствует")

        self._check_int_range(section, 'ScanMemoryLimit', 1024, 8192)
        self._check_enum(section, 'PackageType', {'rpm', 'deb'})
        self._check_int_range(section, 'ExecArgMax', 10, 100)
        self._check_bool(section, 'AdditionalDNSLookup')
        self._check_bool(section, 'CoreDumps')
        self._check_bool(section, 'RevealSensitiveInfoInTraces')
        self._check_int_range(section, 'ExecEnvMax', 10, 100)
        self._check_int_range(section, 'MaxInotifyWatches', 1000, 1_000_000)

        path = self._get_value(section, 'CoreDumpsPath')
        if path and (not os.path.isabs(path) or not os.path.isdir(path)):
            raise ValueError(f"{section}.CoreDumpsPath должен быть существующим абсолютным путем к директории")

        self._check_bool(section, 'UseFanotify')
        self._check_bool(section, 'KsvlaMode')

        machine_id = self._get_value(section, 'MachineId')
        if machine_id and not self._is_uuid(machine_id):
            raise ValueError(f"{section}.MachineId должен быть валидным UUID")

        self._check_bool(section, 'StartupTraces')
        self._check_int_range(section, 'MaxInotifyInstances', 1024, 8192)

        locale = self._get_value(section, 'Locale')
        if locale and not self._is_valid_locale(locale):
            raise ValueError(f"{section}.Locale должен соответствовать формату RFC 3066")

    def _validate_watchdog(self):
        section = 'Watchdog'
        if section not in self.config:
            return

        for param in self.REQUIRED_PARAMS_WATCHDOG:
            if param not in self.config[section]:
                raise ValueError(f"{section}.{param} обязательный параметр, отсутствует")

        value = self._get_value(section, 'ConnectTimeout')
        if not value or not re.fullmatch(r'\d+m', value):
            raise ValueError(f"{section}.ConnectTimeout должен быть в формате \"<число>m\", например \"60m\"")
        try:
            num = int(value[:-1])
            if not (1 <= num <= 120):
                raise ValueError(f"{section}.ConnectTimeout должен быть числом от 1 до 120 с суффиксом \"m\"")
        except ValueError:
            raise ValueError(f"{section}.ConnectTimeout значение до \"m\" должно быть числом")

        for key in ('MaxVirtualMemory', 'MaxMemory'):
            self._check_memory_value(section, key)

        self._check_int_range(section, 'PingInterval', 100, 10000)

    def _get_value(self, section, key):
        return self.config.get(section, {}).get(key, '').strip()

    def _check_int_range(self, section, key, min_val, max_val):
        value = self._get_value(section, key)
        if not value.isdigit() or not (min_val <= int(value) <= max_val):
            raise ValueError(f"{section}.{key} должен быть целым числом в интервале [{min_val}-{max_val}]")

    def _check_bool(self, section, key):
        value = self._get_value(section, key).lower()
        if value not in self.BOOL_VALUES:
            raise ValueError(f"{section}.{key} должен быть одним из значений {self.BOOL_VALUES}")

    def _check_enum(self, section, key, allowed):
        value = self._get_value(section, key).lower()
        if value not in allowed:
            raise ValueError(f"{section}.{key} должен быть одним из значений {allowed}")

    def _check_memory_value(self, section, key):
        value = self._get_value(section, key).lower()
        if value in {'off', 'auto'}:
            return
        try:
            fval = float(value)
            if not (0 < fval <= 100):
                raise ValueError
        except ValueError:
            raise ValueError(f"{section}.{key} должен быть \"off\", \"auto\", или вещественным числом в интервале (0, 100]")

    def _is_uuid(self, value):
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    def _is_valid_locale(self, value):
        return bool(self.RFC_3066_REGEX.match(value))
