import configparser
from pathlib import Path

DEFAULTS = {
    'display': {
        'max_items': '5',
    },
    'storage': {
        'db_path': '~/doterm.sqlite',
    },
}


def load_config():
    config = configparser.ConfigParser()
    for section, values in DEFAULTS.items():
        config[section] = values
    config_path = Path('~/.doterm.rc').expanduser()
    if config_path.exists():
        config.read(config_path)
    return config


def get_db_path(config=None):
    if config is None:
        config = load_config()
    return Path(config['storage']['db_path']).expanduser()


def get_max_items(config=None):
    if config is None:
        config = load_config()
    return config.getint('display', 'max_items')
