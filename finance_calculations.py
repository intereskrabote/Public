"""
finance_calculations.py - Математические функции для финансовых расчётов.
Все функции не содержат ввода/вывода, только вычисления.
"""

import math
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple


def calculate_annuity_payment(principal: float, annual_rate: float, months: int) -> float:
    """
    Рассчитывает ежемесячный аннуитетный платёж по кредиту.
    
    :param principal: Сумма кредита
    :param annual_rate: Годовая процентная ставка (в процентах, например 12 для 12%)
    :param months: Срок кредита в месяцах
    :return: Ежемесячный платёж
    """
    if annual_rate == 0:
        return principal / months
    
    monthly_rate = annual_rate / 100 / 12
    # Формула аннуитетного платежа: A = P * r * (1+r)^n / ((1+r)^n - 1)
    payment = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
    return payment


def calculate_differentiated_schedule(
    principal: float, 
    annual_rate: float, 
    months: int, 
    start_date: Optional[date] = None
) -> List[Dict]:
    """
    Рассчитывает график дифференцированных платежей по кредиту.
    
    :param principal: Сумма кредита
    :param annual_rate: Годовая процентная ставка (в процентах)
    :param months: Срок кредита в месяцах
    :param start_date: Дата первого платежа (опционально)
    :return: Список словарей с информацией о каждом платеже
    """
    if start_date is None:
        start_date = date.today()
    
    schedule = []
    remaining_principal = principal
    monthly_principal = principal / months
    monthly_rate = annual_rate / 100 / 12
    
    for month in range(1, months + 1):
        # Вычисляем дату платежа (примерно +30 дней в месяц)
        payment_date = start_date + timedelta(days=30 * month)
        
        # Проценты за текущий месяц
        interest = remaining_principal * monthly_rate
        
        # Общий платёж
        total_payment = monthly_principal + interest
        
        # Остаток после платежа
        remaining_principal -= monthly_principal
        if remaining_principal < 0:
            remaining_principal = 0
        
        schedule.append({
            'month': month,
            'date': payment_date,
            'payment': total_payment,
            'principal': monthly_principal,
            'interest': interest,
            'remaining': remaining_principal
        })
    
    return schedule


def calculate_credit_summary(
    principal: float, 
    annual_rate: float, 
    months: int, 
    payment_type: str = 'annuity',
    start_date: Optional[date] = None
) -> Dict:
    """
    Рассчитывает общую информацию по кредиту.
    
    :param principal: Сумма кредита
    :param annual_rate: Годовая процентная ставка (в процентах)
    :param months: Срок кредита в месяцах
    :param payment_type: Тип платежа ('annuity' или 'differentiated')
    :param start_date: Дата первого платежа (опционально)
    :return: Словарь с общей суммой выплат, переплатой и эффективной ставкой
    """
    if payment_type == 'annuity':
        monthly_payment = calculate_annuity_payment(principal, annual_rate, months)
        total_payment = monthly_payment * months
        schedule = None
    else:
        schedule = calculate_differentiated_schedule(principal, annual_rate, months, start_date)
        total_payment = sum(item['payment'] for item in schedule)
        monthly_payment = None
    
    overpayment = total_payment - principal
    years = months / 12
    
    # Эффективная ставка (упрощённо)
    effective_rate = (total_payment / principal - 1) / years * 100 if years > 0 else 0
    
    return {
        'monthly_payment': monthly_payment,
        'total_payment': total_payment,
        'overpayment': overpayment,
        'effective_rate': effective_rate,
        'schedule': schedule
    }


