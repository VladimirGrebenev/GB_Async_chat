from sqlalchemy import create_engine, Table, Column, Integer, String, Text, \
    MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import os
import sys

sys.path.append('../')
from common_files.settings import *
import datetime


# Класс базs данных сервера.
class ClientDatabase:
    # Класс знакомых людей.
    class FamiliarUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    # Класс истории сообщений
    class MsgHistory:
        def __init__(self, from_sender, to_recipient, msg):
            self.id = None
            self.from_sender = from_sender
            self.to_recipient = to_recipient
            self.msg = msg
            self.date = datetime.datetime.now()

    # Класс спискок контактов
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Конструктор класса базы
    def __init__(self, name):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(
            f'sqlite:///{os.path.join(path, filename)}.db3',
            echo=False, pool_recycle=7200, connect_args={
                'check_same_thread': False})

        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаём таблицу знакомых людей
        users = Table('familiar_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        # Создаём таблицу истории сообщений
        history = Table('msg_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_sender', String),
                        Column('to_recipient', String),
                        Column('msg', Text),
                        Column('date', DateTime)
                        )

        # Создаём таблицу контактов
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        mapper(self.FamiliarUsers, users)
        mapper(self.MsgHistory, history)
        mapper(self.Contacts, contacts)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Очищаем таблицу контактов, которая подгрузилась с сервера.
        self.session.query(self.Contacts).delete()
        # Коммитим
        self.session.commit()

    # Функция для добавления контакта
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(
                name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция для удаления контакта
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    # Функция добавления знакомых юзеров..
    def add_users(self, users_list):
        self.session.query(self.FamiliarUsers).delete()
        for user in users_list:
            user_row = self.FamiliarUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # Функция для сохранения сообщений
    def save_msg(self, from_sender, to_recipient, msg):
        msg_row = self.MsgHistory(from_sender, to_recipient, msg)
        self.session.add(msg_row)
        self.session.commit()

    # Функция для получения контактов
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(
            self.Contacts.name).all()]

    # Функция для получения списока знакомых юзеров
    def get_familiar_users(self):
        return [user[0] for user in self.session.query(
            self.FamiliarUsers.username).all()]

    # Функция для проверки наличия юзера
    def check_user(self, user):
        if self.session.query(self.FamiliarUsers).filter_by(
                username=user).count():
            return True
        else:
            return False

    # Функция для проверки контакта в списке контактов
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    # Функция для получения истории сообщений
    def get_history(self, from_sender):
        query = self.session.query(self.MsgHistory).filter_by(
            from_sender=from_sender)
        return [(history_row.from_sender, history_row.to_recipient,
                 history_row.msg, history_row.date)
                for history_row in query.all()]


# отладка
if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    # test_db.add_contact('test4')
    # test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    # test_db.save_msg('test2', 'in', f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    # test_db.save_msg('test2', 'out', f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    # print(test_db.get_contacts())
    # print(test_db.get_familiar_users())
    # print(test_db.check_user('test1'))
    # print(test_db.check_user('test10'))
    # print(sorted(test_db.get_history('test2') , key=lambda item: item[3]))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
