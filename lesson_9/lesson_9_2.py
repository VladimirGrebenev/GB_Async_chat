# Задание 9.2.

from ipaddress import ip_address
from lesson_9_1 import host_ping


def host_range_ping():
    while True:
        begin_ip = input('Введите первый ip - начало диапозона проверки: ')
        try:
            last_octet = int(begin_ip.split('.')[3])
            break
        except Exception as error:
            print(error)
    while True:
        quantity_ips = input('Количество адресов для проверки?: ')
        if not quantity_ips.isnumeric():
            print('введите цифрами: ')
        else:
            if (last_octet + int(quantity_ips)) > 254:
                print(
                    f"Возможное число проверки не больше: {254 - last_octet}")
            else:
                break

    ip_list = []
    [ip_list.append(str(ip_address(begin_ip) + x))
     for x in range(int(quantity_ips))]

    return host_ping(ip_list)


if __name__ == "__main__":
    host_range_ping()

