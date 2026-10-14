import numpy as np
import random
from typing import List, Dict, Any, Tuple
from rl_scheduler.data_types import PatientProfile, SimulationMetrics
from rl_scheduler.environments.triage_env import TriageAllocationEnv
from rl_scheduler.environments.slot_scheduling_env import DepartmentSlotSchedulingEnv
from rl_scheduler.environments.live_queue_env import LiveQueueExecutionEnv
from rl_scheduler.agents.dqn_agent import DQNAgent
from rl_scheduler.agents.double_dqn_agent import DoubleDQNAgent
from rl_scheduler.agents.ppo_agent import PPOAgent
from rl_scheduler.baselines.baseline_schedulers import FCFSScheduler, FixedSlotScheduler, HeuristicPriorityScheduler

class MultiStageRLSchedulerPipeline:
    """
    Multi-Stage Reinforcement Learning Scheduling Pipeline.
    Stage 1: Triage Allocation (DQN)
    Stage 2: Department Slot Scheduling (Double DQN)
    Stage 3: Live Queue Execution (PPO)
    """
    def __init__(self, num_departments: int = 5, num_doctors: int = 2, num_slots: int = 12):
        self.num_departments = num_departments
        self.num_doctors = num_doctors
        self.num_slots = num_slots

        # Initialize environments
        self.triage_env = TriageAllocationEnv(num_departments=num_departments)
        self.slot_env = DepartmentSlotSchedulingEnv(num_slots=num_slots)
        self.live_env = LiveQueueExecutionEnv(num_doctors=num_doctors)

        # Initialize agents
        # Triage DQN: obs dim = 1 + 5 + 1 + 5 = 12, actions = num_departments (5)
        self.triage_agent = DQNAgent(state_dim=12, action_dim=num_departments)
        # Slot Double DQN: obs dim = 3 + 3 * 12 = 39, actions = num_slots + 1 (13)
        self.slot_agent = DoubleDQNAgent(state_dim=39, action_dim=num_slots + 1)
        # Live Queue PPO: obs dim = 2 + 3 * 10 = 32, actions = max_queue_size + 1 (11)
        self.ppo_agent = PPOAgent(state_dim=32, action_dim=11)

    def train_agents(self, num_episodes: int = 50) -> Dict[str, List[float]]:
        """
        Trains all 3 agents across synthetic episodes.
        """
        history = {"triage_rewards": [], "slot_rewards": [], "ppo_rewards": []}

        # 1. Train Triage Agent (DQN)
        for ep in range(num_episodes):
            state = self.triage_env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = self.triage_agent.select_action(state)
                next_state, reward, done, _ = self.triage_env.step(action)
                self.triage_agent.store_transition(state, action, reward, next_state, done)
                self.triage_agent.update()
                state = next_state
                ep_reward += reward
            if ep % 5 == 0:
                self.triage_agent.update_target_network()
            history["triage_rewards"].append(ep_reward)

        # 2. Train Slot Scheduling Agent (Double DQN)
        for ep in range(num_episodes):
            state = self.slot_env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = self.slot_agent.select_action(state)
                next_state, reward, done, _ = self.slot_env.step(action)
                self.slot_agent.store_transition(state, action, reward, next_state, done)
                self.slot_agent.update()
                state = next_state
                ep_reward += reward
            if ep % 5 == 0:
                self.slot_agent.update_target_network()
            history["slot_rewards"].append(ep_reward)

        # 3. Train Live Queue Agent (PPO)
        for ep in range(num_episodes):
            state = self.live_env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action, logprob = self.ppo_agent.select_action(state)
                next_state, reward, done, _ = self.live_env.step(action)
                self.ppo_agent.store_transition(state, action, logprob, reward, done)
                state = next_state
                ep_reward += reward
            self.ppo_agent.update()
            history["ppo_rewards"].append(ep_reward)

        return history

    def run_multi_stage_execution(self, incoming_patients: List[PatientProfile]) -> Tuple[SimulationMetrics, List[PatientProfile]]:
        """
        Runs full end-to-end pipeline on input patients:
        Stage 1 (Triage) -> Stage 2 (Slot Scheduling) -> Stage 3 (Live Queue Execution)
        """
        # --- Stage 1: Triage Allocation ---
        triaged_patients_by_dept: Dict[int, List[PatientProfile]] = {i: [] for i in range(self.num_departments)}
        triage_env = TriageAllocationEnv(num_departments=self.num_departments)

        for patient in incoming_patients:
            triage_env.current_patient = patient
            obs = triage_env._get_observation()
            dept_action = self.triage_agent.select_action(obs, evaluate=True)
            patient.target_department = dept_action
            triaged_patients_by_dept[dept_action].append(patient)

        # --- Stage 2: Department Slot Scheduling ---
        # Focus on target department 0 for live simulation
        dept_patients = triaged_patients_by_dept.get(0, incoming_patients)
        slot_env = DepartmentSlotSchedulingEnv(num_slots=self.num_slots)
        slot_obs = slot_env.reset(patients=dept_patients)

        scheduled_patients = []
        done = False
        while not done:
            action = self.slot_agent.select_action(slot_obs, evaluate=True)
            slot_obs, reward, done, info = slot_env.step(action)

        for s in slot_env.schedule:
            if s is not None:
                scheduled_patients.append(s)

        # Add unscheduled/overflow patients to waiting queue as well
        unscheduled = [p for p in dept_patients if p.status != "scheduled"]
        queue_patients = scheduled_patients + unscheduled

        # --- Stage 3: Live Queue Execution ---
        live_env = LiveQueueExecutionEnv(num_doctors=self.num_doctors, total_simulation_minutes=120)
        live_obs = live_env.reset(initial_patients=queue_patients)

        done = False
        while not done:
            action, _ = self.ppo_agent.select_action(live_obs, evaluate=True)
            live_obs, reward, done, info = live_env.step(action)

        # Compute final pipeline metrics
        completed = live_env.completed_patients
        cancelled = [p for p in queue_patients if p.status == "cancelled"]

        fcfs_helper = FCFSScheduler()
        metrics = fcfs_helper._compute_metrics(
            queue_patients,
            completed,
            cancelled,
            live_env.doctor_idle_time,
            120.0
        )
        return metrics, completed


