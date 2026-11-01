"""Алгоритмы планирования лечения в частной стоматологической клинике.

Процедурная реализация: данные хранятся в словарях и списках,
обработка выполняется отдельными функциями.
"""
import heapq
from datetime import date, timedelta

SUNDAY = 6
PREP_MINUTES = 15  # подготовка кабинета и обработка инструментов


def visit_specialty(visit, services):
    """Специальность врача для приёма (по первой услуге приёма)."""
    return services[visit["items"][0]["code"]]["specialty"]


def calc_plan_cost(plan, services):
    """Алгоритм 1. Стоимость плана лечения, руб.

    Внешний цикл - по приёмам плана, внутренний - по услугам приёма.
    """
    total = 0.0
    for visit in plan["visits"]:
        for item in visit["items"]:
            price = services[item["code"]]["price"]
            total += price * item["qty"]
    total = total * plan["category_coef"] * (1 - plan["discount"] / 100)
    return round(total, 2)


def visit_hours(visit, services):
    """Длительность приёма, ч (формула 2.2)."""
    minutes = PREP_MINUTES
    for item in visit["items"]:
        minutes += services[item["code"]]["minutes"] * item["qty"]
    return round(minutes / 60, 2)


def next_working_day(day, holidays):
    """Ближайший рабочий день: воскресенья и праздники пропускаются."""
    while day.weekday() == SUNDAY or day.isoformat() in holidays:
        day += timedelta(days=1)
    return day


def visit_dates(plan, holidays):
    """Даты всех приёмов плана лечения."""
    dates = []
    current = next_working_day(date.fromisoformat(plan["start_date"]), holidays)
    for _ in plan["visits"]:
        dates.append(current)
        current = next_working_day(current + timedelta(days=plan["interval_days"]),
                                   holidays)
    return dates


def build_schedule(plans, services, year, month, holidays):
    """Алгоритм 2. Формирование списка приёмов на месяц.

    Приёмы сортируются по дате, а внутри дня - по убыванию
    длительности (так их удобнее распределять между врачами).
    """
    tasks = []
    for plan in plans:
        dates = visit_dates(plan, holidays)
        for number, (visit, day) in enumerate(zip(plan["visits"], dates), start=1):
            if day.year != year or day.month != month:
                continue
            tasks.append({"date": day, "plan_id": plan["id"], "visit_no": number,
                          "specialty": visit_specialty(visit, services),
                          "hours": visit_hours(visit, services)})
    tasks.sort(key=lambda t: (t["date"], -t["hours"]))
    return tasks


def assign_tasks(tasks, doctors):
    """Алгоритм 3. Распределение приёмов между врачами.

    Для каждого дня и каждой специальности создаётся минимальная куча
    врачей, упорядоченных по остатку времени смены (меньше значение -
    больше свободного времени). Приём получает врач с наибольшим
    остатком. Если приём не помещается даже к нему, он попадает
    в список нераспределённых.
    """
    capacity = {d["id"]: d["capacity_hours"] for d in doctors}
    assigned = []
    unassigned = []
    heaps = {}
    current_day = None
    for task in tasks:
        if task["date"] != current_day:
            current_day = task["date"]
            heaps = {}
        spec = task["specialty"]
        if spec not in heaps:
            heaps[spec] = [(-d["capacity_hours"], d["id"])
                           for d in doctors if d["specialty"] == spec]
            heapq.heapify(heaps[spec])
        if not heaps[spec]:
            unassigned.append(task)
            continue
        free, doctor_id = heapq.heappop(heaps[spec])
        free = -free
        if task["hours"] <= free:
            assigned.append(dict(task, doctor_id=doctor_id))
            free -= task["hours"]
        else:
            unassigned.append(task)
        heapq.heappush(heaps[spec], (-free, doctor_id))
    return assigned, unassigned


def count_visits(tasks, plan_id):
    """Число приёмов и суммарная длительность для плана лечения."""
    count = 0
    hours = 0.0
    for task in tasks:
        if task["plan_id"] == plan_id:
            count += 1
            hours += task["hours"]
    return count, round(hours, 2)
