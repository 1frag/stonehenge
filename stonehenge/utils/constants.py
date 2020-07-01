import pathlib
import os

HOST = os.getenv('HOST', '127.0.0.1:8080')
PROJECT_DIR = pathlib.Path(__file__).parent.parent
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
VK_CLIENT_ID = os.getenv('VK_CLIENT_ID')
VK_CLIENT_SECRET = os.getenv('VK_CLIENT_SECRET')
VK_VERSION_API = os.getenv('VK_VERSION_API')
YANDEX_ID = os.getenv('YANDEX_ID')
YANDEX_PWD = os.getenv('YANDEX_PWD')
YANDEX_ACCESS_TOKEN = os.getenv('YANDEX_ACCESS_TOKEN')
PRODUCTION = os.getenv('PRODUCTION', False)
