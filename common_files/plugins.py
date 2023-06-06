"""Плагины"""

import json
import sys
from .settings import *
from log.log_decorator import log
sys.path.append('../')

@log
def get_msg(client):
    """
    Плагин, принимает сообщение в байтах и декодирует его в словарь.
    Возвращает ошибку значения, если на вход подано что-то другое.
    :param client:
    :return:
    """

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_msg(sock, message):
    """
    Плагин принимает сообщение на вход в виде словаря, кодирует и
    отправляет его.
    :param sock:
    :param message:
    :return:
    """
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
