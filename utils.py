"""
utils.py - Вспомогательные функции для форматирования и валидации.
"""

import re
from datetime import date
from typing import Optional, Tuple


def format_number(value: float, decimal_places: int = 2) -> str:
    """
    Форматирует число с разделением тысяч пробелом и указанным количеством знаков после запятой.
    
    :param value: Число для форматирования
    :param decimal_places: Количество знаков после запятой
    :return: Отформатированная строка
    """
    formatted = f"{value:,.{decimal_places}f}"
    return formatted.replace(',', ' ')


def format_date(d: date) -> str:
    """
    Форматирует дату в формате ДД.ММ.ГГГГ.
    
    :param d: Объект даты
    :return: Отформатированная строка
    """
    return d.strftime('%d.%m.%Y')


def format_currency(value: float) -> str:
    """
    Форматирует сумму как валюту с двумя знаками после запятой.
    
    :param value: Сумма
    :return: Отформатированная строка
    """
    return format_number(value, 2)


def validate_positive_number(value: str, allow_zero: bool = False) -> Tuple[bool, Optional[float], str]:
    """
    Проверяет, является ли строка положительным числом.
    
    :param value: Строка для проверки
    :param allow_zero: Разрешать ли ноль
    :return: Кортеж (успех, значение или None, сообщение об ошибке)
    """
    if not value or not value.strip():
        return False, None, "Ввод не может быть пустым"
    
    value = value.strip()
    
    # Проверка формата числа (целое или дробное)
    if not re.match(r'^-?\d+(\.\d+)?$', value):
        return False, None, "Неверный формат числа. Используйте цифры и точку для дробной части"
    
    try:
        num = float(value)
        
        if allow_zero:
            if num < 0:
                return False, None, "Значение не может быть отрицательным"
        else:
            if num <= 0:
                return False, None, "Значение должно быть положительным"
        
        return True, num, ""
    except ValueError:
        return False, None, "Не удалось преобразовать в число"


def validate_integer(value: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Tuple[bool, Optional[int], str]:
    """
    Проверяет, является ли строка целым числом в заданном диапазоне.
    
    :param value: Строка для проверки
    :param min_value: Минимальное допустимое значение
    :param max_value: Максимальное допустимое значение
    :return: Кортеж (успех, значение или None, сообщение об ошибке)
    """
    if not value or not value.strip():
        return False, None, "Ввод не может быть пустым"
    
    value = value.strip()
    
    if not re.match(r'^-?\d+$', value):
        return False, None, "Неверный формат. Введите целое число"
    
    try:
        num = int(value)
        
        if min_value is not None and num < min_value:
            return False, None, f"Значение должно быть не меньше {min_value}"
        
        if max_value is not None and num > max_value:
            return False, None, f"Значение должно быть не больше {max_value}"
        
        return True, num, ""
    except ValueError:
        return False, None, "Не удалось преобразовать в целое число"


def validate_date(value: str) -> Tuple[bool, Optional[date], str]:
    """
    Проверяет, является ли строка датой в формате ДД.ММ.ГГГГ.
    
    :param value: Строка для проверки
    :return: Кортеж (успех, дата или None, сообщение об ошибке)
    """
    if not value or not value.strip():
        return False, None, "Ввод не может быть пустым"
    
    value = value.strip()
    
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', value):
        return False, None, "Неверный формат даты. Используйте ДД.ММ.ГГГГ"
    
    try:
        day, month, year = map(int, value.split('.'))
        d = date(year, month, day)
        return True, d, ""
    except ValueError:
        return False, None, "Некорректная дата"


def get_input_with_validation(
    prompt: str, 
    validator_func, 
    **validator_kwargs
) -> any:
    """
    Запрашивает ввод у пользователя с валидацией.
    
    :param prompt: Текст приглашения к вводу
    :param validator_func: Функция валидации
    :param validator_kwargs: Аргументы для функции валидации
    :return: Валидное значение
    """
    while True:
        user_input = input(prompt).strip()
        success, value, error = validator_func(user_input, **validator_kwargs)
        
        if success:
            return value
        else:
            print(f"Ошибка: {error}. Попробуйте снова.")


def print_separator(char: str = '-', length: int = 50) -> None:
    """
    Выводит разделительную линию.
    
    :param char: Символ разделителя
    :param length: Длина линии
    """
    print(char * length)


def print_header(title: str) -> None:
    """
    Выводит заголовок раздела.
    
    :param title: Текст заголовка
    """
    print_separator('=')
    print(f"  {title}")
    print_separator('=')


def print_result(label: str, value: any, is_currency: bool = False) -> None:
    """
    Выводит результат расчёта.
    
    :param label: Описание значения
    :param value: Значение
    :param is_currency: Является ли значение денежной суммой
    """
    if is_currency:
        formatted = format_currency(value)
    elif isinstance(value, float):
        formatted = f"{value:.2f}"
    else:
        formatted = str(value)
    
    print(f"  {label}: {formatted}")
