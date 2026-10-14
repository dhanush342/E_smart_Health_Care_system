import numpy as np
import random
from typing import Tuple, Dict, Any, List, Optional
from rl_scheduler.data_types import PatientProfile

class DepartmentSlotSchedulingEnv:
    """
    Stage 2: Department Slot Scheduling Environment for Double DQN Agent.
    Optimizes the appointment book layout by assigning patients to time slots,
    factoring in priority levels, cancellation rates, and no-shows.
    """
    def __init__(self, num_slots: int = 12, max_patients_per_batch: int = 15):
        self.num_slots = num_slots
        self.max_patients_per_batch = max_patients_per_batch
        self.schedule: List[Optional[PatientProfile]] = [None] * num_slots
        self.patient_queue: List[PatientProfile] = []
        self.current_patient_idx = 0

    def reset(self, patients: Optional[List[PatientProfile]] = None) -> np.ndarray:
        self.schedule = [None] * self.num_slots
        self.current_patient_idx = 0
        if patients is not None:
            self.patient_queue = list(patients)
        else:
            self.patient_queue = []
            num_patients = random.randint(8, self.max_patients_per_batch)
            for i in range(num_patients):
                sev = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.1, 0.1])[0]
                canc_prob = random.uniform(0.02, 0.35)
                is_emerg = (sev >= 4) and (random.random() < 0.3)
                patient = PatientProfile(
                    patient_id=f"PAT_BOOK_{i}",
                    severity=sev,
                    condition="Scheduled Visit",
                    target_department=0,
                    base_consultation_time=15.0,
                    cancellation_prob=canc_prob,
                    is_emergency=is_emerg,
                    arrival_time=0.0
                )
                self.patient_queue.append(patient)

        return self._get_observation()

    def _get_observation(self) -> np.ndarray:
        # Observation format:
        # Current patient features: [severity/5, cancellation_prob, is_emergency] (3)
        # Slots status: [slot_occupied (0/1), slot_patient_severity/5, slot_cancellation_prob] * num_slots (3 * num_slots)
        obs = np.zeros(3 + 3 * self.num_slots, dtype=np.float32)
        if self.current_patient_idx < len(self.patient_queue):
            p = self.patient_queue[self.current_patient_idx]
            obs[0] = p.severity / 5.0
            obs[1] = p.cancellation_prob
            obs[2] = 1.0 if p.is_emergency else 0.0

        for slot_idx in range(self.num_slots):
            base_idx = 3 + slot_idx * 3
            slot_patient = self.schedule[slot_idx]
            if slot_patient is not None:
                obs[base_idx] = 1.0
                obs[base_idx + 1] = slot_patient.severity / 5.0
                obs[base_idx + 2] = slot_patient.cancellation_prob
        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        action: slot index (0 to num_slots - 1) or action == num_slots (skip / reject / defer)
        """
        done = False
        reward = 0.0

        if self.current_patient_idx >= len(self.patient_queue):
            done = True
            return self._get_observation(), 0.0, done, {}

        patient = self.patient_queue[self.current_patient_idx]

        if action == self.num_slots:
            # Action to skip/defer patient
            if patient.severity >= 4:
                reward -= 15.0  # Heavy penalty for skipping high severity
            else:
                reward -= 2.0
        elif 0 <= action < self.num_slots:
            if self.schedule[action] is None:
                self.schedule[action] = patient
                patient.scheduled_slot = action
                patient.status = "scheduled"

                # Reward calculation:
                # 1. Base scheduling reward
                reward += 10.0

                # 2. Early slot preference for high severity
                earliness_bonus = (self.num_slots - action) * (patient.severity / 5.0) * 2.0
                reward += earliness_bonus

                # 3. Penalty if placing high cancellation risk in prime early slots
                if action < 3 and patient.cancellation_prob > 0.2:
                    reward -= 5.0
            else:
                # Slot already occupied! Overwrite penalty or rejection penalty
                reward -= 20.0

        self.current_patient_idx += 1
        if self.current_patient_idx >= len(self.patient_queue):
            done = True

        next_obs = self._get_observation()
        info = {
            "current_patient_idx": self.current_patient_idx,
            "scheduled_slots_count": sum(1 for s in self.schedule if s is not None)
        }
        return next_obs, reward, done, info
