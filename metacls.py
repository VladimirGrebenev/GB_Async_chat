import dis

# Метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент»:
class ClientVerifier(type):
    def __init__(self, name_of_class, basis, class_dict):
        # Методы, используемые в функциях класса:
        methods_list = []

        for func in class_dict:
            try:
                result = dis.get_instructions(class_dict[func])
            except TypeError:
                pass
            else:
                for item in result:
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods_list:
                            methods_list.append(item.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods_list:
                raise TypeError(f'Использование {command} метода запрещено в'
                                f' классе')

        if 'get_msg' in methods_list or 'send_msg' in methods_list:
            pass
        else:
            raise TypeError('Функций, работающих с сокетами, не обнаружено')
        super().__init__(name_of_class, basis, class_dict)

class ServerVerifier(type):
    def __init__(self, name_of_class, basis, class_dict):
        # Методы, используемые в функциях класса:
        methods_list = []
        # Атрибуты, функций класса:
        attrs_list = []

        for func in class_dict:
            try:
                result = dis.get_instructions(class_dict[func])
            except TypeError:
                pass
            else:
                for item in result:
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods_list:
                            methods_list.append(item.argval)
                    elif item.opname == 'LOAD_ATTR':
                        if item.argval not in attrs_list:
                            attrs_list.append(item.argval)

        if 'connect' in methods_list:
            raise TypeError(f'Метод connect запрещён в классе')
        if not ('SOCK_STREAM' in attrs_list and 'AF_INET' in attrs_list):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(name_of_class, basis, class_dict)
