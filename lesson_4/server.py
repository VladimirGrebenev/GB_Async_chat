"""Программа-сервер"""

import socket
import sys
import json
from common_files.settings import ACTION, ACCOUNT_NAME, RESPONSE, \
    MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, \
    DEFAULT_IP_ADDRESS
from common_files.plugins import get_msg, send_msg


def process_client_msg(msg):
    """
    Обработка сообщений от клиентов. На вход получаем сообщение от клиента -
    словарь. Проверяем его корректность и возвращаем ответ клиенту - словарь.

    :param msg:
    :return:
    """
    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg \
            and USER in msg and msg[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


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
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('Параметр -\'p\' необходимо указать номер порта. '
              'Пример: server.py -p 8079 -a 192.168.1.2')
        sys.exit(1)
    except ValueError:
        print('Второй аргумент - число, адрес порта, должен быть в диапазоне '
              'от 1024 до 65535. Пример: server.py -p 8079 -a 192.168.1.2')
        sys.exit(1)

    # Установка IP адреса для подключения клиента
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = DEFAULT_IP_ADDRESS

    except IndexError:
        print('После параметра \'a\'- необходимо указать адрес, который '
              'будет слушать сервер. Пример: server.py -p 8079 -a 192.168.1.2')
        sys.exit(1)

    # Активация сокета

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Активация прослушивания порта

    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        try:
            msg_from_client = get_msg(client)
            print(msg_from_client)
            # {'action': 'presence', 'time': 1573760672.167031, 'user': {
            # 'account_name': 'Guest'}}
            response = process_client_msg(msg_from_client)
            send_msg(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Некорректное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()
