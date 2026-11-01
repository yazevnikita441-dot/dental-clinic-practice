"""Планирование лечения пациентов на месяц (процедурная версия)."""
import csv
import json
import os

from algorithms import (assign_tasks, build_schedule, calc_plan_cost,
                        count_visits)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "sample_data.json")
YEAR, MONTH = 2026, 11


def load_data(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_schedule(path, assigned):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Дата", "План", "Приём", "Специальность",
                         "Часы", "Врач"])
        for t in assigned:
            writer.writerow([t["date"].isoformat(), t["plan_id"], t["visit_no"],
                             t["specialty"], t["hours"], t["doctor_id"]])


def main():
    data = load_data(DATA_FILE)
    services = {s["code"]: s for s in data["services"]}
    holidays = set(data["holidays"])
    tasks = build_schedule(data["plans"], services, YEAR, MONTH, holidays)
    assigned, unassigned = assign_tasks(tasks, data["doctors"])

    print(f"План лечения на {MONTH:02d}.{YEAR}")
    print("-" * 66)
    total = 0.0
    for plan in data["plans"]:
        visits, hours = count_visits(tasks, plan["id"])
        cost = calc_plan_cost(plan, services)
        total += cost
        print(f"{plan['patient']:<16} приёмов: {visits:>2} часов: {hours:>5.2f} "
              f"стоимость: {cost:>10.2f} руб.")
    print("-" * 66)
    print(f"Итого по планам лечения: {total:.2f} руб.")
    print(f"Приёмов всего: {len(tasks)}, распределено: {len(assigned)}, "
          f"не распределено: {len(unassigned)}")
    for t in unassigned:
        print(f"  нет свободного врача: {t['date']} план {t['plan_id']} "
              f"({t['specialty']}, {t['hours']} ч)")

    out_file = os.path.join(BASE_DIR, "data", f"schedule_{YEAR}_{MONTH:02d}.csv")
    save_schedule(out_file, assigned)
    print(f"График сохранён: {os.path.relpath(out_file, BASE_DIR)}")


if __name__ == "__main__":
    main()