def calculate_deposit(
    initial_amount: float, 
    annual_rate: float, 
    months: int, 
    capitalization_period: str = 'monthly',
    monthly_contribution: float = 0,
    inflation_rate: float = 0
) -> Dict:
    """
    Рассчитывает итоговую сумму по депозиту с учётом капитализации и пополнений.
    
    :param initial_amount: Начальная сумма вклада
    :param annual_rate: Годовая процентная ставка (в процентах)
    :param months: Срок вклада в месяцах
    :param capitalization_period: Периодичность капитализации ('monthly', 'quarterly', 'yearly')
    :param monthly_contribution: Ежемесячное пополнение
    :param inflation_rate: Ожидаемый уровень инфляции (в процентах)
    :return: Словарь с итоговой суммой, начисленными процентами и реальной доходностью
    """
    periods_map = {'monthly': 1, 'quarterly': 3, 'yearly': 12}
    cap_months = periods_map.get(capitalization_period, 1)
    
    balance = initial_amount
    total_contributions = initial_amount
    monthly_rate = annual_rate / 100 / 12
    
    for month in range(1, months + 1):
        # Добавляем ежемесячное пополнение
        if monthly_contribution > 0:
            balance += monthly_contribution
            total_contributions += monthly_contribution
        
        # Капитализация процентов
        if month % cap_months == 0:
            interest = balance * monthly_rate * cap_months
            balance += interest
    
    earned_interest = balance - total_contributions
    
    # Расчёт реальной доходности с учётом инфляции
    if inflation_rate > 0:
        # Реальная доходность по формуле Фишера (упрощённо)
        real_return_rate = ((1 + annual_rate / 100) / (1 + inflation_rate / 100) - 1) * 100
        # Корректируем итоговую сумму на инфляцию
        inflation_factor = (1 + inflation_rate / 100) ** (months / 12)
        real_value = balance / inflation_factor
        real_earned = real_value - total_contributions
    else:
        real_return_rate = annual_rate
        real_value = balance
        real_earned = earned_interest
    
    return {
        'final_amount': balance,
        'total_contributions': total_contributions,
        'earned_interest': earned_interest,
        'real_value': real_value,
        'real_earned': real_earned,
        'real_return_rate': real_return_rate
    }


def calculate_investment(
    initial_capital: float, 
    monthly_contribution: float, 
    annual_return: float, 
    years: int
) -> Dict:
    """
    Рассчитывает итоговый капитал при инвестировании со сложным процентом.
    
    :param initial_capital: Начальный капитал
    :param monthly_contribution: Ежемесячный взнос
    :param annual_return: Ожидаемая годовая доходность (в процентах)
    :param years: Горизонт инвестирования в годах
    :return: Словарь с итоговым капиталом, суммой внесённых средств и доходом
    """
    months = years * 12
    monthly_rate = annual_return / 100 / 12
    
    balance = initial_capital
    total_contributed = initial_capital
    
    for _ in range(months):
        # Начисляем проценты
        balance *= (1 + monthly_rate)
        # Добавляем взнос
        balance += monthly_contribution
        total_contributed += monthly_contribution
    
    investment_income = balance - total_contributed
    
    return {
        'final_capital': balance,
        'total_contributed': total_contributed,
        'investment_income': investment_income
    }


def calculate_npv(initial_investment: float, cash_flows: List[float], discount_rate: float) -> float:
    """
    Рассчитывает чистую приведённую стоимость (NPV).
    
    :param initial_investment: Начальные инвестиции (положительное число)
    :param cash_flows: Список денежных потоков по периодам
    :param discount_rate: Ставка дисконтирования (в процентах)
    :return: NPV проекта
    """
    rate = discount_rate / 100
    npv = -initial_investment
    
    for t, cf in enumerate(cash_flows, 1):
        npv += cf / ((1 + rate) ** t)
    
    return npv


def calculate_irr(initial_investment: float, cash_flows: List[float], max_iterations: int = 100, tolerance: float = 1e-6) -> Optional[float]:
    """
    Рассчитывает внутреннюю норму доходности (IRR) методом Ньютона.
    
    :param initial_investment: Начальные инвестиции (положительное число)
    :param cash_flows: Список денежных потоков по периодам
    :param max_iterations: Максимальное количество итераций
    :param tolerance: Точность вычислений
    :return: IRR в процентах или None, если не удалось найти
    """
    # Полные денежные потоки (с учётом начальных инвестиций)
    flows = [-initial_investment] + cash_flows
    n = len(flows)
    
    # Начальное приближение
    irr = 0.1
    
    for _ in range(max_iterations):
        # Вычисляем NPV и её производную
        npv = 0.0
        d_npv = 0.0
        
        for t, cf in enumerate(flows):
            if t == 0:
                npv += cf
            else:
                npv += cf / ((1 + irr) ** t)
                d_npv -= t * cf / ((1 + irr) ** (t + 1))
        
        if abs(d_npv) < 1e-10:
            break
        
        new_irr = irr - npv / d_npv
        
        if abs(new_irr - irr) < tolerance:
            return new_irr * 100
        
        irr = new_irr
        
        # Защита от выхода за разумные пределы
        if irr < -0.99 or irr > 10:
            break
    
    return None


def get_effective_rate_from_schedule(schedule: List[Dict], principal: float, months: int) -> float:
    """
    Вычисляет эффективную ставку на основе графика платежей.
    
    :param schedule: График платежей
    :param principal: Сумма кредита
    :param months: Срок в месяцах
    :return: Эффективная годовая ставка в процентах
    """
    total_payment = sum(item['payment'] for item in schedule)
    years = months / 12
    return (total_payment / principal - 1) / years * 100 if years > 0 else 0
