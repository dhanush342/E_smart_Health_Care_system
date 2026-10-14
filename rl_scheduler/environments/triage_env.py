import numpy as np
import random
from typing import Tuple, Dict, Any, List, Optional
from rl_scheduler.data_types import PatientProfile, ClinicDepartmentInfo

DEPARTMENT_NAMES = [
    "General Medicine",
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "Pediatrics"
]

class TriageAllocationEnv:
    """
    Stage 1: Triage Allocation Environment for DQN Agent.
    Routes incoming patient profiles to suitable clinic departments considering severity
    and department backlogs.
    """
    def __init__(self, num_departments: int = 5, max_steps: int = 100):
        self.num_departments = num_departments
        self.max_steps = max_steps
        self.current_step = 0
        self.departments = [
            ClinicDepartmentInfo(dept_id=i, name=DEPARTMENT_NAMES[i], num_doctors=2, queue_backlog=0)
            for i in range(num_departments)
        ]
        self.current_patient: Optional[PatientProfile] = None

    def _generate_patient(self) -> PatientProfile:
        severity = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.1, 0.1])[0]
        primary_dept = random.randint(0, self.num_departments - 1)
        base_time = random.uniform(10.0, 25.0)
        cancellation_prob = random.uniform(0.05, 0.25)
        is_emergency = (severity >= 4) and (random.random() < 0.4)

        return PatientProfile(
            patient_id=f"PAT_{random.randint(1000, 9999)}",
            severity=severity,
            condition=f"Condition_Dept_{primary_dept}",
            target_department=primary_dept,
            base_consultation_time=base_time,
            cancellation_prob=cancellation_prob,
            is_emergency=is_emergency,
            arrival_time=0.0
        )

    def reset(self) -> np.ndarray:
        self.current_step = 0
        for dept in self.departments:
            dept.queue_backlog = random.randint(0, 5)
        self.current_patient = self._generate_patient()
        return self._get_observation()

    def _get_observation(self) -> np.ndarray:
        obs = np.zeros(1 + 5 + 1 + self.num_departments, dtype=np.float32)
        if self.current_patient:
            obs[0] = self.current_patient.severity / 5.0
            obs[1 + self.current_patient.target_department] = 1.0
            obs[6] = 1.0 if self.current_patient.is_emergency else 0.0

        for i, dept in enumerate(self.departments):
            obs[7 + i] = min(dept.queue_backlog / 20.0, 1.0)

        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        assert 0 <= action < self.num_departments, f"Invalid action {action}"

        reward = 0.0
        patient = self.current_patient
        chosen_dept = self.departments[action]

        if action == patient.target_department:
            reward += 10.0
        else:
            if action == 0:
                reward += 2.0
            else:
                reward -= 15.0

        backlog_penalty = chosen_dept.queue_backlog * 0.5
        reward -= backlog_penalty

        if patient.severity >= 4:
            if chosen_dept.queue_backlog < 3:
                reward += 10.0
            else:
                reward -= 10.0

        chosen_dept.queue_backlog += 1

        for dept in self.departments:
            if dept.queue_backlog > 0 and random.random() < 0.3:
                dept.queue_backlog -= 1

        self.current_step += 1
        done = self.current_step >= self.max_steps

        self.current_patient = self._generate_patient() if not done else None
        next_obs = self._get_observation()

        info = {
            "assigned_dept": action,
            "target_dept": patient.target_department,
            "severity": patient.severity if patient else 0,
            "is_emergency": patient.is_emergency if patient else False
        }

        return next_obs, reward, done, info
