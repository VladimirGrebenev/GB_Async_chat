"""Программа-клиент"""

import sys
import json
import socket
import time
import argparse
import logging
import threading
import log.client_log_config
from common_files.settings import DEFAULT_PORT, DEFAULT_IP_ADDRESS, ACTION, \
    TIME, USER, USER_NAME, SENDER, PRESENCE, RESPONSE, \
    ERROR, MSG, MSG_TEXT, RECIPIENT, EXIT
from common_files.plugins import get_msg, send_msg
from common_files.exceptions import WrongDataRecivedError, \
    RequiredFieldAbsent, ServerError
from log.log_decorator import log
from metacls import ClientVerifier

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, user_name, sock):
        self.user_name = user_name
        self.sock = sock
        super().__init__()

    def make_exit_msg(self):
        """Для создания сообщения о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            USER_NAME: self.user_name
        }



    def make_msg(self):
        """
        Функция для формирования сообщения для отправки на сервер
        :param sock:
        :param user_name:
        :return:
        """
        to_recipient = input('Введите имя реципиента: ')
        msg = input('Введите сообщение: ')
        msg_dict = {
            ACTION: MSG,
            SENDER: self.user_name,
            RECIPIENT: to_recipient,
            TIME: time.time(),
            MSG_TEXT: msg
        }
        CLIENT_LOGGER.debug(f'Словарь сообщения: {msg_dict}')
        try:
            send_msg(self.sock, msg_dict)
            CLIENT_LOGGER.info(f'Ушло сообщение для реципиента {to_recipient}')
        except:
            CLIENT_LOGGER.critical('Соединение с сервером потеряно.')
            sys.exit(1)



    def pip_boy_3000(self):
        """Функция для отправки команд пользователем"""
        self.help_me()
        while True:
            command = input('Введите команду: ')
            if command == 'msg':
                self.make_msg()
            elif command == 'help':
                self.help_me()
            elif command == 'exit':
                send_msg(self.sock, self.make_exit_msg())
                print('Конец связи. Связи конец.')
                CLIENT_LOGGER.info('Пользователь завершил сеанс связи.')
                # Нужна задержка для того, чтобы ушло сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Не понял команду, попробуй ещё раз или help'
                      ' - чтобы посмотреть команды.')


    def help_me(self):
        """Функция помощь с командами """
        print('Команды для ввода:')
        print('msg - отправить сообщение')
        print('help - помощь')
        print('exit - закончить сеанс связи')

class ClientReader(threading.Thread , metaclass=ClientVerifier):
    def __init__(self, user_name, sock):
        self.user_name = user_name
        self.sock = sock
        super().__init__()


    def msg_from_server(self):
        """Для обработки сообщений с сервера"""
        while True:
            try:
                msg = get_msg(self.sock)
                if ACTION in msg and msg[ACTION] == MSG and \
                        SENDER in msg and RECIPIENT in msg \
                        and MSG_TEXT in msg and \
                        msg[RECIPIENT] == self.user_name:
                    print(f'\nОт пользователя {msg[SENDER]} получено'
                          f' сообщение:'
                          f'\n{msg[MSG_TEXT]}')
                    CLIENT_LOGGER.info(f'От клиента {msg[SENDER]} сообщение:'
                                       f'\n{msg[MSG_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'Некорректное сообщение с сервера: {msg}')
            except WrongDataRecivedError:
                CLIENT_LOGGER.error(f'Декодировать сообщение не удалось.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Соединение с сервером потеряно.')
                break


@log
def make_exist(user_name):
    """Функция проверяет присутствие клиента"""
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            USER_NAME: user_name
        }
    }
    CLIENT_LOGGER.debug(f'Создано {PRESENCE} для пользователя {user_name}')
    return out


@log
def make_resp_server(msg):
    """
    Функция анализа ответа сервера на сообщение о присутствии клиента
    :param msg:
    :return:
    """
    CLIENT_LOGGER.debug(f'Получено сообщение сервером: {msg}')
    if RESPONSE in msg:
        if msg[RESPONSE] == 200:
            return '200 : OK'
        elif msg[RESPONSE] == 400:
            raise ServerError(f'400 : {msg[ERROR]}')
    raise RequiredFieldAbsent(RESPONSE)


@log
def analyze_args():
    """Анализатор аргументов при запуске клиента в коммандной строке"""
    analyzer = argparse.ArgumentParser()
    analyzer.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    analyzer.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    analyzer.add_argument('-n', '--name', default=None, nargs='?')
    namespace = analyzer.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверяем корректность полученного номера порта
    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(
            f'Некорректный номер порта: {server_port}. '
            f'Номер порта должен быть с 1024 по 65535.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    """Запуск клиента"""
    print('Клиентский модуль запущен.')

    # Загрузка параметров коммандной строки
    server_address, server_port, client_name = analyze_args()

    # Запрос имени пользователя
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    CLIENT_LOGGER.info(
        f'Клиент запущен с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Активация сокета
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_msg(transport, make_exist(client_name))
        answer = make_resp_server(get_msg(transport))
        CLIENT_LOGGER.info(
            f'Соединение с сервером установлено, ответ: {answer}')
        print(f'Соединение установлено.')
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Декодировать Json не удалось.')
        sys.exit(1)
    except ServerError as error:
        CLIENT_LOGGER.error(
            f'Сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except RequiredFieldAbsent as missing_error:
        CLIENT_LOGGER.error(
            f'В ответе сервера нет поля {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        CLIENT_LOGGER.critical(
            f'Не могу подключиться к серверу {server_address}:{server_port}, '
            f'сервер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Соединение с сервером установлено, принимаем сообщения
        receiver = threading.Thread(target=msg_from_server,
                                    args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # Отправка сообщений через команды.
        user_pip_boy = threading.Thread(target=pip_boy_3000,
                                          args=(transport, client_name))
        user_pip_boy.daemon = True
        user_pip_boy.start()
        CLIENT_LOGGER.debug('Запущены демонические потоки')

        # Mainloop , если один из потоков закрылся,
        # значит сеанс связи закончен.
        # Цикл завершается, если один из потоков завершён.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_pip_boy.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
