import json


def write_order_to_json(item, quantity, price, buyer, date):
    """
    Функция записи заказов в файл.
    :param item: {str} 'ватрушки'
    :param quantity: {int} 10
    :param price: {int} 25
    :param buyer: {str} 'Гребенев В.В.'
    :param date: {str} '05.04.2023'
    """
    order = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date,
    }

    with open('orders.json', 'w', encoding='utf-8') as f_n:
        json.dump(order, f_n, indent=4, ensure_ascii=False)


write_order_to_json('ватрушки', 10, 25, 'Гребенев В.В.', '05.04.2023')

with open('orders.json', 'r', encoding='utf-8') as f_n:
    data = json.load(f_n)
    print(json.dumps(data, indent=4, ensure_ascii=False))

