from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common_files.settings import *
import datetime


# Класс базы данных чата:
class ChatStorage:
    # Класс всех пользователей
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    # Класс активных юзеров:
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # Класс истории входов
    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    # Класс контактов пользователей
    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс отображение таблицы истории действий
    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Инициируем базу данных
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False,
                                             pool_recycle=7200,
                                             connect_args={
                                                 'check_same_thread': False})

        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаём таблицу юзеров
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        # Создаём таблицу активных юзеров
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'),
                                          unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # Создаём таблицу истории входов
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        # Создаём таблицу контактов пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Создаём таблицу истории пользователей
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        # Связываем класс в ORM с таблицей
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Если в таблице активных юзеров есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных юзеров
        self.session.query(self.ActiveUsers).delete()
        # Коммитим
        self.session.commit()

    # Функция выполняющяяся при входе юзера, записывает в базу факт входа
    def user_login(self, username, ip_address, port):
        # Запрос в таблицу юзеров на наличие там юзера с таким именем
        rez = self.session.query(self.AllUsers).filter_by(name=username)
        #print(type(rez))
        # Если имя юзера уже присутствует в таблице, обновляем время
        # последнего входа
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаздаём нового юзера
        else:
            # Создаем экземпляр класса self.AllUsers,
            # через который передаем данные в таблицу
            user = self.AllUsers(username)
            self.session.add(user)
            # Коммитим, чтобы присвоился ID
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        # Теперь можно создать запись в таблицу активных юзеров о факте входа.
        # Создаем экземпляр класса self.ActiveUsers, через который передаем
        # данные в таблицу
        new_active_user = self.ActiveUsers(user.id, ip_address, port,
                                           datetime.datetime.now())
        self.session.add(new_active_user)

        # и сохраняем в историю входов
        # Создаем экземпляр класса self.LoginHistory, через который передаем
        # данные в таблицу
        history = self.LoginHistory(user.id, datetime.datetime.now(),
                                    ip_address, port)
        self.session.add(history)

        # Коммитим
        self.session.commit()

    # Функция фиксирующая отключение юзера
    def user_logout(self, username):
        # Запрашиваем юзера, что покидает чат
        user = self.session.query(self.AllUsers).filter_by(
            name=username).first()

        # Удаляем его из таблицы активных юзеров.
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Коммитим
        self.session.commit()

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_msg(self, sender, recipient):
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(
            name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(
            name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(
            user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(
            user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # Функция добавляет контакт для пользователя.
    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(
            name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            name=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UsersContacts).filter_by(
                user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # Функция удаляет контакт из базы данных
    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(
            name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            name=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    # Функция возвращает список известных юзеров со временем последнего входа.
    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        # Возвращаем список кортежей
        return query.all()

    # Функция возвращает список активных юзеров
    def active_users_list(self):
        # Запрашиваем соединение таблиц и собираем кортежи
        # имя, адрес, порт, время.
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
            ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()

    # Функция возвращающая историю входов по юзеру или всем юзерам
    def login_history(self, username=None):
        # Запрашиваем историю входа
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # Если было указано имя юзера, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def get_contacts(self, username):
        # Запрашивааем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(
            self.UsersContacts,
            self.AllUsers.name).filter_by(user=user.id).join(self.AllUsers,
                                                             self.UsersContacts.contact == self.AllUsers.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()


# Отладка
if __name__ == '__main__':
    test_db = ChatStorage(path='server_base.db3')
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    print(test_db.users_list())
    # print(test_db.active_users_list())
    # test_db.user_logout('McG')
    # print(test_db.login_history('re'))
    # test_db.add_contact('test2', 'test1')
    # test_db.add_contact('test1', 'test3')
    # test_db.add_contact('test1', 'test6')
    # test_db.remove_contact('test1', 'test3')
    test_db.process_msg('McG2', '1111')
    print(test_db.message_history())
