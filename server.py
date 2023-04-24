"""Программа-сервер"""

import socket
import sys
import json
import time

import select

from common_files.settings import ACTION, ACCOUNT_NAME, RESPONSE, \
    MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, \
    DEFAULT_IP_ADDRESS, MESSAGE, MESSAGE_TEXT, SENDER
from common_files.plugins import get_msg, send_msg
import logging
import log.server_log_config
from log.log_decorator import log

SERVER_LOGGER = logging.getLogger('server_log')


@log
def process_client_msg(msg, msg_list, client):
    """
    Обработка сообщений от клиента. На вход получаем сообщение от клиента -
    словарь. Проверяем его корректность и возвращаем ответ клиенту - словарь.
    :param msg:
    :param msg_list:
    :param client:
    :return:
    """
    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg \
            and USER in msg and msg[USER][ACCOUNT_NAME] == 'Guest':
        send_msg(client, {RESPONSE: 200})
        return
    elif ACTION in msg and msg[ACTION] == MESSAGE and TIME in msg and \
            MESSAGE_TEXT in msg:
        msg_list.append((msg[ACCOUNT_NAME], msg[MESSAGE_TEXT]))
        return
    else:
        send_msg(client, {RESPONSE: 400, ERROR: 'Bad Request'})
        return


def main():
    """
    Запуск сервера. Установка аргументов из командной строки.
    Пример: server.py -p 8079 -a 192.168.1.2
    :return:
    """

    # Установка порта для сетевого взаимодействия
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
            SERVER_LOGGER.info(f'Установлен порт {listen_port}')
        else:
            listen_port = DEFAULT_PORT
            SERVER_LOGGER.info(f'Установлен DEFAULT_PORT {DEFAULT_PORT}')
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        SERVER_LOGGER.critical(f'Параметр -\'p\' необходимо указать номер '
                               'порта. Пример: server.py -p 8079 -a '
                               '192.168.1.2')
        sys.exit(1)
    except ValueError:
        SERVER_LOGGER.critical(f'Второй аргумент - число, адрес порта, '
                               'должен быть в диапазоне от 1024 до 65535. '
                               'Пример: server.py -p 8079 -a 192.168.1.2')
        sys.exit(1)

    # Установка IP адреса для подключения клиента
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
            SERVER_LOGGER.info(f'Установлен IP адрес {listen_address}')
        else:
            listen_address = DEFAULT_IP_ADDRESS
            SERVER_LOGGER.info(
                f'Установлен DEFAULT_IP_ADDRESS {DEFAULT_IP_ADDRESS}')

    except IndexError:
        SERVER_LOGGER.critical(f'После параметра \'a\'- необходимо указать '
                               f'адрес, который будет слушать сервер. '
                               f'Пример: server.py -p 8079 -a 192.168.1.2')
        sys.exit(1)

    # список клиентов и список сообщений
    clients = []
    messages = []

    # Активация сокета
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Таймаут для операций с сокетом
    transport.settimeout(1)

    # Активация прослушивания порта
    transport.listen(MAX_CONNECTIONS)

    while True:
        try:
            # Проверка подключений
            client, client_address = transport.accept()
        except OSError as e:
            pass  # timeout вышел
        else:
            SERVER_LOGGER.info(f'Связь установлена: {client_address}')
            clients.append(client)

        read_list = []
        write_list = []

        try:
            if clients:
                read_list, write_list, e = select.select(clients,
                                                         clients, [], 0)
        except OSError as e:
            pass

        if read_list:
            for client in read_list:
                try:
                    process_client_msg(get_msg(client), messages, client)
                except:
                    clients.remove(client)

        if messages and write_list:
            msg = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1]
            }
            del messages[0]
            for client in write_list:
                try:
                    send_msg(client, msg)
                except Exception:
                    clients.remove(client)


if __name__ == '__main__':
    main()
