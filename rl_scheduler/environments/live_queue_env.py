import numpy as np
import random
from typing import Tuple, Dict, Any, List, Optional
from rl_scheduler.data_types import PatientProfile

class LiveQueueExecutionEnv:
    """
    Stage 3: Live Queue Execution Environment for PPO Agent.
    Runs real-time minute-by-minute waiting room execution.
    Dynamically decides which patient from the waiting room to pull into the clinician's room next
    under variable consultation times, walk-in emergencies, and cancellations.
    """
    def __init__(self, num_doctors: int = 2, total_simulation_minutes: int = 120, max_queue_size: int = 10):
        self.num_doctors = num_doctors
        self.total_simulation_minutes = total_simulation_minutes
        self.max_queue_size = max_queue_size
        self.current_time = 0.0  # in minutes

        self.doctor_busy_until = [0.0] * num_doctors
        self.waiting_queue: List[PatientProfile] = []
        self.completed_patients: List[PatientProfile] = []
        self.doctor_idle_time = 0.0

    def reset(self, initial_patients: Optional[List[PatientProfile]] = None) -> np.ndarray:
        self.current_time = 0.0
        self.doctor_busy_until = [0.0] * self.num_doctors
        self.waiting_queue = []
        self.completed_patients = []
        self.doctor_idle_time = 0.0

        if initial_patients is not None:
            self.waiting_queue = list(initial_patients)
            for p in self.waiting_queue:
                p.status = "waiting"
        else:
            # Generate starting queue
            num_initial = random.randint(3, 7)
            for i in range(num_initial):
                sev = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.1, 0.1])[0]
                base_time = max(5.0, random.gauss(15.0, 4.0))
                self.waiting_queue.append(PatientProfile(
                    patient_id=f"PAT_LIVE_{i}",
                    severity=sev,
                    condition="Live Visit",
                    target_department=0,
                    base_consultation_time=base_time,
                    cancellation_prob=0.05,
                    is_emergency=(sev >= 4) and (random.random() < 0.2),
                    arrival_time=0.0
                ))
        return self._get_observation()

    def _get_observation(self) -> np.ndarray:
        # State vector:
        # [current_time / total_simulation_minutes, free_doctors_ratio] (2)
        # Top max_queue_size patients features: [severity/5, wait_time/60, is_emergency] * max_queue_size (3 * max_queue_size)
        free_doctors = sum(1 for b in self.doctor_busy_until if b <= self.current_time)
        obs = np.zeros(2 + 3 * self.max_queue_size, dtype=np.float32)
        obs[0] = self.current_time / float(self.total_simulation_minutes)
        obs[1] = free_doctors / float(self.num_doctors)

        for i in range(min(len(self.waiting_queue), self.max_queue_size)):
            p = self.waiting_queue[i]
            base_idx = 2 + i * 3
            obs[base_idx] = p.severity / 5.0
            wait_time = self.current_time - p.arrival_time
            obs[base_idx + 1] = min(wait_time / 60.0, 2.0)
            obs[base_idx + 2] = 1.0 if p.is_emergency else 0.0

        return obs

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        action: index in waiting queue (0 to max_queue_size - 1) to call into an available doctor's room.
        action == max_queue_size: NO-OP / wait for current consultations to progress.
        """
        reward = 0.0

        # Check if any doctor is free
        free_doc_indices = [i for i, b in enumerate(self.doctor_busy_until) if b <= self.current_time]

        # Stochastic event: Walk-in emergency arrival probability (10% chance per minute)
        if random.random() < 0.10 and len(self.waiting_queue) < self.max_queue_size * 2:
            walkin = PatientProfile(
                patient_id=f"PAT_WALKIN_{int(self.current_time)}",
                severity=random.choice([4, 5]),
                condition="Emergency Walk-in",
                target_department=0,
                base_consultation_time=random.uniform(15.0, 30.0),
                cancellation_prob=0.01,
                is_emergency=True,
                arrival_time=self.current_time
            )
            # Insert walk-in emergency into queue
            self.waiting_queue.append(walkin)

        if free_doc_indices and action < len(self.waiting_queue) and action < self.max_queue_size:
            doc_idx = free_doc_indices[0]
            patient = self.waiting_queue.pop(action)

            # Check for cancellation / no-show on call
            if random.random() < patient.cancellation_prob:
                patient.status = "cancelled"
                reward -= 1.0  # Minor slot wastage penalty
            else:
                # Consultation occurs
                patient.start_service_time = self.current_time
                patient.status = "in_consultation"

                # Variable consultation duration (Gaussian variability around base duration)
                actual_duration = max(5.0, random.gauss(patient.base_consultation_time, 3.0))
                patient.actual_consultation_time = actual_duration
                patient.completion_time = self.current_time + actual_duration

                self.doctor_busy_until[doc_idx] = patient.completion_time
                self.completed_patients.append(patient)

                # Reward calculation:
                # Completion reward proportional to severity
                reward += 10.0 * patient.severity

                # Penalty for wait time (weighted heavily for severe cases)
                wait_time = patient.calculate_wait_time()
                wait_penalty = (wait_time / 10.0) * (patient.severity / 2.0)
                reward -= wait_penalty

                # Bonus for immediate emergency handling
                if patient.is_emergency and wait_time < 10.0:
                    reward += 15.0
        else:
            # Action was NO-OP or invalid queue index selected
            if free_doc_indices and len(self.waiting_queue) > 0:
                # Doctor was idle while patients were waiting!
                reward -= 5.0
                self.doctor_idle_time += 1.0

        # Advance simulation time by 1 minute
        self.current_time += 1.0

        # Accumulate waiting time penalties for remaining queue
        for p in self.waiting_queue:
            if p.is_emergency:
                reward -= 0.5  # Heavy urgency penalty per minute
            else:
                reward -= 0.05 * (p.severity / 5.0)

        done = self.current_time >= self.total_simulation_minutes
        next_obs = self._get_observation()

        info = {
            "current_time": self.current_time,
            "completed_count": len(self.completed_patients),
            "waiting_count": len(self.waiting_queue),
            "doctor_idle_time": self.doctor_idle_time
        }
        return next_obs, reward, done, info
