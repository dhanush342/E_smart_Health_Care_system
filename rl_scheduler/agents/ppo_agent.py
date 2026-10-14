import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np
from typing import List, Tuple

class ActorCriticNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 64):
        super(ActorCriticNetwork, self).__init__()
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim)
        )
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        logits = self.actor(state)
        value = self.critic(state)
        return logits, value

class PPOAgent:
    """
    Proximal Policy Optimization (PPO) Agent for Stage 3: Live Queue Execution.
    Handles continuous minute-by-minute scheduling with stability clipping.
    """
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        lr: float = 3e-4,
        gamma: float = 0.99,
        eps_clip: float = 0.2,
        k_epochs: int = 4
    ):
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.k_epochs = k_epochs

        self.policy = ActorCriticNetwork(state_dim, action_dim)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)

        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.logprobs: List[float] = []
        self.rewards: List[float] = []
        self.dones: List[bool] = []

    def select_action(self, state: np.ndarray, evaluate: bool = False) -> Tuple[int, float]:
        state_t = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            logits, _ = self.policy(state_t)
            probs = torch.softmax(logits, dim=-1)
            dist = Categorical(probs)
            if evaluate:
                action = torch.argmax(probs, dim=-1)
            else:
                action = dist.sample()
            log_prob = dist.log_prob(action)

        return action.item(), log_prob.item()

    def store_transition(self, state: np.ndarray, action: int, logprob: float, reward: float, done: bool):
        self.states.append(state)
        self.actions.append(action)
        self.logprobs.append(logprob)
        self.rewards.append(reward)
        self.dones.append(done)

    def clear_buffer(self):
        self.states.clear()
        self.actions.clear()
        self.logprobs.clear()
        self.rewards.clear()
        self.dones.clear()

    def update(self) -> float:
        if len(self.states) == 0:
            return 0.0

        # Compute Monte Carlo returns
        returns = []
        discounted_reward = 0
        for reward, done in zip(reversed(self.rewards), reversed(self.dones)):
            if done:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            returns.insert(0, discounted_reward)

        returns_t = torch.FloatTensor(returns)
        if returns_t.std() > 1e-8:
            returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)

        old_states = torch.FloatTensor(np.array(self.states))
        old_actions = torch.LongTensor(self.actions)
        old_logprobs = torch.FloatTensor(self.logprobs)

        total_loss = 0.0
        for _ in range(self.k_epochs):
            logits, state_values = self.policy(old_states)
            probs = torch.softmax(logits, dim=-1)
            dist = Categorical(probs)
            new_logprobs = dist.log_prob(old_actions)
            entropy = dist.entropy()

            ratios = torch.exp(new_logprobs - old_logprobs)
            advantages = returns_t - state_values.squeeze().detach()

            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1.0 - self.eps_clip, 1.0 + self.eps_clip) * advantages

            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(state_values.squeeze(), returns_t)
            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy.mean()

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        self.clear_buffer()
        return total_loss / self.k_epochs
