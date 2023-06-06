import socket
import sys
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
from common_files.plugins import *
from common_files.settings import *

CLIENT_LOGGER = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
            CLIENT_LOGGER.error(
                'Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
        self.running = True

    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            CLIENT_LOGGER.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            CLIENT_LOGGER.critical(
                'Не удалось установить соединение с сервером')

        CLIENT_LOGGER.debug('Установлено соединение с сервером')

        try:
            with socket_lock:
                send_msg(self.transport, self.create_presence())
                self.process_server_ans(get_msg(self.transport))
        except (OSError, json.JSONDecodeError):
            CLIENT_LOGGER.critical('Потеряно соединение с сервером!')

        CLIENT_LOGGER.info('Соединение с сервером успешно установлено.')

    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                USER_NAME: self.username
            }
        }
        CLIENT_LOGGER.debug(
            f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
        return out

    def process_server_ans(self, msg):
        CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {msg}')

        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return
            elif msg[RESPONSE] == 400:
                raise RESPONSE_400
            else:
                CLIENT_LOGGER.debug(f'Принят неизвестный код подтверждения '
                                    f'{msg[RESPONSE]}')


        elif ACTION in msg and msg[ACTION] == MSG and SENDER in \
                msg and RECIPIENT in msg and MSG_TEXT in msg and \
                msg[RECIPIENT] == self.username:
            CLIENT_LOGGER.debug(f'Получено сообщение от пользователя '
                                f'{msg[SENDER]}:{msg[MSG_TEXT]}')
            self.database.save_message(msg[SENDER], 'in', msg[
                MSG_TEXT])
            self.new_message.emit(msg[SENDER])

    def contacts_list_update(self):
        CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователся '
                            f'{self.name}')
        req = {
            ACTION: TAKE_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        CLIENT_LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[CONTACTS_INFO]:
                self.database.add_contact(contact)
        else:
            CLIENT_LOGGER.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        CLIENT_LOGGER.debug(f'Запрос списка известных пользователей '
                            f'{self.username}')
        req = {
            ACTION: TAKE_USERS,
            TIME: time.time(),
            USER_NAME: self.username
        }
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[CONTACTS_INFO])
        else:
            CLIENT_LOGGER.error('Не удалось обновить список известных '
                                'пользователей.')

    def add_contact(self, contact):
        CLIENT_LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            USER_NAME: contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    def remove_contact(self, contact):
        CLIENT_LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: DELETE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            USER_NAME: contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            USER_NAME: self.username
        }
        with socket_lock:
            try:
                send_msg(self.transport, message)
            except OSError:
                pass
        CLIENT_LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            ACTION: MSG,
            SENDER: self.username,
            RECIPIENT: to,
            TIME: time.time(),
            MSG_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_msg(self.transport, message_dict)
            self.process_server_ans(get_msg(self.transport))
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        CLIENT_LOGGER.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    msg = get_msg(self.transport)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(
                            f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()

                except (
                        ConnectionError, ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError, TypeError):
                    CLIENT_LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()

                else:
                    CLIENT_LOGGER.debug(f'Принято сообщение с сервера: '
                                        f'{msg}')
                    self.process_server_ans(msg)
                finally:
                    self.transport.settimeout(5)
