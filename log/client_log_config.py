import logging
import sys
import os

sys.path.append('../')

FORMAT_LOG = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
FILE_PATH_NAME = os.path.join(PATH, 'client_log.log')

FILE_LOG = logging.FileHandler(FILE_PATH_NAME, encoding='utf8')
FILE_LOG.setFormatter(FORMAT_LOG)

LOG_LEVEL = logging.DEBUG

CLIENT_LOG = logging.getLogger('client_log')
CLIENT_LOG.addHandler(FILE_LOG)
CLIENT_LOG.setLevel(LOG_LEVEL)

if __name__ == '__main__':
    CLIENT_LOG.debug('test debug')
    CLIENT_LOG.info('test info message')
    CLIENT_LOG.error('test error')
    CLIENT_LOG.critical('test critical error')
