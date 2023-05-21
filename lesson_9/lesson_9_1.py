# Задание 9.1.

from subprocess import Popen, PIPE
from ipaddress import ip_address


def host_ping(host_ip_addr_list, timeout=500, requests=1):
    result_dict = {'Узел доступен': "", 'Узел недоступен': ""}
    for item in host_ip_addr_list:
        try:
            item = ip_address(item)
        except ValueError:
            pass
        trial = Popen(f"ping {item} -w {timeout} -n {requests}", shell=False,
                      stdout=PIPE)
        trial.wait()

        if trial.returncode == 0:
            result_dict['Доступные узлы'] += f"{str(item)}\n"
            res_str = f'{item} - Узел доступен'
        else:
            result_dict['Недоступные узлы'] += f"{str(item)}\n"
            res_str = f'{item} - Узел недоступен'
        print(res_str)
    return result_dict


if __name__ == '__main__':
    ip_host_address = ['mail.ru', 'gb.ru', 'yandex.ru', 'vk.ru']
    host_ping(ip_host_address)
