"""
cli.py - Пользовательский интерфейс для финансового калькулятора.
Консольное приложение с интерактивным меню.
"""

import requests
from datetime import date
from typing import Dict, List, Optional

from finance_calculations import (
    calculate_annuity_payment,
    calculate_differentiated_schedule,
    calculate_credit_summary,
    calculate_deposit,
    calculate_investment,
    calculate_npv,
    calculate_irr
)
from utils import (
    format_currency,
    format_date,
    format_number,
    validate_positive_number,
    validate_integer,
    validate_date,
    print_separator,
    print_header,
    print_result,
    get_input_with_validation
)


# Офлайн-курсы валют (заглушка)
OFFLINE_RATES: Dict[str, float] = {
    'USD': 1.0,
    'EUR': 0.92,
    'RUB': 90.0,
    'GBP': 0.79,
    'CNY': 7.24,
    'KZT': 450.0,
    'BYN': 3.27,
    'JPY': 150.0,
    'CHF': 0.88,
    'INR': 83.0
}

# API для курсов валют
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"


def fetch_currency_rates() -> Optional[Dict[str, float]]:
    """
    Загружает актуальные курсы валют из API.
    
    :return: Словарь с курсами валют относительно USD или None при ошибке
    """
    try:
        response = requests.get(CURRENCY_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('rates', OFFLINE_RATES)
    except (requests.RequestException, ValueError):
        return None


def convert_currency(amount: float, from_currency: str, to_currency: str) -> tuple:
    """
    Конвертирует сумму из одной валюты в другую.
    
    :param amount: Сумма для конвертации
    :param from_currency: Исходная валюта (код)
    :param to_currency: Целевая валюта (код)
    :return: Кортеж (результат, используемый курс, использован ли офлайн-режим)
    """
    rates = fetch_currency_rates()
    offline_mode = False
    
    if rates is None:
        rates = OFFLINE_RATES
        offline_mode = True
        print("\n⚠️  Предупреждение: API недоступен. Используются офлайн-курсы.")
    
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency not in rates:
        raise ValueError(f"Валюта {from_currency} не найдена")
    if to_currency not in rates:
        raise ValueError(f"Валюта {to_currency} не найдена")
    
    # Конвертация через USD как базовую валюту
    # rate_from - сколько единиц исходной валюты за 1 USD
    # rate_to - сколько единиц целевой валюты за 1 USD
    rate_from = rates[from_currency]
    rate_to = rates[to_currency]
    
    # Сначала переводим в USD, затем в целевую валюту
    amount_in_usd = amount / rate_from
    result = amount_in_usd * rate_to
    
    # Вычисляем кросс-курс
    cross_rate = rate_to / rate_from
    
    return result, cross_rate, offline_mode


def menu_credit() -> None:
    """Меню кредитного калькулятора."""
    print_header("Кредитный калькулятор")
    
    print("\nВыберите тип платежа:")
    print("  1. Аннуитетные платежи")
    print("  2. Дифференцированные платежи")
    print("  0. Назад")
    
    choice = input("\nВаш выбор: ").strip()
    
    if choice == '0':
        return
    
    # Ввод данных
    principal = get_input_with_validation(
        "Введите сумму кредита: ",
        validate_positive_number
    )
    
    annual_rate = get_input_with_validation(
        "Введите годовую процентную ставку (%): ",
        validate_positive_number
    )
    
    months = get_input_with_validation(
        "Введите срок кредита в месяцах: ",
        validate_integer,
        min_value=1
    )
    
    # Опциональная дата первого платежа
    print("\nДата первого платежа (необязательно, формат ДД.ММ.ГГГГ).")
    date_input = input("Оставьте пустым для использования текущей даты: ").strip()
    
    start_date = None
    if date_input:
        success, d, error = validate_date(date_input)
        if success:
            start_date = d
        else:
            print(f"Некорректная дата, будет использована текущая: {format_date(date.today())}")
    
    # Расчёт
    summary = calculate_credit_summary(principal, annual_rate, months, 
                                       'annuity' if choice == '1' else 'differentiated',
                                       start_date)
    
    # Вывод результатов
    print_header("Результаты расчёта")
    
    if choice == '1':
        print_result("Ежемесячный платёж", summary['monthly_payment'], is_currency=True)
    else:
        print("Тип платежа: дифференцированный")
        print("Первый платёж:", format_currency(summary['schedule'][0]['payment']) if summary['schedule'] else "N/A")
        print("Последний платёж:", format_currency(summary['schedule'][-1]['payment']) if summary['schedule'] else "N/A")
    
    print_result("Общая сумма выплат", summary['total_payment'], is_currency=True)
    print_result("Сумма переплаты", summary['overpayment'], is_currency=True)
    print_result("Эффективная процентная ставка", summary['effective_rate'], is_currency=False)
    print_result("Эффективная ставка", f"{summary['effective_rate']:.2f}%")
    
    # Для дифференцированных платежей показываем график
    if choice == '2' and summary['schedule']:
        print("\nГрафик платежей (первые 5 и последние 5):")
        print_separator('-', 80)
        print(f"{'Месяц':<6} {'Дата':<12} {'Платёж':<15} {'Основной долг':<15} {'Проценты':<12} {'Остаток':<15}")
        print_separator('-', 80)
        
        schedule = summary['schedule']
        display_months = list(range(5)) + list(range(max(5, len(schedule)-5), len(schedule)))
        display_months = sorted(set(display_months))[:10]
        
        for idx in display_months:
            item = schedule[idx]
            print(f"{item['month']:<6} {format_date(item['date']):<12} {format_currency(item['payment']):<15} "
                  f"{format_currency(item['principal']):<15} {format_currency(item['interest']):<12} "
                  f"{format_currency(item['remaining']):<15}")
        
        print_separator('-', 80)
    
    print()


def menu_deposit() -> None:
    """Меню депозитного калькулятора."""
    print_header("Депозитный калькулятор")
    
    # Ввод данных
    initial_amount = get_input_with_validation(
        "Введите начальную сумму вклада: ",
        validate_positive_number
    )
    
    annual_rate = get_input_with_validation(
        "Введите годовую процентную ставку (%): ",
        validate_positive_number
    )
    
    months = get_input_with_validation(
        "Введите срок вклада в месяцах: ",
        validate_integer,
        min_value=1
    )
    
    print("\nПериодичность капитализации:")
    print("  1. Ежемесячно")
    print("  2. Ежеквартально")
    print("  3. Ежегодно")
    
    cap_choice = input("Ваш выбор: ").strip()
    cap_map = {'1': 'monthly', '2': 'quarterly', '3': 'yearly'}
    capitalization_period = cap_map.get(cap_choice, 'monthly')
    
    monthly_contribution = get_input_with_validation(
        "\nВведите ежемесячное пополнение (0 если нет): ",
        validate_positive_number,
        allow_zero=True
    )
    
    inflation_rate = get_input_with_validation(
        "Введите ожидаемый уровень инфляции (%) (0 если не учитывать): ",
        validate_positive_number,
        allow_zero=True
    )
    
    # Расчёт
    result = calculate_deposit(
        initial_amount, annual_rate, months,
        capitalization_period, monthly_contribution, inflation_rate
    )
    
    # Вывод результатов
    print_header("Результаты расчёта")
    print_result("Итоговая сумма на счёте", result['final_amount'], is_currency=True)
    print_result("Внесено всего средств", result['total_contributions'], is_currency=True)
    print_result("Начисленные проценты", result['earned_interest'], is_currency=True)
    
    if inflation_rate > 0:
        print()
        print("С учётом инфляции:")
        print_result("Реальная стоимость", result['real_value'], is_currency=True)
        print_result("Реальный доход", result['real_earned'], is_currency=True)
        print_result("Реальная доходность (% годовых)", result['real_return_rate'])
    
    print()


def menu_investment() -> None:
    """Меню инвестиционного калькулятора."""
    print_header("Инвестиционный калькулятор")
    
    # Ввод данных
    initial_capital = get_input_with_validation(
        "Введите начальный капитал: ",
        validate_positive_number,
        allow_zero=True
    )
    
    monthly_contribution = get_input_with_validation(
        "Введите ежемесячный взнос: ",
        validate_positive_number,
        allow_zero=True
    )
    
    annual_return = get_input_with_validation(
        "Введите ожидаемую годовую доходность (%): ",
        validate_positive_number
    )
    
    years = get_input_with_validation(
        "Введите горизонт инвестирования (лет): ",
        validate_integer,
        min_value=1
    )
    
    # Расчёт
    result = calculate_investment(initial_capital, monthly_contribution, annual_return, years)
    
    # Вывод результатов
    print_header("Результаты расчёта")
    print_result("Итоговый капитал", result['final_capital'], is_currency=True)
    print_result("Сумма внесённых средств", result['total_contributed'], is_currency=True)
    print_result("Инвестиционный доход", result['investment_income'], is_currency=True)
    
    # Дополнительная статистика
    total_return_percent = ((result['final_capital'] - result['total_contributed']) / result['total_contributed'] * 100) if result['total_contributed'] > 0 else 0
    print_result("Общая доходность (%)", total_return_percent)
    
    print()


def menu_npv_irr() -> None:
    """Меню расчёта NPV и IRR."""
    print_header("Расчёт NPV и IRR")
    
    # Ввод данных
    initial_investment = get_input_with_validation(
        "Введите сумму начальных инвестиций: ",
        validate_positive_number
    )
    
    discount_rate = get_input_with_validation(
        "Введите ставку дисконтирования (%): ",
        validate_positive_number,
        allow_zero=True
    )
    
    print("\nВведите денежные потоки по периодам (по одному, пустая строка для завершения):")
    cash_flows: List[float] = []
    period = 1
    
    while True:
        cf_input = input(f"  Период {period}: ").strip()
        if not cf_input:
            break
        
        success, value, error = validate_positive_number(cf_input, allow_zero=True)
        if not success:
            # Пробуем как отрицательное число
            try:
                value = float(cf_input)
                success = True
            except ValueError:
                pass
        
        if success:
            cash_flows.append(value)
            period += 1
        else:
            print(f"Ошибка: {error}. Попробуйте снова.")
    
    if not cash_flows:
        print("Не введено ни одного денежного потока.")
        return
    
    # Расчёт
    npv = calculate_npv(initial_investment, cash_flows, discount_rate)
    irr = calculate_irr(initial_investment, cash_flows)
    
    # Вывод результатов
    print_header("Результаты расчёта")
    print_result("Чистая приведённая стоимость (NPV)", npv, is_currency=True)
    
    if irr is not None:
        print_result("Внутренняя норма доходности (IRR)", f"{irr:.2f}%")
    else:
        print("  IRR: не удалось вычислить")
    
    # Интерпретация
    print("\nИнтерпретация:")
    if npv > 0:
        print("  Проект прибыльный (NPV > 0)")
    elif npv < 0:
        print("  Проект убыточный (NPV < 0)")
    else:
        print("  Проект безубыточный (NPV = 0)")
    
    if irr is not None and irr > discount_rate:
        print(f"  IRR ({irr:.2f}%) > ставки дисконтирования ({discount_rate}%) - проект привлекателен")
    elif irr is not None:
        print(f"  IRR ({irr:.2f}%) < ставки дисконтирования ({discount_rate}%) - проект непривлекателен")
    
    print()


def menu_currency_converter() -> None:
    """Меню конвертера валют."""
    print_header("Конвертер валют")
    
    # Ввод данных
    amount = get_input_with_validation(
        "Введите сумму для конвертации: ",
        validate_positive_number
    )
    
    from_currency = input("Введите код исходной валюты (например, USD): ").strip().upper()
    to_currency = input("Введите код целевой валюты (например, EUR): ").strip().upper()
    
    if not from_currency or not to_currency:
        print("Коды валют не могут быть пустыми.")
        return
    
    try:
        result, rate, offline_mode = convert_currency(amount, from_currency, to_currency)
        
        print_header("Результат")
        print(f"  {format_currency(amount)} {from_currency} = {format_currency(result)} {to_currency}")
        print_result("Использованный курс", f"1 {from_currency} = {rate:.4f} {to_currency}")
        
        if offline_mode:
            print("\n⚠️  Использованы офлайн-курсы (API недоступен)")
    except ValueError as e:
        print(f"Ошибка: {e}")
    
    print()


def main_menu() -> None:
    """Главное меню приложения."""
    print_header("Финансовый калькулятор")
    print("Добро пожаловать! Выберите режим работы:\n")
    
    while True:
        print("  1. Кредитный калькулятор")
        print("  2. Депозитный калькулятор")
        print("  3. Инвестиционный калькулятор")
        print("  4. Расчёт NPV и IRR")
        print("  5. Конвертер валют")
        print("  0. Выход")
        print()
        
        choice = input("Ваш выбор: ").strip()
        
        if choice == '1':
            menu_credit()
        elif choice == '2':
            menu_deposit()
        elif choice == '3':
            menu_investment()
        elif choice == '4':
            menu_npv_irr()
        elif choice == '5':
            menu_currency_converter()
        elif choice == '0':
            print("\nСпасибо за использование финансового калькулятора. До свидания!")
            break
        else:
            print("\nНеверный выбор. Попробуйте снова.\n")


if __name__ == "__main__":
    main_menu()
