"""
1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом
формате и проверить тип и содержание соответствующих переменных. Затем с
 помощью онлайн-конвертера преобразовать строковые представление в формат
  Unicode и также проверить тип и содержимое переменных.
"""
dev = 'разработка'
soc = 'сокет'
dec = 'декоратор'

print(f'{dev}-{type(dev)}, {soc}-{type(soc)}, {dec}-{type(dec)}')

dev = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
soc = '\u0441\u043e\u043a\u0435\u0442'
dec = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'

print(f'{dev}-{type(dev)}, {soc}-{type(soc)}, {dec}-{type(dec)}')

"""
2. Каждое из слов «class», «function», «method» записать в байтовом типе без
 преобразования в последовательность кодов (не используя методы encode и
  decode) и определить тип, содержимое и длину соответствующих переменных.
"""

words = [b'class', b'function', b'method']
[print(f'{word} - {type(word)} - {len(word)}') for word in words]

"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно
 записать в байтовом типе.
"""
w1 = b'attribute'
w2 = 'класс'  # есть символы не в ascii, приведение в байты через encode
w2_bytes = w2.encode('utf-8')
w3 = 'функция'  # есть символы не в ascii, приведение в байты через encode
w3_bytes = w3.encode('utf-8')
w4 = b'type'

"""
4. Преобразовать слова «разработка», «администрирование», «protocol»,
 «standard» из строкового представления в байтовое и выполнить обратное
  преобразование (используя методы encode и decode).
"""

words = ['разработка', 'администрирование', 'protocol', 'standard']
words_enc = [word.encode('utf-8') for word in words]
words_dec = [word.decode('utf-8') for word in words_enc]
print(words_enc)
print(words_dec)

"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать
 результаты из байтовового в строковый тип на кириллице.
"""

import subprocess
import chardet


def ping_inet(web_address):
    args = ['ping', web_address]
    subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)

    for line in subproc_ping.stdout:
        result = chardet.detect(line)
        line = line.decode(result['encoding']).encode('utf-8')
        print(line.decode('utf-8'))


# ping_inet('yandex.ru')
# ping_inet('youtube.com')


"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками:
 «сетевое программирование», «сокет», «декоратор». Проверить кодировку
  файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести
   его содержимое.
"""
words = ['сетевое программирование', 'сокет', 'декоратор']

with open('example.txt', 'w') as f_example:
    for word in words:
        f_example.write(word +'\n')
    file_encoding = f_example.encoding

with open('example.txt', 'r', encoding=file_encoding, errors='replace') as \
        f_example:
    for el_str in f_example:
        print(el_str)
