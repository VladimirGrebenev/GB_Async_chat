import logging
import log.client_log_config
import argparse
import sys
from PyQt5.QtWidgets import QApplication

from common_files.settings import *
from common_files.exceptions import ServerError
from log.log_decorator import log
from client.client_database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

CLIENT_LOGGER = logging.getLogger('client')


@log
def analyze_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: '
            f'{server_port}. Допустимы адреса с 1024 до 65535. Клиент '
            f'завершается.')
        exit(1)

    return server_address, server_port, client_name


if __name__ == '__main__':

    server_address, server_port, client_name = analyze_args()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    CLIENT_LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , '
        f'порт: {server_port}, имя пользователя: {client_name}')

    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database,
                                    client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат  - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
