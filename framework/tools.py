import os
from dotenv import load_dotenv

DEFAULT_PATH = '/var/opt/kaspersky/config.ini'

from collections import UserDict

class SingleInsertDict(UserDict):
    def __setitem__(self, key, value):
        if key in self.data:
            raise KeyError(f"Повторное добавление ключа запрещено: {key}")
        super().__setitem__(key, value)



def get_config_path():
    load_dotenv()  # Подгружает все что есть в .env и в окружении автоматически
    path_to_config=os.getenv('CONFIG_PATH', DEFAULT_PATH)

    return path_to_config

def parse_config(path_to_config) -> dict:
    result = SingleInsertDict()
    current_section = None

    with open(path_to_config, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith(';') or line.startswith('#'):
                continue

            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                result[current_section] = SingleInsertDict()
            elif '=' in line:
                if not current_section:
                    # Пропускаем параметр вне секции
                    continue
                
                key, value = map(str.strip, line.split('=', 1))
                section = result[current_section]

                section[key] = value
            
            else:
                raise ValueError(f"Неподдерживаемая строка: {line}")

    return result


def get_config() -> dict:
    """Получает конфигурацию, объединяя путь и парсинг."""
    config_path = get_config_path()
    return parse_config(config_path)
