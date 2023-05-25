"""Программа-клиент"""

import sys
import json
import socket
import time
import argparse
import logging
import threading
import log.client_log_config
from common_files.settings import *
from common_files.plugins import get_msg, send_msg
from common_files.exceptions import WrongDataRecivedError, \
    RequiredFieldAbsent, ServerError
from log.log_decorator import log
from metacls import ClientVerifier
from client_database import ClientDatabase

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')

# Объект блокировки сокета
sock_lock = threading.Lock()
# Объект работы с базой данных
database_lock = threading.Lock()

class ClientSend(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, user_name, sock, database):
        self.user_name = user_name
        self.sock = sock
        self.database = database
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

        # Чекаем, что получатель существует
        with database_lock:
            if not self.database.check_user(to_recipient):
                CLIENT_LOGGER.error(f'Попытка отправить сообщение '
                                    f'незарегистрированому получателю:'
                                    f' {to_recipient}')
                return

        msg_dict = {
            ACTION: MSG,
            SENDER: self.user_name,
            RECIPIENT: to_recipient,
            TIME: time.time(),
            MSG_TEXT: msg
        }
        CLIENT_LOGGER.debug(f'Словарь сообщения: {msg_dict}')

        # Сохраняем сообщения в базу в историю сообщений
        with database_lock:
            self.database.save_message(self.user_name, to_recipient, msg)

        with sock_lock:
            try:
                send_msg(self.sock, msg_dict)
                CLIENT_LOGGER.info(f'Ушло сообщение для {to_recipient}')
            except:
                CLIENT_LOGGER.critical('Соединение с сервером потеряно.')
                sys.exit(1)


    def run(self):
        """Функция для отправки команд пользователем"""
        self.help_me()
        while True:
            command = input('Введите команду: ')
            if command == 'msg':
                self.make_msg()
            elif command == 'help':
                self.help_me()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_msg(self.sock, self.make_exit_msg())
                    except:
                        pass
                    print('Конец связи. Связи конец.')
                    CLIENT_LOGGER.info('Пользователь завершил сеанс связи.')
                # Нужна задержка для того, чтобы ушло сообщение о выходе
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit contacts':
                self.edit_contacts()
            elif command == 'history msg':
                self.print_history_msg()
            else:
                print('Не понял команду, попробуй ещё раз или help'
                      ' - чтобы посмотреть команды.')


    def help_me(self):
        """Функция помощь с командами """
        print('Команды для ввода:')
        print('msg - отправить сообщение')
        print('history msg - история сообщений')
        print('contacts - список контактов')
        print('edit contacts - редактировать контакты')
        print('help - помощь')
        print('exit - закончить сеанс связи')

    # Функция для вывода истории сообщений
    def print_history_msg(self):
        choice = input(
            'Входящие - inсoming, исходящие - outgoing, все - нажмите Enter: ')
        with database_lock:
            if choice == 'inсoming':
                history_list = self.database.get_history(
                    to_who=self.user_name)
                for msg in history_list:
                    print(
                        f'\nСообщение от: {msg[0]} от {msg[3]}:\n{msg[2]}')
            elif choice == 'outgoing':
                history_list = self.database.get_history(
                    from_who=self.user_name)
                for msg in history_list:
                    print(
                        f'\nСообщение пользователю: {msg[1]} от {msg[3]}:\
                        n{msg[2]}')
            else:
                history_list = self.database.get_history()
                for msg in history_list:
                    print(
                        f'\nСообщение от: {msg[0]}, пользователю {msg[1]} от'
                        f' {msg[3]}\n{msg[2]}')


    #Функция для редактирования контактов
    def edit_contacts(self):
        choice = input('Для удаления введите delete, для добавления add: ')
        if choice == 'delete':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    CLIENT_LOGGER.error('Этого контакта не существует.')
        elif choice == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.user_name, edit)
                    except ServerError:
                        CLIENT_LOGGER.error('Не удалось отправить информацию.')



class ClientRead(threading.Thread , metaclass=ClientVerifier):
    def __init__(self, user_name, sock, database):
        self.user_name = user_name
        self.sock = sock
        self.database = database
        super().__init__()


    def run(self):
        """Для обработки сообщений с сервера"""
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    msg = get_msg(self.sock)
                except WrongDataRecivedError:
                    CLIENT_LOGGER.error(f'Декодировать сообщение не удалось.')
                except (OSError, ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    CLIENT_LOGGER.critical(f'Соединение с сервером потеряно.')
                    break
                else:
                    if ACTION in msg and msg[ACTION] == MSG and \
                            SENDER in msg and RECIPIENT in msg \
                            and MSG_TEXT in msg and \
                            msg[RECIPIENT] == self.user_name:
                        print(f'\nОт пользователя {msg[SENDER]} получено'
                              f' сообщение: \n{msg[MSG_TEXT]}')
                        CLIENT_LOGGER.info(f'От клиента {msg[SENDER]} '
                                           f'сообщение: \n{msg[MSG_TEXT]}')
                    else:
                        CLIENT_LOGGER.error(f'Некорректное сообщение с '
                                            f'сервера: {msg}')


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


# Функция запроса списка контактов
def take_contacts_list(sock, name):
    CLIENT_LOGGER.debug(f'Запрос списка контактов для {name}')
    req = {
        ACTION: TAKE_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
    send_msg(sock, req)
    answer = get_msg(sock)
    CLIENT_LOGGER.debug(f'Получен ответ {answer}')
    if RESPONSE in answer and answer[RESPONSE] == 202:
        return answer[CONTACTS_INFO]
    else:
        raise ServerError


# Функция добавления юзера в список контактов
def add_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        USER_NAME: contact
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Контакт создан.')


# Функция запроса знакомых юзеров
def take_user_list(sock, username):
    CLIENT_LOGGER.debug(f'Запрос списка знакомых {username}')
    req = {
        ACTION: TAKE_USERS,
        TIME: time.time(),
        USER_NAME: username
    }
    send_msg(sock, req)
    answer = get_msg(sock)
    if RESPONSE in answer and answer[RESPONSE] == 202:
        return answer[CONTACTS_INFO]
    else:
        raise ServerError


# Функция удаления из списка контактов
def remove_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: DELETE_CONTACT,
        TIME: time.time(),
        USER: username,
        USER_NAME: contact
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Контакт удалён')


# Функция инициализатор базы данных.
def database_load(sock, database, username):
    try:
        users_list = take_user_list(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка знакомых.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = take_contacts_list(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    """Запуск клиента"""
    print('Клиентский модуль запущен.')

    # Загрузка параметров коммандной строки
    server_address, server_port, client_name = analyze_args()

    # Запрос имени пользователя
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиент запущен пользователем: {client_name}')

    CLIENT_LOGGER.info(
        f'Клиент запущен с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Активация сокета
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)
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
        # Инициализируем базу данных
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        # Соединение с сервером установлено, принимаем сообщения
        receiver = ClientRead(client_name, transport, database)
        receiver.daemon = True
        receiver.start()

        # Отправка сообщений через команды.
        user_pip_boy = ClientSend(client_name, transport, database)
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
