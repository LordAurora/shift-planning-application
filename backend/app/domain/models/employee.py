"""
Pure domain entity for Employee - Framework agnostic business logic.
"""
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional, List, Dict


class SkillLevel(str, Enum):
    """Employee skill proficiency levels"""
    TRAINEE = "trainee"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"


@dataclass
class EmployeeAvailability:
    """Represents an employee's availability slot"""
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    is_preferred: bool = False  # Employee prefers this slot
    
    def contains_time(self, check_time: time) -> bool:
        """Check if a time falls within this availability window"""
        return self.start_time <= check_time <= self.end_time


@dataclass
class EmployeePreference:
    """Employee shift preferences for AI consideration"""
    preferred_shift_types: List[str] = field(default_factory=list)  # morning/afternoon/night
    preferred_days: List[int] = field(default_factory=list)  # 0-6
    avoid_days: List[int] = field(default_factory=list)
    max_consecutive_days: int = 5
    preferred_colleagues: List[int] = field(default_factory=list)  # employee_ids
    avoid_colleagues: List[int] = field(default_factory=list)
    preference_weight: float = 1.0  # How much to weight preferences (0-1)


@dataclass
class EmployeeSkill:
    """Skill possessed by an employee"""
    skill_name: str
    level: SkillLevel
    certified: bool = False
    certification_expiry: Optional[datetime] = None


@dataclass
class EmployeeEntity:
    """
    Pure domain model for an Employee.
    Contains business logic for workforce management.
    """
    id: Optional[int]
    name: str
    email: str
    role: str  # Job role (Developer, Support, etc.)
    department_id: int
    
    # Working limits
    weekly_working_limit: float = 40.0
    overtime_limit: float = 10.0
    
    # Availability and preferences
    availability: List[EmployeeAvailability] = field(default_factory=list)
    preferences: Optional[EmployeePreference] = None
    skills: List[EmployeeSkill] = field(default_factory=list)
    
    # Metrics
    total_hours_this_week: float = 0.0
    total_hours_this_month: float = 0.0
    consecutive_working_days: int = 0
    last_shift_end: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    is_on_leave: bool = False
    
    @property
    def remaining_weekly_hours(self) -> float:
        """Calculate remaining available hours for the week"""
        return max(0, self.weekly_working_limit - self.total_hours_this_week)
    
    @property
    def remaining_overtime_hours(self) -> float:
        """Calculate remaining overtime hours available"""
        regular_remaining = self.remaining_weekly_hours
        if regular_remaining > 0:
            return self.overtime_limit
        return max(0, self.overtime_limit - (self.total_hours_this_week - self.weekly_working_limit))
    
    @property
    def max_available_hours(self) -> float:
        """Total hours employee can still work this week"""
        return self.remaining_weekly_hours + self.remaining_overtime_hours
    
    @property
    def is_in_overtime(self) -> bool:
        """Check if employee is currently in overtime"""
        return self.total_hours_this_week > self.weekly_working_limit
    
    def is_available_at(self, day: int, check_time: time) -> bool:
        """Check if employee is available at a specific day and time"""
        if not self.is_active or self.is_on_leave:
            return False
        
        for slot in self.availability:
            if slot.day_of_week == day and slot.contains_time(check_time):
                return True
        return False
    
    def can_work_shift(self, shift_duration_hours: float) -> tuple[bool, str]:
        """
        Check if employee can work a shift of given duration.
        Returns (can_work, reason)
        """
        if not self.is_active:
            return False, "Employee is not active"
        
        if self.is_on_leave:
            return False, "Employee is on leave"
        
        if shift_duration_hours > self.max_available_hours:
            return False, f"Shift duration ({shift_duration_hours}h) exceeds remaining available hours ({self.max_available_hours}h)"
        
        if self.consecutive_working_days >= 6:
            return False, f"Employee has worked {self.consecutive_working_days} consecutive days (max 6)"
        
        return True, "OK"
    
    def has_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.TRAINEE) -> bool:
        """Check if employee has a skill at minimum required level"""
        level_order = [SkillLevel.TRAINEE, SkillLevel.JUNIOR, SkillLevel.MID, SkillLevel.SENIOR, SkillLevel.EXPERT]
        min_index = level_order.index(min_level)
        
        for skill in self.skills:
            if skill.skill_name == skill_name:
                skill_index = level_order.index(skill.level)
                return skill_index >= min_index
        return False
    
    def calculate_preference_score(self, day: int, shift_type: str) -> float:
        """
        Calculate how well a shift matches employee preferences.
        Returns score from 0.0 (poor match) to 1.0 (perfect match)
        """
        if not self.preferences:
            return 0.5  # Neutral score
        
        score = 0.5
        
        # Day preference
        if day in self.preferences.preferred_days:
            score += 0.2
        elif day in self.preferences.avoid_days:
            score -= 0.3
        
        # Shift type preference
        if shift_type in self.preferences.preferred_shift_types:
            score += 0.2
        
        # Availability preference bonus
        for slot in self.availability:
            if slot.day_of_week == day and slot.is_preferred:
                score += 0.1
                break
        
        return max(0.0, min(1.0, score)) * self.preferences.preference_weight
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department_id": self.department_id,
            "weekly_working_limit": self.weekly_working_limit,
            "overtime_limit": self.overtime_limit,
            "remaining_weekly_hours": self.remaining_weekly_hours,
            "is_in_overtime": self.is_in_overtime,
            "is_active": self.is_active,
            "is_on_leave": self.is_on_leave,
        }
