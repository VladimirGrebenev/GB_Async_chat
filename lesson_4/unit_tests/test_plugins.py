"""unittest common_files.plugins.py"""

import unittest
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from ..common_files.plugins import get_msg, send_msg
from ..common_files.settings import RESPONSE, ACTION, PRESENCE, TIME, USER, \
    ACCOUNT_NAME, ERROR, ENCODING


class MyTestSocket:
    """
    Тестовый класс сокета для отправки и получения,
    при создании требует словарь, который будет приниматься
    через тестируемую функцию.
    """
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_msg = None
        self.received_msg = None

    def send(self, msg_to_send):
        """
        Тестовая функция для кодировки и отправки сообщения.
        :param msg_to_send:
        :return:
        """
        json_test_msg = json.dumps(self.test_dict)
        # кодируем сообщение
        self.encoded_msg = json_test_msg.encode(ENCODING)
        # сохраняем в сокет
        self.received_msg = msg_to_send

    def recv(self, max_len):
        """
        Получаем и декодируем сообщение из сокета
        :param max_len:
        :return:
        """
        json_test_msg = json.dumps(self.test_dict)
        return json_test_msg.encode(ENCODING)


class TestsPlugins(unittest.TestCase):
    """
    Тестовый класс для common_files.plugins.py.
    """

    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 6.9,
        USER: {
            ACCOUNT_NAME: 'Guest'
        }
    }
    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_error = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_msg(self):
        """
        Тестируем plugin отправки
        :return:
        """
        # создаём экземпляр тестового сокета
        test_socket = MyTestSocket(self.test_dict_send)
        # вызываем тестируемую функцию в тестовом сокете
        send_msg(test_socket, self.test_dict_send)
        # сравниваем сообщения закодированное и тестируемой функции
        self.assertEqual(test_socket.encoded_msg,
                         test_socket.received_msg)

    def test_get_msg(self):
        """
        Тест плагина приёма сообщения
        :return:
        """
        test_sock_ok = MyTestSocket(self.test_dict_recv_ok)
        test_sock_err = MyTestSocket(self.test_dict_recv_error)
        # тест корректной расшифровки корректного словаря
        self.assertEqual(get_msg(test_sock_ok), self.test_dict_recv_ok)
        # тест корректной расшифровки ошибочного словаря
        self.assertEqual(get_msg(test_sock_err), self.test_dict_recv_error)


if __name__ == '__main__':
    unittest.main()
