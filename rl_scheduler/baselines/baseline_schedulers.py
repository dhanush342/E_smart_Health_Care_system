import random
import numpy as np
from typing import List, Dict, Any
from rl_scheduler.data_types import PatientProfile, SimulationMetrics

class FCFSScheduler:
    """
    First-Come-First-Served (FCFS) Baseline.
    Processes patients strictly in the chronological order of their arrival, ignoring severity or cancellations.
    """
    def run_simulation(self, patients: List[PatientProfile], num_doctors: int = 2, total_minutes: int = 120) -> SimulationMetrics:
        queue = sorted(list(patients), key=lambda x: x.arrival_time)
        doctor_free_at = [0.0] * num_doctors
        completed = []
        cancelled = []
        total_idle_time = 0.0

        current_time = 0.0
        while current_time < total_minutes and queue:
            # Check for free doctor
            free_docs = [i for i, t in enumerate(doctor_free_at) if t <= current_time]
            if free_docs and queue:
                doc_idx = free_docs[0]
                patient = queue.pop(0)

                # Check cancellation
                if random.random() < patient.cancellation_prob:
                    patient.status = "cancelled"
                    cancelled.append(patient)
                else:
                    patient.start_service_time = current_time
                    patient.status = "completed"
                    dur = max(5.0, random.gauss(patient.base_consultation_time, 3.0))
                    patient.actual_consultation_time = dur
                    patient.completion_time = current_time + dur
                    doctor_free_at[doc_idx] = patient.completion_time
                    completed.append(patient)
            else:
                current_time += 1.0
                if any(t <= current_time for t in doctor_free_at) and not queue:
                    total_idle_time += 1.0

        return self._compute_metrics(patients, completed, cancelled, total_idle_time, total_minutes)

    def _compute_metrics(self, all_p, completed, cancelled, idle_time, total_minutes) -> SimulationMetrics:
        metrics = SimulationMetrics()
        metrics.total_patients = len(all_p)
        metrics.completed_patients = len(completed)
        metrics.cancelled_patients = len(cancelled)
        metrics.doctor_idle_time = idle_time
        metrics.throughput = (len(completed) / float(total_minutes)) * 60.0

        if completed:
            wait_times = [p.calculate_wait_time() for p in completed]
            metrics.avg_wait_time = float(np.mean(wait_times))

            # Avg wait by severity
            sev_waits = {}
            for sev in range(1, 6):
                p_sev = [p.calculate_wait_time() for p in completed if p.severity == sev]
                if p_sev:
                    sev_waits[sev] = float(np.mean(p_sev))
            metrics.avg_wait_time_by_severity = sev_waits

            # Priority fairness score (Ratio of high severity wait to low severity wait)
            high_sev_wait = np.mean([p.calculate_wait_time() for p in completed if p.severity >= 4]) if any(p.severity >= 4 for p in completed) else metrics.avg_wait_time
            low_sev_wait = np.mean([p.calculate_wait_time() for p in completed if p.severity <= 2]) if any(p.severity <= 2 for p in completed) else metrics.avg_wait_time

            # Fairness score: higher is fairer (low emergency wait vs general wait)
            if high_sev_wait > 0:
                metrics.priority_fairness_score = float(low_sev_wait / high_sev_wait)
            else:
                metrics.priority_fairness_score = 10.0

        return metrics


class FixedSlotScheduler:
    """
    Fixed-Slot Baseline.
    Assigns static, fixed time slots of equal duration (e.g. 15 mins) regardless of patient needs.
    """
    def run_simulation(self, patients: List[PatientProfile], num_doctors: int = 2, total_minutes: int = 120, slot_duration: int = 15) -> SimulationMetrics:
        num_slots = total_minutes // slot_duration
        completed = []
        cancelled = []
        total_idle_time = 0.0

        patient_idx = 0
        for slot in range(num_slots):
            slot_start = slot * slot_duration
            for doc in range(num_doctors):
                if patient_idx < len(patients):
                    patient = patients[patient_idx]
                    patient_idx += 1

                    if random.random() < patient.cancellation_prob:
                        patient.status = "cancelled"
                        cancelled.append(patient)
                    else:
                        patient.start_service_time = float(slot_start)
                        dur = max(5.0, random.gauss(patient.base_consultation_time, 3.0))
                        patient.actual_consultation_time = dur
                        patient.completion_time = slot_start + dur
                        patient.status = "completed"
                        completed.append(patient)

                        if dur < slot_duration:
                            total_idle_time += (slot_duration - dur)
                else:
                    total_idle_time += slot_duration

        fcfs = FCFSScheduler()
        return fcfs._compute_metrics(patients, completed, cancelled, total_idle_time, total_minutes)


class HeuristicPriorityScheduler:
    """
    Heuristic Priority Baseline.
    Uses rule-based ordering: strictly sorts queue by Severity (highest first) and then Arrival Time.
    """
    def run_simulation(self, patients: List[PatientProfile], num_doctors: int = 2, total_minutes: int = 120) -> SimulationMetrics:
        # Sort by severity descending, then arrival time ascending
        queue = sorted(list(patients), key=lambda x: (-x.severity, x.arrival_time))
        doctor_free_at = [0.0] * num_doctors
        completed = []
        cancelled = []
        total_idle_time = 0.0

        current_time = 0.0
        while current_time < total_minutes and queue:
            free_docs = [i for i, t in enumerate(doctor_free_at) if t <= current_time]
            if free_docs and queue:
                doc_idx = free_docs[0]
                # Pick highest severity available patient
                patient = queue.pop(0)

                if random.random() < patient.cancellation_prob:
                    patient.status = "cancelled"
                    cancelled.append(patient)
                else:
                    patient.start_service_time = current_time
                    patient.status = "completed"
                    dur = max(5.0, random.gauss(patient.base_consultation_time, 3.0))
                    patient.actual_consultation_time = dur
                    patient.completion_time = current_time + dur
                    doctor_free_at[doc_idx] = patient.completion_time
                    completed.append(patient)
            else:
                current_time += 1.0
                if any(t <= current_time for t in doctor_free_at) and not queue:
                    total_idle_time += 1.0

        fcfs = FCFSScheduler()
        return fcfs._compute_metrics(patients, completed, cancelled, total_idle_time, total_minutes)
