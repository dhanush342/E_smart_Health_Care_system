import unittest
import json
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse

from rl_scheduler.data_types import PatientProfile, ClinicDepartmentInfo, SimulationMetrics
from rl_scheduler.environments.triage_env import TriageAllocationEnv
from rl_scheduler.environments.slot_scheduling_env import DepartmentSlotSchedulingEnv
from rl_scheduler.environments.live_queue_env import LiveQueueExecutionEnv

from rl_scheduler.agents.dqn_agent import DQNAgent
from rl_scheduler.agents.double_dqn_agent import DoubleDQNAgent
from rl_scheduler.agents.ppo_agent import PPOAgent

from rl_scheduler.baselines.baseline_schedulers import FCFSScheduler, FixedSlotScheduler, HeuristicPriorityScheduler
from rl_scheduler.pipeline import MultiStageRLSchedulerPipeline, run_comprehensive_benchmark

class TestRLSchedulerCore(unittest.TestCase):
    def test_triage_env_and_dqn(self):
        env = TriageAllocationEnv(num_departments=5)
        obs = env.reset()
        self.assertEqual(len(obs), 12)

        agent = DQNAgent(state_dim=12, action_dim=5)
        action = agent.select_action(obs)
        self.assertTrue(0 <= action < 5)

        next_obs, reward, done, info = env.step(action)
        self.assertEqual(len(next_obs), 12)
        agent.store_transition(obs, action, reward, next_obs, done)
        loss = agent.update()
        self.assertIsInstance(loss, float)

    def test_slot_scheduling_env_and_double_dqn(self):
        env = DepartmentSlotSchedulingEnv(num_slots=12)
        obs = env.reset()
        self.assertEqual(len(obs), 39)

        agent = DoubleDQNAgent(state_dim=39, action_dim=13)
        action = agent.select_action(obs)
        self.assertTrue(0 <= action <= 12)

        next_obs, reward, done, info = env.step(action)
        self.assertEqual(len(next_obs), 39)
        agent.store_transition(obs, action, reward, next_obs, done)
        loss = agent.update()
        self.assertIsInstance(loss, float)

    def test_live_queue_env_and_ppo(self):
        env = LiveQueueExecutionEnv(num_doctors=2, total_simulation_minutes=30)
        obs = env.reset()
        self.assertEqual(len(obs), 32)

        agent = PPOAgent(state_dim=32, action_dim=11)
        action, logprob = agent.select_action(obs)
        self.assertTrue(0 <= action <= 10)

        next_obs, reward, done, info = env.step(action)
        self.assertEqual(len(next_obs), 32)
        agent.store_transition(obs, action, logprob, reward, done)
        loss = agent.update()
        self.assertIsInstance(loss, float)

    def test_baseline_schedulers(self):
        patients = [
            PatientProfile("P1", severity=5, condition="Chest Pain", target_department=0, base_consultation_time=15.0, is_emergency=True),
            PatientProfile("P2", severity=1, condition="Checkup", target_department=0, base_consultation_time=10.0),
            PatientProfile("P3", severity=3, condition="Fever", target_department=0, base_consultation_time=20.0),
        ]

        fcfs = FCFSScheduler()
        m_fcfs = fcfs.run_simulation([p for p in patients], num_doctors=1, total_minutes=60)
        self.assertGreaterEqual(m_fcfs.completed_patients, 1)

        fixed = FixedSlotScheduler()
        m_fixed = fixed.run_simulation([p for p in patients], num_doctors=1, total_minutes=60)
        self.assertGreaterEqual(m_fixed.completed_patients, 1)

        heuristic = HeuristicPriorityScheduler()
        m_heuristic = heuristic.run_simulation([p for p in patients], num_doctors=1, total_minutes=60)
        self.assertGreaterEqual(m_heuristic.completed_patients, 1)

    def test_pipeline_and_benchmark(self):
        res = run_comprehensive_benchmark(num_train_episodes=2)
        self.assertIn("low", res)
        self.assertIn("medium", res)
        self.assertIn("high", res)
        for sc in ["low", "medium", "high"]:
            self.assertIn("Multi-Stage RL", res[sc])
            self.assertIn("FCFS", res[sc])
            self.assertIn("Fixed-Slot", res[sc])
            self.assertIn("Heuristic Priority", res[sc])


class TestAppointmentDjangoViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_rl_benchmark_endpoint(self):
        response = self.client.get('/appointment/benchmark/?episodes=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("benchmark_results", data)
        self.assertIn("medium", data["benchmark_results"])

    def test_rl_optimize_schedule_endpoint(self):
        payload = {
            "patients": [
                {
                    "patient_id": "P_TEST_1",
                    "severity": 5,
                    "condition": "Severe Shortness of Breath",
                    "target_department": 0,
                    "base_consultation_time": 20.0,
                    "cancellation_prob": 0.0,
                    "is_emergency": True,
                    "arrival_time": 0.0
                },
                {
                    "patient_id": "P_TEST_2",
                    "severity": 2,
                    "condition": "Routine Blood Test",
                    "target_department": 0,
                    "base_consultation_time": 10.0,
                    "cancellation_prob": 0.1,
                    "is_emergency": False,
                    "arrival_time": 5.0
                }
            ]
        }
        response = self.client.post(
            '/appointment/optimize/',
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertIn("completed_schedule", data)
        self.assertGreaterEqual(len(data["completed_schedule"]), 1)
