"""
Rule Engine - Deterministic business rules for shift validation.
Separated from AI for predictability and compliance.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any
from enum import Enum

from app.domain.models.shift import ShiftEntity, ShiftConflict, ShiftConflictType
from app.domain.models.employee import EmployeeEntity


class RuleSeverity(str, Enum):
    """Rule violation severity"""
    ERROR = "error"  # Must be fixed
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational


@dataclass
class RuleViolation:
    """Represents a rule violation"""
    rule_name: str
    rule_code: str
    message: str
    severity: RuleSeverity
    affected_entity_type: str
    affected_entity_id: Optional[int] = None
    suggested_fix: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Rule(ABC):
    """Base class for all business rules"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable rule name"""
        pass
    
    @property
    @abstractmethod
    def code(self) -> str:
        """Unique rule identifier"""
        pass
    
    @property
    def severity(self) -> RuleSeverity:
        """Default severity for violations"""
        return RuleSeverity.ERROR
    
    @property
    def is_enabled(self) -> bool:
        """Can be toggled for testing/special cases"""
        return True
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """
        Evaluate the rule against given context.
        Returns list of violations (empty if rule passes).
        """
        pass


class LaborLawRule(Rule):
    """
    Labor law compliance rules.
    These are non-negotiable legal requirements.
    """
    
    # Turkish Labor Law defaults (can be overridden per region)
    MAX_DAILY_HOURS = 11
    MAX_WEEKLY_HOURS = 45
    MIN_DAILY_REST_HOURS = 11
    MIN_WEEKLY_REST_HOURS = 24
    MAX_CONSECUTIVE_DAYS = 6
    MIN_BREAK_FOR_6H_SHIFT = 30  # minutes
    MIN_BREAK_FOR_9H_SHIFT = 60  # minutes
    
    @property
    def name(self) -> str:
        return "Labor Law Compliance"
    
    @property
    def code(self) -> str:
        return "LABOR_LAW_001"
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        
        shift: ShiftEntity = context.get("shift")
        employee: EmployeeEntity = context.get("employee")
        existing_shifts: List[ShiftEntity] = context.get("existing_shifts", [])
        
        if not shift or not employee:
            return violations
        
        # Check daily hours
        if shift.duration_hours > self.MAX_DAILY_HOURS:
            violations.append(RuleViolation(
                rule_name=self.name,
                rule_code=f"{self.code}_DAILY_HOURS",
                message=f"Shift duration ({shift.duration_hours:.1f}h) exceeds legal daily maximum ({self.MAX_DAILY_HOURS}h)",
                severity=RuleSeverity.ERROR,
                affected_entity_type="shift",
                affected_entity_id=shift.id,
                suggested_fix=f"Reduce shift duration to maximum {self.MAX_DAILY_HOURS} hours"
            ))
        
        # Check rest period between shifts
        for existing in existing_shifts:
            if existing.employee_id != shift.employee_id:
                continue
            
            # Calculate gap between shifts
            if shift.start_time > existing.end_time:
                gap_hours = (shift.start_time - existing.end_time).total_seconds() / 3600
                if gap_hours < self.MIN_DAILY_REST_HOURS:
                    violations.append(RuleViolation(
                        rule_name=self.name,
                        rule_code=f"{self.code}_REST_PERIOD",
                        message=f"Rest period ({gap_hours:.1f}h) between shifts is below legal minimum ({self.MIN_DAILY_REST_HOURS}h)",
                        severity=RuleSeverity.ERROR,
                        affected_entity_type="shift",
                        affected_entity_id=shift.id,
                        suggested_fix=f"Ensure at least {self.MIN_DAILY_REST_HOURS} hours between shifts",
                        metadata={"previous_shift_id": existing.id}
                    ))
        
        # Check consecutive working days
        if employee.consecutive_working_days >= self.MAX_CONSECUTIVE_DAYS:
            violations.append(RuleViolation(
                rule_name=self.name,
                rule_code=f"{self.code}_CONSECUTIVE_DAYS",
                message=f"Employee has worked {employee.consecutive_working_days} consecutive days (max {self.MAX_CONSECUTIVE_DAYS})",
                severity=RuleSeverity.ERROR,
                affected_entity_type="employee",
                affected_entity_id=employee.id,
                suggested_fix="Employee must have at least 1 day off"
            ))
        
        return violations


class OvertimeRule(Rule):
    """
    Overtime management rules.
    Controls overtime allocation and limits.
    """
    
    @property
    def name(self) -> str:
        return "Overtime Management"
    
    @property
    def code(self) -> str:
        return "OVERTIME_001"
    
    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING  # Overtime is allowed but should be monitored
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        
        employee: EmployeeEntity = context.get("employee")
        shift: ShiftEntity = context.get("shift")
        
        if not employee or not shift:
            return violations
        
        # Calculate projected hours
        projected_hours = employee.total_hours_this_week + shift.duration_hours
        
        # Check if entering overtime
        if projected_hours > employee.weekly_working_limit:
            overtime_hours = projected_hours - employee.weekly_working_limit
            
            if overtime_hours > employee.overtime_limit:
                violations.append(RuleViolation(
                    rule_name=self.name,
                    rule_code=f"{self.code}_LIMIT_EXCEEDED",
                    message=f"Projected overtime ({overtime_hours:.1f}h) exceeds employee limit ({employee.overtime_limit}h)",
                    severity=RuleSeverity.ERROR,
                    affected_entity_type="employee",
                    affected_entity_id=employee.id,
                    suggested_fix="Assign shift to another employee or reduce hours"
                ))
            else:
                violations.append(RuleViolation(
                    rule_name=self.name,
                    rule_code=f"{self.code}_OVERTIME_ENTERED",
                    message=f"This shift will result in {overtime_hours:.1f}h overtime for the employee",
                    severity=RuleSeverity.WARNING,
                    affected_entity_type="employee",
                    affected_entity_id=employee.id,
                    metadata={"overtime_hours": overtime_hours}
                ))
        
        return violations


