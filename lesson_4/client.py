"""Программа-клиент"""

import sys
import json
import socket
import time
from common_files.settings import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common_files.plugins import get_msg, send_msg


def exist_client_msg(account_name='Guest'):
    """
    Функция создаёт сообщение в нужном формате о наличии клиента
    :param account_name:
    :return:
    """
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {
    # 'account_name': 'Guest'}}
    out_msg = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return out_msg


def server_answer(msg):
    """
    Проверка статуса ответа сервера
    :param msg:
    :return:
    """
    if RESPONSE in msg:
        if msg[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {msg[ERROR]}'
    raise ValueError


def main():
    """Запуск клиента"""

    # Установка аргументов из командной строки
    # client.py 192.168.1.2 8079
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('Второй аргумент - число, адрес порта, должен быть в диапазоне'
              ' от 1024 до 65535.')
        sys.exit(1)

    # Активация сокета и обмен сообщениями
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    msg_to_server = exist_client_msg()
    send_msg(transport, msg_to_server)
    try:
        status_server_answer = server_answer(get_msg(transport))
        print(status_server_answer)
    except (ValueError, json.JSONDecodeError):
        print('Попытка декодировать сообщение от сервера потерпела неудачу.')


if __name__ == '__main__':
    main()
