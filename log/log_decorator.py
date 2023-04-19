import logging
import log.client_log_config
import log.server_log_config
import inspect
import traceback


def log(func):
    def call_func(*args, **kwargs):
        if inspect.getfile(func).endswith('client.py'):
            # Функция вызвана в модуле client.py
            LOGGER = logging.getLogger('client_log')
        else:
            # Функция вызвана в модуле server.py
            LOGGER = logging.getLogger('server_log')

        func_result = func(*args, **kwargs)
        sep = '\\'
        stack = traceback.extract_stack()
        LOGGER.debug(f'Функция {func.__name__} '
                     f'из модуля {inspect.getfile(func).split(sep)[-1]}. '
                     f'Вызвана из функции {stack[-2][2]}'
                     f' c аргументами {args}, {kwargs} '
                     f'в модуле {stack[-2][0].split(sep)[-1]}.')
        return func_result

    return call_func
