"""unittest server.py"""

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from ..server import process_client_msg
from ..common_files.settings import RESPONSE, ACTION, PRESENCE, TIME, USER, \
    ACCOUNT_NAME, ERROR


class TestServer(unittest.TestCase):
    """Тест класс сервера"""

    def setUp(self) -> None:
        self.ok_request = {RESPONSE: 200}
        self.bad_request = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_process_client_msg_200(self):
        """Обработка сообщения от клиента прошла успешно"""
        self.assertEqual(process_client_msg(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}),
            self.ok_request)

    def test_process_client_msg_unknown_user(self):
        """Неизвестный клиент USER"""
        self.assertEqual(process_client_msg(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Unknown'}}),
            self.bad_request)

    def test_process_client_msg_wrong_action(self):
        """Неизвестное действие ACTION"""
        self.assertEqual(process_client_msg(
            {ACTION: 'action', TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}),
            self.bad_request)

    def test_process_client_msg_absence_time(self):
        """Отсутствует TIME"""
        self.assertEqual(process_client_msg(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}),
            self.bad_request)


if __name__ == '__main__':
    unittest.main()
