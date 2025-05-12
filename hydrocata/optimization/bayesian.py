import logging

from bayes_opt import BayesianOptimization

logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """Bayesian optimizer for recommending the next x1 value."""

    def __init__(self):
        self.optimizer = BayesianOptimization(
            f=None, pbounds={"x1": (0, 1)}, verbose=2, random_state=1
        )
        self.initialized = False

    def update_data(self, x1: float, objective_value: float) -> None:
        """Update the optimizer with a new data point."""
        try:
            self.optimizer.register(params={"x1": x1}, target=objective_value)
            self.initialized = True
            logger.debug(
                f"Updated optimizer with x1={x1}, objective_value={objective_value}"
            )
        except Exception as e:
            logger.error(f"Failed to update optimizer: {str(e)}")
            raise

    def recommend(self) -> float:
        """Recommend the next x1 value to test."""
        try:
            if not self.initialized:
                # Return a random point if no data is available
                return 0.5
            next_point = self.optimizer.suggest()
            logger.debug(f"Recommended next x1={next_point['x1']}")
            return next_point["x1"]
        except Exception as e:
            logger.error(f"Failed to recommend next x1: {str(e)}")
            raise
