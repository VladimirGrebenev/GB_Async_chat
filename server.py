"""Программа-сервер"""

import socket
import sys
import os
import argparse
import select
from common_files.settings import *
from common_files.plugins import *
import logging
import threading
import configparser
import log.server_log_config
from log.log_decorator import log
from metacls import ServerVerifier
from chat_database import ChatStorage

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from chat_gui import MainWindow, gui_make_model, HistoryWindow, \
    make_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Активация настроек логирования для сервера.
SERVER_LOGGER = logging.getLogger('server_log')

# Флаг что был подключён новый пользователь, нужен чтобы не дёргать базу данных
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


def analyze_args(default_port, default_address):
    """Анализатор аргументов при запуске в коммандной строке"""
    analyzer = argparse.ArgumentParser()
    analyzer.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    analyzer.add_argument('-a', default='', nargs='?')
    namespace = analyzer.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
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


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.clients = []
        self.msgs = []
        self.users_names = dict()
        super().__init__()

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

    def run(self):
        global new_connection
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
            except OSError as err:
                SERVER_LOGGER.error(f'Ошибка сокетов: {err}')

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
                        for name in self.users_names:
                            if self.users_names[name] == client_with_msg:
                                self.database.user_logout(name)
                                del self.users_names[name]
                                break
                        self.clients.remove(client_with_msg)
                        with conflag_lock:
                            new_connection = True

            # Обработка сообщений.
            for item in self.msgs:
                try:
                    self.make_msg(item, to_send_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом {item[RECIPIENT]}'
                                       f' потеряна.')
                    self.clients.remove(self.users_names[item[RECIPIENT]])
                    self.database.user_logout(item[RECIPIENT])
                    del self.users_names[item[RECIPIENT]]
                    with conflag_lock:
                        new_connection = True
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
        global new_connection
        SERVER_LOGGER.debug(f'Разбор сообщения: {msg} ')

        if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg \
                and USER in msg:
            # Если пользователя нет в списке, то добавляем его.
            # Если такой есть, то говорим, что имя занято и завершаем
            # соединение.
            if msg[USER][USER_NAME] not in self.users_names.keys():
                self.users_names[msg[USER][USER_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(msg[USER][USER_NAME],
                                         client_ip, client_port)
                send_msg(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такой юзер уже существует'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если сообщение имеет все параметры,
        # то добавляем в список сообщений на доставку.
        elif ACTION in msg and msg[
            ACTION] == MSG and RECIPIENT in msg and TIME in msg \
                and SENDER in msg and MSG_TEXT in msg and \
                self.users_names[msg[SENDER]] == client:
            if msg[RECIPIENT] in self.users_names:
                self.msgs.append(msg)
                self.database.process_msg(msg[SENDER],
                                              msg[RECIPIENT])
                send_msg(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере.'
                send_msg(client, response)
            return

        # Если клиент выбрал команду exit
        elif ACTION in msg and msg[ACTION] == EXIT and USER_NAME in msg:
            self.database.user_logout(msg[USER_NAME])
            self.clients.remove(self.users_names[USER_NAME])
            self.users_names[USER_NAME].close()
            del self.users_names[USER_NAME]
            with conflag_lock:
                new_connection = True
            return

        # Если запрос контактов
        elif ACTION in msg and msg[ACTION] == TAKE_CONTACTS and USER in \
                msg and self.users_names[msg[USER]] == client:
            response = RESPONSE_202
            response[CONTACTS_INFO] = self.database.get_contacts(msg[USER])
            send_msg(client, response)

        # Если добавление контакта
        elif ACTION in msg and msg[ACTION] == ADD_CONTACT and USER_NAME in \
                msg and USER in msg and self.users_names[msg[USER]] == client:
            self.database.add_contact(msg[USER], msg[USER_NAME])
            send_msg(client, RESPONSE_200)

        # Если удаление контакта
        elif ACTION in msg and msg[ACTION] == DELETE_CONTACT and USER_NAME \
                in msg and USER in msg and self.users_names[msg[USER]] == \
                client:
            self.database.remove_contact(msg[USER], msg[USER_NAME])
            send_msg(client, RESPONSE_200)

        # Если запрос известных юзеров
        elif ACTION in msg and msg[ACTION] == TAKE_USERS and USER_NAME in msg \
                and self.users_names[msg[USER_NAME]] == client:
            response = RESPONSE_202
            response[CONTACTS_INFO] = [user[0] for user in
                                   self.database.users_list()]
            send_msg(client, response)

        # В остальных случаях, констатируем некорректный запрос
        else:
            response = RESPONSE_400
            response[ERROR] = 'Получен некорректный запрос к серверу.'
            send_msg(client, response)
            return

# def help_me(self):
#     """Функция помощь с командами """
#     print('Команды для ввода:')
#     print('users - список юзеров')
#     print('connected - список активных юзеров')
#     print('loghist - история активности')
#     print('exit - завершить работу сервера')
#     print('help - вывод справки по поддерживаемым командам')


# Загрузка файла конфигурации
def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    # Загрузка конфигурации сервера
    config = config_load()

    # Загрузка параметров командной строки,
    # если нет параметров, то задаём значения по умоланию.
    listen_address, listen_port = analyze_args(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_Address'])


    # Инициализируем базу чата
    database = ChatStorage(os.path.join(config['SETTINGS']['Database_path'],
                                          config['SETTINGS']['Database_file']))

    # Создаём экземпляр класса Server.
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # # Вывод доступных команд:
    # help_me()

    # Создаём gui для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализация параметров окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_make_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

# Функция обновляющяя список подключённых, проверяет флаг подключения, и если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_make_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(make_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()