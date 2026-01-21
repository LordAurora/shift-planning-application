"""
Shift Optimization Service - Orchestrates AI and Rule Engine for shift planning.
"""
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import logging

from app.domain.models.shift import ShiftEntity, ShiftAssignment, ShiftStatus
from app.domain.models.employee import EmployeeEntity
from app.domain.services.rule_engine import RuleEngine, RuleViolation, RuleSeverity

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Strategies for shift optimization"""
    BALANCED = "balanced"  # Balance workload across employees
    MINIMIZE_OVERTIME = "minimize_overtime"  # Minimize overtime costs
    MAXIMIZE_PREFERENCES = "maximize_preferences"  # Prioritize employee preferences
    EMERGENCY = "emergency"  # Fill gaps immediately
    COST_EFFECTIVE = "cost_effective"  # Minimize total cost


class AssignmentSource(str, Enum):
    """How an assignment was determined"""
    MANUAL = "manual"
    RULE_BASED = "rule_based"
    AI_OPTIMIZED = "ai_optimized"
    AUTO_REBALANCE = "auto_rebalance"


@dataclass
class OptimizationConstraints:
    """Constraints for the optimization algorithm"""
    min_employees_per_shift: int = 1
    max_employees_per_shift: int = 10
    required_skills: List[str] = field(default_factory=list)
    preferred_departments: List[int] = field(default_factory=list)
    exclude_employees: List[int] = field(default_factory=list)
    force_include_employees: List[int] = field(default_factory=list)
    respect_preferences: bool = True
    allow_overtime: bool = True
    max_overtime_percentage: float = 0.25  # 25% overtime allowed


@dataclass 
class OptimizationResult:
    """Result of an optimization run"""
    success: bool
    assignments: List[ShiftAssignment]
    violations: List[RuleViolation]
    warnings: List[str]
    
    # Metrics
    total_shifts_optimized: int = 0
    employees_assigned: int = 0
    overtime_hours_added: float = 0.0
    preference_score: float = 0.0
    
    # AI explainability
    strategy_used: OptimizationStrategy = OptimizationStrategy.BALANCED
    optimization_time_ms: int = 0
    ai_confidence: Optional[float] = None
    explanation: Optional[str] = None
    
    # For scenario simulation
    scenario_id: Optional[str] = None
    is_simulation: bool = False


@dataclass
class EmployeeScore:
    """Scoring data for employee-shift matching"""
    employee: EmployeeEntity
    base_score: float
    availability_score: float
    preference_score: float
    workload_balance_score: float
    skill_match_score: float
    final_score: float
    violations: List[RuleViolation]
    explanation: str


class ShiftOptimizationService:
    """
    Central service for shift optimization.
    Combines rule-based validation with AI-powered optimization.
    """
    
    def __init__(self, rule_engine: RuleEngine, ai_service=None):
        self.rule_engine = rule_engine
        self.ai_service = ai_service  # Optional AI service injection
    
    def optimize_shifts(
        self,
        shifts_to_fill: List[ShiftEntity],
        available_employees: List[EmployeeEntity],
        existing_shifts: List[ShiftEntity],
        constraints: OptimizationConstraints,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ) -> OptimizationResult:
        """
        Main optimization entry point.
        Returns optimal assignments respecting all rules and constraints.
        """
        start_time = datetime.now()
        
        assignments = []
        all_violations = []
        warnings = []
        total_overtime = 0.0
        total_preference_score = 0.0
        
        for shift in shifts_to_fill:
            # Score all employees for this shift
            scored_employees = self._score_employees_for_shift(
                shift, available_employees, existing_shifts, constraints, strategy
            )
            
            # Filter out employees with blocking violations
            valid_candidates = [
                s for s in scored_employees 
                if not self.rule_engine.has_blocking_violations(s.violations)
            ]
            
            if not valid_candidates:
                warnings.append(f"No valid candidates for shift {shift.id} at {shift.start_time}")
                all_violations.extend(scored_employees[0].violations if scored_employees else [])
                continue
            
            # Select best candidate
            best = max(valid_candidates, key=lambda s: s.final_score)
            
            # Create assignment
            assignment = ShiftAssignment(
                employee_id=best.employee.id,
                shift_id=shift.id,
                assigned_at=datetime.now(),
                assigned_by=0,  # System assignment
                assignment_reason=AssignmentSource.AI_OPTIMIZED.value if self.ai_service else AssignmentSource.RULE_BASED.value,
                confidence_score=best.final_score,
                explanation=best.explanation
            )
            
            assignments.append(assignment)
            all_violations.extend(best.violations)
            total_preference_score += best.preference_score
            
            # Track overtime
            if best.employee.is_in_overtime:
                total_overtime += shift.duration_hours
            
            # Update employee state for next iteration
            best.employee.total_hours_this_week += shift.duration_hours
        
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return OptimizationResult(
            success=len(assignments) == len(shifts_to_fill),
            assignments=assignments,
            violations=all_violations,
            warnings=warnings,
            total_shifts_optimized=len(assignments),
            employees_assigned=len(set(a.employee_id for a in assignments)),
            overtime_hours_added=total_overtime,
            preference_score=total_preference_score / len(assignments) if assignments else 0,
            strategy_used=strategy,
            optimization_time_ms=elapsed_ms,
            explanation=self._generate_optimization_explanation(assignments, strategy)
        )
    
    def _score_employees_for_shift(
        self,
        shift: ShiftEntity,
        employees: List[EmployeeEntity],
        existing_shifts: List[ShiftEntity],
        constraints: OptimizationConstraints,
        strategy: OptimizationStrategy
    ) -> List[EmployeeScore]:
        """Score all employees for a specific shift"""
        scores = []
        
        for employee in employees:
            # Skip excluded employees
            if employee.id in constraints.exclude_employees:
                continue
            
            # Run rule validation
            violations = self.rule_engine.evaluate_shift(
                shift, employee, existing_shifts
            )
            
            # Calculate component scores
            availability = self._calculate_availability_score(shift, employee)
            preference = employee.calculate_preference_score(
                shift.start_time.weekday(),
                self._get_shift_type(shift)
            ) if constraints.respect_preferences else 0.5
            workload = self._calculate_workload_balance_score(employee, shift)
            skill = self._calculate_skill_match_score(employee, constraints.required_skills)
            
            # Apply strategy weights
            weights = self._get_strategy_weights(strategy)
            final_score = (
                availability * weights["availability"] +
                preference * weights["preference"] +
                workload * weights["workload"] +
                skill * weights["skill"]
            )
            
            # Penalty for violations
            warning_count = sum(1 for v in violations if v.severity == RuleSeverity.WARNING)
            final_score -= warning_count * 0.05
            
            # Bonus for force-included employees
            if employee.id in constraints.force_include_employees:
                final_score += 0.5
            
            explanation = self._generate_employee_explanation(
                employee, shift, availability, preference, workload, skill, final_score
            )
            
            scores.append(EmployeeScore(
                employee=employee,
                base_score=1.0,
                availability_score=availability,
                preference_score=preference,
                workload_balance_score=workload,
                skill_match_score=skill,
                final_score=final_score,
                violations=violations,
                explanation=explanation
            ))
        
        return sorted(scores, key=lambda s: s.final_score, reverse=True)
    
    def _calculate_availability_score(self, shift: ShiftEntity, employee: EmployeeEntity) -> float:
        """Calculate how well employee availability matches shift"""
        if not employee.is_active or employee.is_on_leave:
            return 0.0
        
        day = shift.start_time.weekday()
        shift_time = shift.start_time.time()
        
        if employee.is_available_at(day, shift_time):
            return 1.0
        return 0.2  # Low score if not in preferred availability
    
    def _calculate_workload_balance_score(self, employee: EmployeeEntity, shift: ShiftEntity) -> float:
        """
        Calculate workload balance score.
        Higher scores for employees with fewer hours (balancing).
        """
        max_hours = employee.weekly_working_limit + employee.overtime_limit
        current_utilization = employee.total_hours_this_week / max_hours
        
        # Inverse - prefer less utilized employees
        return 1.0 - current_utilization
    
    def _calculate_skill_match_score(self, employee: EmployeeEntity, required_skills: List[str]) -> float:
        """Calculate skill match score"""
        if not required_skills:
            return 1.0
        
        matches = sum(1 for skill in required_skills if employee.has_skill(skill))
        return matches / len(required_skills)
    
    def _get_shift_type(self, shift: ShiftEntity) -> str:
        """Determine shift type based on start time"""
        hour = shift.start_time.hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _get_strategy_weights(self, strategy: OptimizationStrategy) -> Dict[str, float]:
        """Get scoring weights based on strategy"""
        weights = {
            OptimizationStrategy.BALANCED: {
                "availability": 0.3, "preference": 0.25, "workload": 0.25, "skill": 0.2
            },
            OptimizationStrategy.MINIMIZE_OVERTIME: {
                "availability": 0.2, "preference": 0.1, "workload": 0.5, "skill": 0.2
            },
            OptimizationStrategy.MAXIMIZE_PREFERENCES: {
                "availability": 0.2, "preference": 0.5, "workload": 0.15, "skill": 0.15
            },
            OptimizationStrategy.EMERGENCY: {
                "availability": 0.6, "preference": 0.05, "workload": 0.15, "skill": 0.2
            },
            OptimizationStrategy.COST_EFFECTIVE: {
                "availability": 0.25, "preference": 0.1, "workload": 0.45, "skill": 0.2
            },
        }
        return weights.get(strategy, weights[OptimizationStrategy.BALANCED])
    
    def _generate_employee_explanation(
        self, employee: EmployeeEntity, shift: ShiftEntity,
        availability: float, preference: float, workload: float, skill: float, final: float
    ) -> str:
        """Generate human-readable explanation for employee score"""
        parts = []
        
        if availability >= 0.8:
            parts.append("Employee is available during shift hours")
        
        if preference >= 0.7:
            parts.append("Shift matches employee preferences")
        
        if workload >= 0.6:
            parts.append("Employee has balanced workload this week")
        elif workload < 0.3:
            parts.append("Employee is heavily utilized this week")
        
        if skill >= 0.8:
            parts.append("Employee has required skills")
        
        if not parts:
            parts.append("Standard assignment based on availability")
        
        return f"Score: {final:.2f}. " + "; ".join(parts)
    
    def _generate_optimization_explanation(
        self, assignments: List[ShiftAssignment], strategy: OptimizationStrategy
    ) -> str:
        """Generate explanation for overall optimization result"""
        return (
            f"Optimization completed using {strategy.value} strategy. "
            f"Assigned {len(assignments)} shifts to {len(set(a.employee_id for a in assignments))} employees."
        )
    
    # ============== Emergency & Rebalancing ==============
    
    def handle_emergency_absence(
        self,
        absent_employee_id: int,
        affected_shifts: List[ShiftEntity],
        available_employees: List[EmployeeEntity],
        existing_shifts: List[ShiftEntity]
    ) -> OptimizationResult:
        """
        Handle sudden employee absence (e.g., sick leave).
        Uses EMERGENCY strategy with relaxed constraints.
        """
        logger.warning(f"Emergency absence: Employee {absent_employee_id}, {len(affected_shifts)} shifts affected")
        
        # Filter out the absent employee
        available = [e for e in available_employees if e.id != absent_employee_id]
        
        # Use emergency strategy with relaxed constraints
        constraints = OptimizationConstraints(
            exclude_employees=[absent_employee_id],
            respect_preferences=False,  # Emergency overrides preferences
            allow_overtime=True,
            max_overtime_percentage=0.5  # Allow more overtime in emergency
        )
        
        return self.optimize_shifts(
            affected_shifts, available, existing_shifts,
            constraints, OptimizationStrategy.EMERGENCY
        )
    
    def rebalance_after_leave_approval(
        self,
        leave_employee_id: int,
        leave_start: date,
        leave_end: date,
        all_employees: List[EmployeeEntity],
        all_shifts: List[ShiftEntity]
    ) -> OptimizationResult:
        """
        Automatically rebalance shifts after leave is approved.
        Triggered by automation when leave status changes.
        """
        # Find shifts that need reassignment
        affected_shifts = [
            s for s in all_shifts
            if s.employee_id == leave_employee_id
            and leave_start <= s.start_time.date() <= leave_end
            and s.status == ShiftStatus.SCHEDULED
        ]
        
        if not affected_shifts:
            return OptimizationResult(
                success=True, assignments=[], violations=[], warnings=[],
                explanation="No shifts needed rebalancing"
            )
        
        # Get available employees (excluding the one on leave)
        available = [e for e in all_employees if e.id != leave_employee_id]
        existing = [s for s in all_shifts if s.employee_id != leave_employee_id]
        
        constraints = OptimizationConstraints(
            exclude_employees=[leave_employee_id],
            respect_preferences=True,
            allow_overtime=True
        )
        
        result = self.optimize_shifts(
            affected_shifts, available, existing,
            constraints, OptimizationStrategy.BALANCED
        )
        result.explanation = f"Rebalanced {len(affected_shifts)} shifts due to approved leave for employee {leave_employee_id}"
        
        return result
    
    # ============== Scenario Simulation ==============
    
    def simulate_scenario(
        self,
        scenario_name: str,
        hypothetical_changes: Dict[str, Any],
        current_shifts: List[ShiftEntity],
        current_employees: List[EmployeeEntity]
    ) -> OptimizationResult:
        """
        Run what-if scenario simulation without affecting real data.
        E.g., "What if employee X is absent?" or "What if demand increases 20%?"
        """
        import copy
        import uuid
        
        # Deep copy to avoid modifying original data
        simulated_shifts = copy.deepcopy(current_shifts)
        simulated_employees = copy.deepcopy(current_employees)
        
        # Apply hypothetical changes
        if "absent_employee_id" in hypothetical_changes:
            emp_id = hypothetical_changes["absent_employee_id"]
            for emp in simulated_employees:
                if emp.id == emp_id:
                    emp.is_on_leave = True
            shifts_to_fill = [s for s in simulated_shifts if s.employee_id == emp_id]
        
        elif "demand_increase_percent" in hypothetical_changes:
            increase = hypothetical_changes["demand_increase_percent"] / 100
            # Simulate by extending shift durations or adding shifts
            for shift in simulated_shifts:
                shift.end_time = shift.end_time + timedelta(hours=shift.duration_hours * increase)
            shifts_to_fill = simulated_shifts
        
        else:
            shifts_to_fill = simulated_shifts
        
        # Run optimization
        constraints = OptimizationConstraints(respect_preferences=True)
        result = self.optimize_shifts(
            shifts_to_fill,
            [e for e in simulated_employees if not e.is_on_leave],
            [], constraints, OptimizationStrategy.BALANCED
        )
        
        result.scenario_id = str(uuid.uuid4())
        result.is_simulation = True
        result.explanation = f"Simulation '{scenario_name}': {result.explanation}"
        
        return result
