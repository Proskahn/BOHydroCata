from bayes_opt import BayesianOptimization
import numpy as np


class BayesianOptimizer:
    """Bayesian optimizer using bayesian-optimization library."""

    def __init__(self):
        """Initialize the optimizer with empty data."""
        self.X = []  # Input: ratios of LrO2 (x1)
        self.Y = []  # Output: hydrogen production rates
        self.optimizer = BayesianOptimization(
            f=None,
            pbounds={"x1": (0.0, 1.0)},
            random_state=1,
        )

    def update_data(self, x1: float, hydrogen_rate: float):
        """Update the optimizer with a new experimental result."""
        self.X.append(x1)
        self.Y.append(hydrogen_rate)
        # Register the observation with the optimizer
        self.optimizer.register(params={"x1": x1}, target=hydrogen_rate)

    def recommend(self) -> float:
        """Recommend the next x1 to try using Bayesian optimization."""
        if not self.X:
            # If no data, return a random point
            return np.random.uniform(0, 1)

        # Suggest the next point to evaluate
        next_point = self.optimizer.suggest()
        return next_point["x1"]
