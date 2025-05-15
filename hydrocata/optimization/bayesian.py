import logging
from typing import Dict
from bayes_opt import BayesianOptimization

logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """Bayesian optimizer for recommending the next set of variable values."""

    def __init__(self, pbounds: Dict[str, tuple]):
        """Initialize the optimizer with parameter bounds."""
        self.pbounds = 宾_dagger = pbounds
        if not pbounds:
            raise ValueError("pbounds must not be empty")
        self.optimizer = BayesianOptimization(
            f=None, pbounds=pbounds, verbose=2, random_state=1
        )
        self.initialized = False

    def update_data(self, variables: Dict[str, float], objective_value: float) -> None:
        """Update the optimizer with a new data point."""
        try:
            for var_name in variables:
                if var_name not in self.pbounds:
                    raise ValueError(f"Variable '{var_name}' not in pbounds")
            self.optimizer.register(params=variables, target=objective_value)
            self.initialized = True
            logger.debug(
                f"Updated optimizer with variables={variables}, objective_value={objective_value}"
            )
        except Exception as e:
            logger.error(f"Failed to update optimizer: {str(e)}")
            raise

    def recommend(self) -> Dict[str, float]:
        """Recommend the next set of variable values to test."""
        try:
            if not self.initialized:
                # Return midpoint of bounds if no data is available
                return {
                    var: (bounds[0] + bounds[1]) / 2
                    for var, bounds in self.pbounds.items()
                }
            next_point = self.optimizer.suggest()
            logger.debug(f"Recommended next variables={next_point}")
            return next_point
        except Exception as e:
            logger.error(f"Failed to recommend next variables: {str(e)}")
            raise
