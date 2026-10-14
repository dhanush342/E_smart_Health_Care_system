import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class PatientProfile:
    patient_id: str
    severity: int  # 1 (lowest) to 5 (highest/emergency)
    condition: str
    target_department: int  # 0 to NUM_DEPARTMENTS-1
    base_consultation_time: float  # in minutes
    actual_consultation_time: float = 0.0
    cancellation_prob: float = 0.1
    noshow_prob: float = 0.05
    is_emergency: bool = False
    arrival_time: float = 0.0  # minute of arrival
    scheduled_slot: Optional[int] = None
    start_service_time: Optional[float] = None
    completion_time: Optional[float] = None
    status: str = "waiting"  # "waiting", "scheduled", "in_consultation", "completed", "cancelled", "noshow"

    def calculate_wait_time(self) -> float:
        if self.start_service_time is not None:
            return max(0.0, self.start_service_time - self.arrival_time)
        return 0.0

@dataclass
class ClinicDepartmentInfo:
    dept_id: int
    name: str
    num_doctors: int
    queue_backlog: int = 0
    capacity: int = 50

@dataclass
class SimulationMetrics:
    total_patients: int = 0
    completed_patients: int = 0
    cancelled_patients: int = 0
    noshow_patients: int = 0
    avg_wait_time: float = 0.0
    avg_wait_time_by_severity: Dict[int, float] = field(default_factory=dict)
    doctor_idle_time: float = 0.0
    priority_fairness_score: float = 0.0  # Measured via severity-weighted delay index or Jain's index
    throughput: float = 0.0  # Patients completed per hour
