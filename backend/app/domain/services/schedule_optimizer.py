"""
Constraint-aware shift schedule optimizer.

Builds a schedule for a date range by filling each (day, department, shift type)
slot with the best-scoring eligible employees.

Hard constraints (never violated):
    * one shift per employee per day
    * weekly hour cap (contract limit, plus overtime only when allowed)
    * minimum rest between consecutive shifts
    * maximum consecutive working days
    * declared availability days and preferred weekly day off

Soft objectives (weighted score):
    * preferred shift type
    * balanced workload across the team

The algorithm is a deterministic greedy assignment: the same input always
produces the same schedule, which keeps results explainable and reviewable.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class ShiftType:
    key: str
    label: str
    start: time
    end: time

    @property
    def hours(self) -> float:
        start = datetime.combine(date.min, self.start)
        end = datetime.combine(date.min, self.end)
        if end <= start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600

    def window(self, day: date) -> Tuple[datetime, datetime]:
        start = datetime.combine(day, self.start)
        end = datetime.combine(day, self.end)
        if end <= start:
            end += timedelta(days=1)
        return start, end


SHIFT_TYPES: Dict[str, ShiftType] = {
    "morning": ShiftType("morning", "Morning", time(6), time(14)),
    "day": ShiftType("day", "Day", time(9), time(17)),
    "afternoon": ShiftType("afternoon", "Evening", time(14), time(22)),
    "night": ShiftType("night", "Night", time(22), time(6)),
}

# Python weekday (0 = Monday) -> name
WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class OptimizerSettings:
    shift_types: List[str] = field(default_factory=lambda: ["morning", "day", "afternoon"])
    operating_days: List[str] = field(default_factory=lambda: WEEKDAY_NAMES[:5])
    is_24_7: bool = False
    min_employees_per_shift: int = 2
    max_employees_per_shift: int = 10
    max_hours_per_week: float = 45
    max_consecutive_days: int = 5
    min_rest_hours: float = 11
    allow_overtime: bool = False
    consider_preferences: bool = True
    preference_weight: float = 70  # 0-100
    balance_workload: bool = True


@dataclass
class EmployeeInput:
    id: int
    name: str
    department_id: int
    department_name: Optional[str]
    weekly_limit: float = 40.0
    overtime_limit: float = 10.0
    # Sunday-based day numbers (0 = Sunday) the employee declared as available; empty = any day
    available_days: Optional[set] = None
    preferred_shift: Optional[str] = None
    weekly_off_day: Optional[int] = None  # Sunday-based (0 = Sunday)


@dataclass
class ExistingShift:
    employee_id: int
    start: datetime
    end: datetime
    department_id: Optional[int] = None


@dataclass
class Assignment:
    employee_id: int
    employee_name: str
    department_id: int
    department_name: Optional[str]
    shift_type: str
    start: datetime
    end: datetime
    preferred: bool


@dataclass
class Warning:
    type: str
    message: str
    employee_id: int = 0


@dataclass
class OptimizationOutcome:
    assignments: List[Assignment]
    warnings: List[Warning]
    score: float
    metrics: Dict[str, float]


def _sunday_based(day: date) -> int:
    return (day.weekday() + 1) % 7


def _week_key(day: date) -> date:
    return day - timedelta(days=day.weekday())


class ScheduleOptimizer:
    def __init__(self, settings: OptimizerSettings):
        self.settings = settings
        self.types = [SHIFT_TYPES[k] for k in SHIFT_TYPES if k in settings.shift_types] or [SHIFT_TYPES["day"]]

    # ------------------------------------------------------------------ helpers
    def _operating(self, day: date) -> bool:
        return self.settings.is_24_7 or WEEKDAY_NAMES[day.weekday()] in self.settings.operating_days

    def _weekly_cap(self, emp: EmployeeInput) -> float:
        cap = emp.weekly_limit + (emp.overtime_limit if self.settings.allow_overtime else 0)
        return min(cap, self.settings.max_hours_per_week)

    def _demand(self, team_size: int, operating_days_per_week: int) -> int:
        """How many people one slot needs so the team works roughly its contract hours."""
        avg_shift = sum(t.hours for t in self.types) / len(self.types)
        shifts_per_person = 40 / avg_shift
        per_day = team_size * shifts_per_person / max(operating_days_per_week, 1)
        target = math.floor(per_day / len(self.types))
        return max(self.settings.min_employees_per_shift, min(self.settings.max_employees_per_shift, target))

    # --------------------------------------------------------------------- main
    def optimize(
        self,
        employees: Iterable[EmployeeInput],
        start_date: date,
        end_date: date,
        existing: Iterable[ExistingShift] = (),
    ) -> OptimizationOutcome:
        s = self.settings
        employees = list(employees)
        by_dept: Dict[int, List[EmployeeInput]] = defaultdict(list)
        for emp in employees:
            by_dept[emp.department_id].append(emp)

        week_hours: Dict[Tuple[int, date], float] = defaultdict(float)
        worked_days: Dict[int, set] = defaultdict(set)
        last_end: Dict[int, datetime] = {}
        # Slots that existing shifts already staff: (department, slot start) -> people
        already_staffed: Dict[Tuple[int, datetime], int] = defaultdict(int)
        for shift in existing:
            if shift.department_id is not None:
                already_staffed[(shift.department_id, shift.start)] += 1
            week_hours[(shift.employee_id, _week_key(shift.start.date()))] += (shift.end - shift.start).total_seconds() / 3600
            worked_days[shift.employee_id].add(shift.start.date())
            if shift.employee_id not in last_end or shift.end > last_end[shift.employee_id]:
                last_end[shift.employee_id] = shift.end

        operating_per_week = 7 if s.is_24_7 else max(len(s.operating_days), 1)
        w_pref = (s.preference_weight / 100) if s.consider_preferences else 0.0
        w_balance = (1 - w_pref) if s.balance_workload else 0.0

        assignments: List[Assignment] = []
        warnings: List[Warning] = []
        demand_total = 0
        filled_total = 0
        overtime_flagged: set = set()

        day = start_date
        while day <= end_date:
            if not self._operating(day):
                day += timedelta(days=1)
                continue
            dow = _sunday_based(day)
            week = _week_key(day)

            for stype in self.types:
                slot_start, slot_end = stype.window(day)
                for dept_id, team in sorted(by_dept.items()):
                    demand = self._demand(len(team), operating_per_week)
                    demand_total += demand
                    staffed = min(already_staffed[(dept_id, slot_start)], demand)
                    filled_total += staffed
                    needed = demand - staffed

                    candidates = []
                    for emp in team:
                        if day in worked_days[emp.id]:
                            continue
                        if emp.available_days and dow not in emp.available_days:
                            continue
                        if s.consider_preferences and emp.weekly_off_day is not None and emp.weekly_off_day == dow:
                            continue
                        hours = week_hours[(emp.id, week)]
                        cap = self._weekly_cap(emp)
                        if hours + stype.hours > cap:
                            continue
                        prev_end = last_end.get(emp.id)
                        if prev_end and (slot_start - prev_end).total_seconds() / 3600 < s.min_rest_hours:
                            continue
                        streak = 0
                        d = day - timedelta(days=1)
                        while d in worked_days[emp.id]:
                            streak += 1
                            d -= timedelta(days=1)
                        if streak >= s.max_consecutive_days:
                            continue

                        preferred = emp.preferred_shift == stype.key
                        pref_score = 1.0 if preferred else (0.0 if emp.preferred_shift else 0.5)
                        balance_score = 1 - hours / cap if cap else 0
                        score = w_pref * pref_score + w_balance * balance_score
                        # Deterministic tie-breaker that still rotates people across days
                        tiebreak = ((emp.id * 7919 + day.toordinal() * 31 + len(stype.key)) % 1000) / 1e6
                        candidates.append((score + tiebreak, emp, preferred))

                    candidates.sort(key=lambda c: c[0], reverse=True)
                    chosen = candidates[:needed]
                    filled_total += len(chosen)

                    for _, emp, preferred in chosen:
                        assignments.append(Assignment(
                            employee_id=emp.id,
                            employee_name=emp.name,
                            department_id=emp.department_id,
                            department_name=emp.department_name,
                            shift_type=stype.key,
                            start=slot_start,
                            end=slot_end,
                            preferred=preferred,
                        ))
                        week_hours[(emp.id, week)] += stype.hours
                        worked_days[emp.id].add(day)
                        last_end[emp.id] = slot_end
                        if week_hours[(emp.id, week)] > emp.weekly_limit and (emp.id, week) not in overtime_flagged:
                            overtime_flagged.add((emp.id, week))
                            warnings.append(Warning(
                                "overtime",
                                f"{emp.name} is scheduled for {week_hours[(emp.id, week)]:.0f}h in the week of "
                                f"{week:%b %d} (contract: {emp.weekly_limit:.0f}h).",
                                emp.id,
                            ))

                    if staffed + len(chosen) < s.min_employees_per_shift:
                        dept_name = team[0].department_name or f"Department {dept_id}"
                        warnings.append(Warning(
                            "understaffed",
                            f"{dept_name}: {stype.label} shift on {day:%a %b %d} has {staffed + len(chosen)} of "
                            f"{s.min_employees_per_shift} required people.",
                        ))
            day += timedelta(days=1)

        metrics = self._metrics(assignments, employees, demand_total, filled_total)
        return OptimizationOutcome(assignments, warnings, metrics["score"], metrics)

    def _metrics(self, assignments, employees, demand_total, filled_total) -> Dict[str, float]:
        coverage = filled_total / demand_total if demand_total else 0.0

        emp_pref = {e.id: e.preferred_shift for e in employees}
        pref_relevant = [a for a in assignments if emp_pref.get(a.employee_id)]
        preference = (sum(a.preferred for a in pref_relevant) / len(pref_relevant)) if pref_relevant else 1.0

        hours: Dict[int, float] = defaultdict(float)
        for a in assignments:
            hours[a.employee_id] += (a.end - a.start).total_seconds() / 3600
        values = [hours.get(e.id, 0.0) for e in employees]
        if values and sum(values):
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
            fairness = max(0.0, 1 - std / mean)
        else:
            fairness = 0.0

        if self.settings.consider_preferences:
            score = 100 * (0.45 * coverage + 0.30 * preference + 0.25 * fairness)
        else:
            score = 100 * (0.60 * coverage + 0.40 * fairness)

        return {
            "score": round(score, 1),
            "coverage": round(coverage * 100, 1),
            "preference_match": round(preference * 100, 1),
            "fairness": round(fairness * 100, 1),
            "total_hours": round(sum(values), 1),
            "employees_scheduled": sum(1 for v in values if v > 0),
        }
