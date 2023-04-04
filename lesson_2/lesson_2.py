"""Задание 2_1"""
import csv
import itertools
import re


def get_data(patterns, files_list):
    """
    Функция, принимает список паттернов {patterns} и список файлов
    {files_list}. Возвращает список {main_data} пригодный для записи в cvs.
    :param patterns: {list} список патnернов.
    :param files_list: {list} список файлов
    :return:
    """
    seek_dicts_list = []
    values_list = []
    main_data = []
    for pattern in patterns:
        seek_values = []
        for file in files_list:
            with open(file) as f_n:
                seek_values.append(seek_data(f_n, pattern))
        seek_dicts_list.append({pattern: seek_values})

    keys_list = []
    for el in seek_dicts_list:
        for key in el.keys():
            keys_list.append(key)

    main_data.append(keys_list)

    for el in seek_dicts_list:
        for value in el.values():
            values_list.append(value)

    v1 = values_list[0]
    v2 = values_list[1]
    v3 = values_list[2]
    v4 = values_list[3]

    values = list(itertools.chain(v1,v2,v3,v4))

    # for (a, b, c) in zip(v1, v2, v3):
    #     n = [a, b, c]
    #     values.append(n)

    main_data.append(values)

    print(values)
    print(seek_dicts_list)

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
    return seek_result

def write_to_csv(file_name, patterns, files_list):
    data_to_write = get_data(patterns, files_list)

    with open(file_name, 'w', encoding='utf-8') as f_n:
        f_n_writer = csv.writer(f_n, quoting=csv.QUOTE_NONNUMERIC)
        f_n_writer.writerows(data_to_write)


my_patterns = ['Изготовитель ОС', 'Название ОС', 'Код продукта', 'Тип системы']
my_files = ['info_1.txt', 'info_2.txt', 'info_3.txt']
print(get_data(my_patterns, my_files))
#
# write_to_csv('example_data.csv', my_patterns, my_files)


