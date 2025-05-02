from .tools import get_config
from .validator import ConfigValidator

config = get_config()
validator = ConfigValidator(config)

if validator.validate():
    print("Успешно")
else:
    print(validator.errors)