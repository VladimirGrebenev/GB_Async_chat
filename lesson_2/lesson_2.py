"""Задание 2_1"""
import csv
import itertools
import re


def get_data(patterns, files_list):
    """
    Функция, принимает список паттернов {patterns} и список файлов
    {files_list}. Возвращает список {main_data} пригодный для записи в csv.
    :param patterns: {list} список паттернов.
    :param files_list: {list} список файлов
    :return: список списков для записи в csv
    """
    seek_dicts_list = []
    main_data = []

    main_data.append(patterns)

    for file in files_list:
        with open(file) as f_n:
            seek_values = []
            for pattern in patterns:
                seek = seek_data(f_n, pattern)
                f_n.seek(0)
                seek_values.append(seek)
        seek_dicts_list.append({file: seek_values})

    for el in seek_dicts_list:
        for value in el.values():
            main_data.append(value)

    return main_data


def seek_data(text_data, pattern):
    """
    Функция для поиска значений по ключу в тексте.
    :param text_data: {str} текст.
    :param pattern: {str} паттерн для поиска ключа по точному совпадению.
    :return: строка {seek_result}, значение найденного ключа.
    """
    for string in text_data:
        match = re.search(pattern, string)
        if match:
            seek_result = string.rstrip().replace(" ", "").split(':')[1]
            break

    return seek_result

def write_to_csv(file_name, patterns, files_list):
    data_to_write = get_data(patterns, files_list)

    with open(file_name, 'w', encoding='utf-8', newline='') as f_n:
        f_n_writer = csv.writer(f_n, quoting=csv.QUOTE_NONNUMERIC)
        f_n_writer.writerows(data_to_write)


my_patterns = ['Изготовитель ОС', 'Название ОС', 'Код продукта', 'Тип системы']
my_files = ['info_1.txt', 'info_2.txt', 'info_3.txt']
print(get_data(my_patterns, my_files))

write_to_csv('example_data.csv', my_patterns, my_files)