class RestPeriodRule(Rule):
    """
    Rest period and break rules.
    Ensures adequate rest between shifts and during long shifts.
    """
    
    MIN_REST_HOURS = 11
    BREAK_THRESHOLD_HOURS = 6
    REQUIRED_BREAK_MINUTES = 30
    
    @property
    def name(self) -> str:
        return "Rest Period Requirements"
    
    @property
    def code(self) -> str:
        return "REST_001"
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        
        shift: ShiftEntity = context.get("shift")
        previous_shift: Optional[ShiftEntity] = context.get("previous_shift")
        
        if not shift:
            return violations
        
        # Check break requirement for long shifts
        if shift.duration_hours >= self.BREAK_THRESHOLD_HOURS:
            violations.append(RuleViolation(
                rule_name=self.name,
                rule_code=f"{self.code}_BREAK_REQUIRED",
                message=f"Shift of {shift.duration_hours:.1f}h requires a {self.REQUIRED_BREAK_MINUTES} minute break",
                severity=RuleSeverity.INFO,
                affected_entity_type="shift",
                affected_entity_id=shift.id
            ))
        
        # Check rest period from previous shift
        if previous_shift:
            rest_hours = (shift.start_time - previous_shift.end_time).total_seconds() / 3600
            if rest_hours < self.MIN_REST_HOURS:
                violations.append(RuleViolation(
                    rule_name=self.name,
                    rule_code=f"{self.code}_INSUFFICIENT_REST",
                    message=f"Only {rest_hours:.1f}h rest between shifts (minimum {self.MIN_REST_HOURS}h required)",
                    severity=RuleSeverity.ERROR,
                    affected_entity_type="shift",
                    affected_entity_id=shift.id,
                    suggested_fix=f"Move shift start to at least {self.MIN_REST_HOURS}h after previous shift ends"
                ))
        
        return violations


class AvailabilityRule(Rule):
    """Check shift against employee availability"""
    
    @property
    def name(self) -> str:
        return "Employee Availability"
    
    @property
    def code(self) -> str:
        return "AVAIL_001"
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        violations = []
        
        shift: ShiftEntity = context.get("shift")
        employee: EmployeeEntity = context.get("employee")
        
        if not shift or not employee:
            return violations
        
        day_of_week = shift.start_time.weekday()
        shift_start_time = shift.start_time.time()
        
        if not employee.is_available_at(day_of_week, shift_start_time):
            violations.append(RuleViolation(
                rule_name=self.name,
                rule_code=f"{self.code}_NOT_AVAILABLE",
                message=f"Employee is not available on {shift.start_time.strftime('%A')} at {shift_start_time}",
                severity=RuleSeverity.ERROR,
                affected_entity_type="shift",
                affected_entity_id=shift.id,
                suggested_fix="Assign to a different employee or modify employee availability"
            ))
        
        return violations


class RuleEngine:
    """
    Central rule engine that evaluates all business rules.
    Provides deterministic, auditable validation separate from AI.
    """
    
    def __init__(self):
        self.rules: List[Rule] = [
            LaborLawRule(),
            OvertimeRule(),
            RestPeriodRule(),
            AvailabilityRule(),
        ]
        self._custom_rules: List[Rule] = []
    
    def register_rule(self, rule: Rule):
        """Add a custom rule to the engine"""
        self._custom_rules.append(rule)
    
    def get_all_rules(self) -> List[Rule]:
        """Get all registered rules"""
        return self.rules + self._custom_rules
    
    def evaluate_shift(
        self,
        shift: ShiftEntity,
        employee: EmployeeEntity,
        existing_shifts: List[ShiftEntity] = None,
        previous_shift: ShiftEntity = None
    ) -> List[RuleViolation]:
        """
        Evaluate all rules for a shift assignment.
        Returns list of all violations.
        """
        context = {
            "shift": shift,
            "employee": employee,
            "existing_shifts": existing_shifts or [],
            "previous_shift": previous_shift,
        }
        
        all_violations = []
        
        for rule in self.get_all_rules():
            if rule.is_enabled:
                violations = rule.evaluate(context)
                all_violations.extend(violations)
        
        return all_violations
    
    def has_blocking_violations(self, violations: List[RuleViolation]) -> bool:
        """Check if any violations are blocking (ERROR severity)"""
        return any(v.severity == RuleSeverity.ERROR for v in violations)
    
    def get_violations_by_severity(self, violations: List[RuleViolation]) -> Dict[RuleSeverity, List[RuleViolation]]:
        """Group violations by severity"""
        result = {s: [] for s in RuleSeverity}
        for v in violations:
            result[v.severity].append(v)
        return result
    
    def format_violations_report(self, violations: List[RuleViolation]) -> str:
        """Generate human-readable violations report"""
        if not violations:
            return "✅ All rules passed"
        
        by_severity = self.get_violations_by_severity(violations)
        
        lines = []
        for severity in [RuleSeverity.ERROR, RuleSeverity.WARNING, RuleSeverity.INFO]:
            items = by_severity[severity]
            if items:
                emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[severity.value]
                lines.append(f"\n{emoji} {severity.value.upper()} ({len(items)}):")
                for v in items:
                    lines.append(f"  • [{v.rule_code}] {v.message}")
                    if v.suggested_fix:
                        lines.append(f"    → Fix: {v.suggested_fix}")
        
        return "\n".join(lines)
