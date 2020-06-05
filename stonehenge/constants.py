import pathlib
import os

OBJECT_NOT_FOUND_ERROR = 'Object not found'
PROJECT_DIR = pathlib.Path(__file__).parent.parent
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
