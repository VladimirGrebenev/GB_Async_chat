"""Программа-клиент"""

import sys
import json
import socket
import time
from common_files.settings import ACTION, ACCOUNT_NAME, RESPONSE, \
    MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, \
    DEFAULT_IP_ADDRESS, MESSAGE, MESSAGE_TEXT, SENDER
from common_files.plugins import get_msg, send_msg
import logging
import log.client_log_config
from log.log_decorator import log

CLIENT_LOGGER = logging.getLogger('client_log')


@log
def msg_from_server(msg):
    """Функция воспроизведения всех сообщений с сервера"""
    # if ACTION in msg and msg[ACTION] == MESSAGE and \
    #         SENDER in msg and MESSAGE_TEXT in msg:
    print(f'Сообщение от {msg[SENDER]}:\n{msg[MESSAGE_TEXT]}')
    CLIENT_LOGGER.info(f'Сообщение от {msg[SENDER]}:\n{msg[MESSAGE_TEXT]}')
    # else:
    #     CLIENT_LOGGER.error(f'Ошибка сообщения сервера: {msg}')

@log
def write_msg(sock, account_name='Guest'):
    """Функция ввода текста пользователя.
       Если ввести 'exit', то клиент отключится.
    """
    msg = input('Ваше сообщение (чтобы выйти - exit): ')
    if msg == 'exit':
        sock.close()
        CLIENT_LOGGER.info('Клиент вышел')
        print('Вы вышли')
        sys.exit(0)
    else:
        msg_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            ACCOUNT_NAME: account_name,
            MESSAGE_TEXT: msg
        }
        CLIENT_LOGGER.debug(f'msg_dict: {msg_dict}')
    return msg_dict



@log
def exist_client_msg(account_name='Guest'):
    """
    Функция создаёт сообщение в нужном формате о наличии клиента
    :param account_name:
    :return:
    """

    out_msg = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сообщение {PRESENCE} о наличии клиента '
                        f'{account_name} создано')
    return out_msg

@log
def server_answer(msg):
    """
    Проверка статуса ответа сервера
    :param msg:
    :return:
    """
    CLIENT_LOGGER.debug('Проверка статуса ответа сервера')
    if RESPONSE in msg:
        if msg[RESPONSE] == 200:
            CLIENT_LOGGER.debug('Статус ответа сервера - 200 : OK')
            return '200 : OK'
        else:
            CLIENT_LOGGER.error(f'Статус ответа сервера - 400 : {msg[ERROR]}')
        return f'400 : {msg[ERROR]}'
    raise ValueError


def main():
    """Запуск клиента"""

    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
        CLIENT_LOGGER.critical(f'Установил значения адреса и порта сервера '
                               f'по умолчанию {server_address}:{server_port}')
    except ValueError:
        CLIENT_LOGGER.critical('адрес порта должен быть от 1024 до 65535.')
        sys.exit(1)

    # Активация сокета и обмен сообщениями

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    while True:
        # try:
        send_msg(transport, write_msg(transport))
        msg_from_server(get_msg(transport))

        # except Exception:
        #     CLIENT_LOGGER.error(f'Потеряна связь {server_address}'
        #                         f' {server_port} ')
        #     sys.exit(1)


if __name__ == '__main__':
    main()
