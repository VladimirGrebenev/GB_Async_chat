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

    def __init__(self):
        # Инициируем базу данных
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle - По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось нужно добавить опцию pool_recycle = 7200 (переуст-ка соед-я через 2 часа)
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)

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
                                   Column('user', ForeignKey('Users.id'), unique=True),
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

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        # Связываем класс в ORM с таблицей
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)

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
        print(username, ip_address, port)
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


# Отладка
if __name__ == '__main__':
    test_db = ChatStorage()
    # выполняем 'подключение' юзера
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    # выводим список кортежей - активных юзеров
    print(test_db.active_users_list())
    # выполянем 'отключение' юзера
    test_db.user_logout('client_1')
    # выводим список активных юзеров
    print(test_db.active_users_list())
    # запрашиваем историю входов по юзеру
    test_db.login_history('client_1')
    # выводим список известных юзеров
    print(test_db.users_list())
