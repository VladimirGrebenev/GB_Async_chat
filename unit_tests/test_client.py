"""unittest client.py"""

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from ..client import server_answer, exist_client_msg
from ..common_files.settings import RESPONSE, ACTION, PRESENCE, TIME, USER, \
    ACCOUNT_NAME, ERROR


class TestClient(unittest.TestCase):
    """Тест класс клиента"""

    def test_server_answer_200(self):
        """Тест статуса ответа 200"""
        self.assertEqual(server_answer({RESPONSE: 200}), '200 : OK')

    def test_server_answer_400(self):
        """Тест статус ответа 400"""
        self.assertEqual(server_answer({RESPONSE: 400, ERROR: 'Bad request'}),
                         '400 : Bad request')

    def test_server_answer_absence_response(self):
        """Тест отсутствия RESPONSE"""
        self.assertRaises(ValueError, server_answer, {ERROR: 'Bad Request'})

    def test_exist_client_msg(self):
        """Тест создания сообщения о наличии клиента"""
        out_msg = exist_client_msg()
        out_msg[TIME] = 6.9
        self.assertEqual(out_msg, {ACTION: PRESENCE, TIME: 6.9,
                                   USER: {ACCOUNT_NAME: 'Guest'}})


if __name__ == '__main__':
    unittest.main()
