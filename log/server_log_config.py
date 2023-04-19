import logging
import logging.handlers
import sys
import os

sys.path.append('../')

FORMAT_LOG = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
FILE_PATH_NAME = os.path.join(PATH, 'server_log.log')

FILE_LOG = logging.handlers.TimedRotatingFileHandler(FILE_PATH_NAME,
                                                     encoding='utf8',
                                                     interval=1, when='D')
FILE_LOG.setFormatter(FORMAT_LOG)

LOG_LEVEL = logging.DEBUG

SERVER_LOG = logging.getLogger('server_log')
SERVER_LOG.addHandler(FILE_LOG)
SERVER_LOG.setLevel(LOG_LEVEL)

if __name__ == '__main__':
    SERVER_LOG.debug('test debug')
    SERVER_LOG.info('test info message')
    SERVER_LOG.error('test error')
    SERVER_LOG.critical('test critical error')
