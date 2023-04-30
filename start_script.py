"""Запускающий скрипт"""

import subprocess

LAUNCHES = []

while True:
    ACTION = input('Выбери действие: start - запуск клиентов и сервера, '
                   'exit - закрыть всё, quit - выйти')

    if ACTION == 'quit':
        break
    elif ACTION == 'start':
        LAUNCHES.append(
            subprocess.Popen(
                'python server.py',
                creationflags=subprocess.CREATE_NEW_CONSOLE)
        )
        LAUNCHES.append(
            subprocess.Popen(
                'python client.py -n client1',
                creationflags=subprocess.CREATE_NEW_CONSOLE)
        )
        LAUNCHES.append(
            subprocess.Popen(
                'python client.py -n client2',
                creationflags=subprocess.CREATE_NEW_CONSOLE)
        )
    elif ACTION == 'exit':
        while LAUNCHES:
            VICTIM = LAUNCHES.pop()
            VICTIM.kill()
