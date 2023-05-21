# Задание 9.3.

from tabulate import tabulate
from lesson_9_2 import host_range_ping


def host_range_ping_tab():
    result_dict = host_range_ping()
    print(tabulate([result_dict],
                   headers='keys',
                   tablefmt="pipe",
                   stralign="center"))


if __name__ == "__main__":
    host_range_ping_tab()
