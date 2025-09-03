from hydrocata.optimization.bayesian import BayesianOptimizer
import pytest
import torch


@pytest.fixture
def pbounds():
    return {"x1": (0.0, 10.0), "x2": (-5.0, 5.0)}


def test_init_requires_pbounds():
    with pytest.raises(ValueError):
        BayesianOptimizer({})


def test_midpoint_recommendation_before_data(pbounds):
    opt = BayesianOptimizer(pbounds, batch_size=2)
    recs = opt.recommend()

    assert len(recs) == 2  # batch_size
    for rec in recs:
        assert pytest.approx(rec["x1"]) == 5.0
        assert pytest.approx(rec["x2"]) == 0.0


def test_update_and_storage(pbounds):
    opt = BayesianOptimizer(pbounds, batch_size=2)
    opt.update_data({"x1": 2.0, "x2": -1.0}, 0.5)

    assert opt.initialized is True
    assert len(opt.X) == 1
    assert len(opt.Y) == 1
    assert opt.X[0] == [2.0, -1.0]
    assert opt.Y[0] == [0.5]


def test_batch_recommendation_after_data(pbounds):
    opt = BayesianOptimizer(pbounds, batch_size=3)
    # Add two points
    opt.update_data({"x1": 2.0, "x2": -1.0}, 0.5)
    opt.update_data({"x1": 7.0, "x2": 3.0}, 0.8)

    recs = opt.recommend()

    # Should return batch_size recommendations
    assert len(recs) == 3
    for rec in recs:
        assert set(rec.keys()) == {"x1", "x2"}
        # Values should lie within pbounds
        assert pbounds["x1"][0] <= rec["x1"] <= pbounds["x1"][1]
        assert pbounds["x2"][0] <= rec["x2"] <= pbounds["x2"][1]
