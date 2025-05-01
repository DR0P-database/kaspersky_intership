import os
from dotenv import load_dotenv

from validator import ConfigValidator


DEFAULT_PATH = '/var/opt/kaspersky/config.ini'



def get_config_path():
    load_dotenv()  # Подгружает все что есть в .env и в окружении автоматически
    path_to_config=os.getenv('CONFIG_PATH', DEFAULT_PATH)
    # if not os.path.exists(path_to_config):
    #     raise FileNotFoundError(f"Config file not found: {path_to_config}")
    return path_to_config

def parse_config(path_to_config: str) -> dict:
    result = {}
    current_section = None

    with open(path_to_config, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line or line.startswith(';') or line.startswith('#'):
                continue

            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                result[current_section] = {}
                result[current_section]['__duplicates__'] = {}
            elif '=' in line and current_section:
                key, value = map(str.strip, line.split('=', 1))
                section = result[current_section]

                if key in section:
                    # Увеличиваем счётчик дубликатов
                    section['__duplicates__'][key] = section['__duplicates__'].get(key, 1) + 1
                else:
                    section['__duplicates__'][key] = 1

                section[key] = value
            else:
                raise ValueError(f"Неподдерживаемая строка: {line}")

    return result


def get_config() -> dict:
    """Получает конфигурацию, объединяя путь и парсинг."""
    config_path = get_config_path()
    return parse_config(config_path)


if __name__ == "__main__":
    config = get_config()
    # print(config)
    validator = ConfigValidator(config)
    if validator.validate():
        print("Успешно")
    else:
        print(validator.errors)