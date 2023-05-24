"""Программа-сервер"""

import socket
import sys
import argparse
import select
from common_files.settings import *
from common_files.plugins import get_msg, send_msg
import logging
import log.server_log_config
from log.log_decorator import log
from metacls import ServerVerifier

# Активация настроек логирования для сервера.
SERVER_LOGGER = logging.getLogger('server_log')


@log
def analyze_args():
    """Анализатор аргументов при запуске в коммандной строке"""
    analyzer = argparse.ArgumentParser()
    analyzer.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    analyzer.add_argument('-a', default='', nargs='?')
    namespace = analyzer.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    # проверяем корректность полученного номера порта.
    if not 1023 < listen_port < 65536:
        SERVER_LOGGER.critical(
            f'Некорректный номер порта {listen_port}. '
            f'Номер порта должен быть с 1024 по 65535.')
        sys.exit(1)

    return listen_address, listen_port


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            SERVER_LOGGER.critical(
                f'Некорректный номер порта {value}. '
                f'Номер порта должен быть с 1024 по 65535.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port):
        self.addr = listen_address
        self.port = listen_port
        self.clients = []
        self.msgs = []
        self.users_names = dict()

    def init_socket(self):
        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес для подключения: {self.addr}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        # Подготовка сокета
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            # Ожидаем подключения за отведённый таймаут.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Соединение установлено '
                                   f'с клиентом {client_address}')
                # добавляем клиента в список
                self.clients.append(client)

            to_receive_lst = []
            to_send_lst = []
            err_lst = []
            # Проверка на наличие клиентов в ожидании
            try:
                if self.clients:
                    to_receive_lst, to_send_lst, err_lst = select.select(
                        self.clients,
                        self.clients,
                        [], 0)
            except OSError:
                pass

            # получаем сообщения и если ловим исключение, то клиент исключается
            # из списка.
            if to_receive_lst:
                for client_with_msg in to_receive_lst:
                    try:
                        self.make_client_msg(get_msg(client_with_msg),
                                             client_with_msg)
                    except Exception:
                        SERVER_LOGGER.info(f'Клиент '
                                           f'{client_with_msg.getpeername()} '
                                           f'отключился.')
                        self.clients.remove(client_with_msg)

            # Обработка сообщений.
            for item in self.msgs:
                try:
                    self.make_msg(item, to_send_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом {item[RECIPIENT]}'
                                       f' потеряна.')
                    self.clients.remove(self.users_names[item[RECIPIENT]])
                    del self.users_names[item[RECIPIENT]]
            self.msgs.clear()

    def make_msg(self, msg, listen_socks):
        """
        Функция для отправки сообщения конкретному клиенту по имени.
        На вход получает сообщение, словарь с зарегистрированными именами
        пользователей,и сокеты.
        :param msg:
        :param listen_socks:
        :return:
        """
        if msg[RECIPIENT] in self.users_names and self.users_names[
            msg[RECIPIENT]] \
                in listen_socks:
            send_msg(self.users_names[msg[RECIPIENT]], msg)
            SERVER_LOGGER.info(
                f'Cообщение отправлено клиенту {msg[RECIPIENT]} '
                f'от клиента {msg[SENDER]}.')
        elif msg[RECIPIENT] in self.users_names and self.users_names[
            msg[RECIPIENT]] \
                not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Клиент {msg[RECIPIENT]} не существует на сервере, '
                f'сообщение не доставлено')

    def make_client_msg(self, msg, client):
        """
        Обработка сообщений от клиента. На вход получаем сообщение от клиента -
        словарь. Проверяем его корректность и возвращаем ответ клиенту
         - словарь.
        """

        SERVER_LOGGER.debug(f'Разбор сообщения: {msg} ')

        if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg \
                and USER in msg:
            # Если пользователя нет в списке, то добавляем его.
            # Если такой есть, то говорим, что имя занято и завершаем
            # соединение.
            if msg[USER][USER_NAME] not in self.users_names.keys():
                self.users_names[msg[USER][USER_NAME]] = client
                send_msg(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такой юзер уже существует'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если сообщение имеет все параметры,
        # то добавляем в список сообщений на доставку.
        elif ACTION in msg and msg[ACTION] == MSG and \
                RECIPIENT in msg and TIME in msg \
                and SENDER in msg and MSG_TEXT in msg:
            self.msgs.append(msg)
            return
        # Если клиент выбрал команду exit
        elif ACTION in msg and msg[ACTION] == EXIT and USER_NAME in msg:
            self.clients.remove(self.users_names[USER_NAME])
            self.users_names[USER_NAME].close()
            del self.users_names[USER_NAME]
            return
        # В остальных случаях, констатируем некорректный запрос
        else:
            response = RESPONSE_400
            response[ERROR] = 'Получен некорректный запрос к серверу.'
            send_msg(client, response)
            return


def main():
    """
    Устанавливаем паремтры для сервера из командной строки, если запуск
     без параметров, то устанавливаем параметры по умолчанию.
    """
    listen_address, listen_port = analyze_args()

    # Создаём экземпляр класса Server.
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
