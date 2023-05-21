"""Программа-сервер"""

import socket
import sys
import argparse
import select
from common_files.settings import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME,\
    USER, USER_NAME, SENDER, PRESENCE, ERROR, MSG, MSG_TEXT, \
    RESPONSE_400, RECIPIENT, RESPONSE_200, EXIT
from common_files.plugins import get_msg, send_msg
import logging
import log.server_log_config
from log.log_decorator import log
from metacls import ServerVerifier

# Активация настроек логирования для сервера.
SERVER_LOGGER = logging.getLogger('server_log')


@log
def make_client_msg(msg, msg_list, client, clients, users_names):
    """
    Обработка сообщений от клиента. На вход получаем сообщение от клиента -
    словарь. Проверяем его корректность и возвращаем ответ клиенту - словарь.
    """

    SERVER_LOGGER.debug(f'Разбор сообщения: {msg} ')

    if ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg \
            and USER in msg:
        # Если пользователя нет в списке, то добавляем его. Если такой есть,
        # то говорим, что имя занято и завершаем соединение.
        if msg[USER][USER_NAME] not in users_names.keys():
            users_names[msg[USER][USER_NAME]] = client
            send_msg(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Такой юзер уже существует'
            send_msg(client, response)
            clients.remove(client)
            client.close()
        return
    # Если сообщение имеет все параметры,
    # то добавляем в список сообщений на доставку.
    elif ACTION in msg and msg[ACTION] == MSG and \
            RECIPIENT in msg and TIME in msg \
            and SENDER in msg and MSG_TEXT in msg:
        msg_list.append(msg)
        return
    # Если клиент выбрал команду exit
    elif ACTION in msg and msg[ACTION] == EXIT and USER_NAME in msg:
        clients.remove(users_names[msg[USER_NAME]])
        users_names[msg[USER_NAME]].close()
        del users_names[msg[USER_NAME]]
        return
    # В остальных случаях, констатируем некорректный запрос
    else:
        response = RESPONSE_400
        response[ERROR] = 'Получен некорректный запрос к серверу.'
        send_msg(client, response)
        return


@log
def make_msg(msg, users_names, listen_socks):
    """
    Функция для отправки сообщения конкретному клиенту по имени.
    На вход получает сообщение, словарь с зарегистрированными именами
    пользователей,и сокеты.
    :param msg:
    :param users_names:
    :param listen_socks:
    :return:
    """
    if msg[RECIPIENT] in users_names and users_names[msg[RECIPIENT]]\
            in listen_socks:
        send_msg(users_names[msg[RECIPIENT]], msg)
        SERVER_LOGGER.info(f'Cообщение отправлено клиенту {msg[RECIPIENT]} '
                    f'от клиента {msg[SENDER]}.')
    elif msg[RECIPIENT] in users_names and users_names[msg[RECIPIENT]]\
            not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(
            f'Клиент {msg[RECIPIENT]} не существует на сервере, '
            f'сообщение не доставлено')


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


def main():
    """
    Устанавливаем паремтры для сервера из командной строки, если запуск
     без параметров, то устанавливаем параметры по умолчанию.
    """
    listen_address, listen_port = analyze_args()

    SERVER_LOGGER.info(
        f'Запущен сервер, порт для подключений: {listen_port}, '
        f'адрес для подключения: {listen_address}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')
    # Подготовка сокета
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.5)

    # список клиентов и список сообщений для отправки
    clients = []
    msgs = []

    # Имена пользователей.
    users_names = dict()

    # Прослушиваем порт
    transport.listen(MAX_CONNECTIONS)
    # Главная петля сервера
    while True:
        # Ожидаем подключения за отведённый таймаут.
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            SERVER_LOGGER.info(f'Соединение установлено '
                               f'с клиентом {client_address}')
            # добавляем клиента в список
            clients.append(client)

        to_receive_lst = []
        to_send_lst = []
        err_lst = []
        # Проверка на наличие клиентов в ожидании
        try:
            if clients:
                to_receive_lst, to_send_lst, err_lst = select.select(clients,
                                                                     clients,
                                                                     [], 0)
        except OSError:
            pass

        # получаем сообщения и если ловим исключение, то клиент исключается
        # из списка.
        if to_receive_lst:
            for client_with_msg in to_receive_lst:
                try:
                    make_client_msg(get_msg(client_with_msg), msgs,
                                    client_with_msg, clients, users_names)
                except Exception:
                    SERVER_LOGGER.info(f'Клиент '
                                       f'{client_with_msg.getpeername()} '
                                f'отключился.')
                    clients.remove(client_with_msg)

        # Обработка сообщений.
        for i in msgs:
            try:
                make_msg(i, users_names, to_send_lst)
            except Exception:
                SERVER_LOGGER.info(f'Связь с клиентом {i[RECIPIENT]}'
                                   f' потеряна.')
                clients.remove(users_names[i[RECIPIENT]])
                del users_names[i[RECIPIENT]]
        msgs.clear()


if __name__ == '__main__':
    main()
