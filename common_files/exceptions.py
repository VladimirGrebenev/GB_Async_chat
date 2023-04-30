"""Ошибки исключения."""


class WrongDataRecivedError(Exception):
    """Исключение  - от сокета получены некорректные данные."""
    def __str__(self):
        return 'Получено некорректное сообщение от клиента.'


class ServerError(Exception):
    """Исключение - ошибка на стороне сервера."""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class NotDictError(Exception):
    """Исключение - функция приняла аргумент не являющийся словарём."""
    def __str__(self):
        return 'Для данной функции нужен аргумент в виде словаря.'


class RequiredFieldAbsent(Exception):
    """Исключение - нет обязательного поля в принятом словаре"""
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'Не хватает обязательного поля в принятом словаре' \
               f' {self.missing_field}.'