def generate_demand_scenario(demand_level: str = "medium", count: int = 15) -> List[PatientProfile]:
    """
    Generates synthetic patient workloads for low, medium, and high/surge demand.
    """
    patients = []
    if demand_level == "low":
        weights = [0.4, 0.4, 0.15, 0.04, 0.01]
    elif demand_level == "high":
        weights = [0.1, 0.2, 0.3, 0.25, 0.15]
    else:  # medium
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]

    for i in range(count):
        sev = random.choices([1, 2, 3, 4, 5], weights=weights)[0]
        c_prob = random.uniform(0.02, 0.30) if sev < 4 else random.uniform(0.01, 0.10)
        is_emerg = (sev >= 4) and (random.random() < 0.4)
        arrival = random.uniform(0.0, 60.0)

        patients.append(PatientProfile(
            patient_id=f"PAT_{demand_level.upper()}_{i}",
            severity=sev,
            condition="General Visit",
            target_department=random.randint(0, 4),
            base_consultation_time=random.uniform(10.0, 25.0),
            cancellation_prob=c_prob,
            is_emergency=is_emerg,
            arrival_time=arrival
        ))
    return patients


def run_comprehensive_benchmark(num_train_episodes: int = 30) -> Dict[str, Any]:
    """
    Runs training and compares Multi-Stage RL against FCFS, Fixed-Slot, and Heuristic Priority
    across Low, Medium, and High demand scenarios.
    """
    pipeline = MultiStageRLSchedulerPipeline()
    print("Training Multi-Stage RL Agents...")
    pipeline.train_agents(num_episodes=num_train_episodes)
    print("Training complete.")

    fcfs = FCFSScheduler()
    fixed_slot = FixedSlotScheduler()
    heuristic = HeuristicPriorityScheduler()

    scenarios = ["low", "medium", "high"]
    results = {}

    for sc in scenarios:
        count = 10 if sc == "low" else (18 if sc == "medium" else 28)
        patients = generate_demand_scenario(sc, count=count)

        # 1. Multi-Stage RL
        rl_metrics, _ = pipeline.run_multi_stage_execution([p for p in patients])

        # 2. FCFS Baseline
        fcfs_metrics = fcfs.run_simulation([p for p in patients])

        # 3. Fixed Slot Baseline
        fixed_metrics = fixed_slot.run_simulation([p for p in patients])

        # 4. Heuristic Priority Baseline
        heuristic_metrics = heuristic.run_simulation([p for p in patients])

        results[sc] = {
            "Multi-Stage RL": rl_metrics,
            "FCFS": fcfs_metrics,
            "Fixed-Slot": fixed_metrics,
            "Heuristic Priority": heuristic_metrics
        }

    return results
