"""Плагины"""

import json
from .settings import MAX_PACKAGE_LENGTH, ENCODING
from log.log_decorator import log

@log
def get_msg(client):
    """
    Плагин, принимает сообщение в байтах и декодирует его в словарь.
    Возвращает ошибку значения, если на вход подано что-то другое.
    :param client:
    :return:
    """

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError

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
