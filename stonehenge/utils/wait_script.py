import socket
import time
import random

from stonehenge.utils.common import get_config

if __name__ == '__main__':
    config = get_config()
    postgres = config['postgres']
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((postgres['host'], postgres['port']))
                print('Successfully started postgres')
                break
        except socket.error:
            print('Waiting for postgres')
            time.sleep(0.5 + (random.randint(0, 100) / 1000))
