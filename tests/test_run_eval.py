"""Retry policy of the runner, tested with simulated failures (no API calls)."""
import pytest

from src import run_eval


class FakeError(Exception):
    def __init__(self, status=None, msg=""):
        super().__init__(msg)
        self.status_code = status


class APITimeoutError(Exception):
    pass


def make_call(failures):
    """A fake API call that raises each exception in `failures`, then succeeds."""
    calls = {"n": 0}

    def call(model, prompt):
        calls["n"] += 1
        if failures:
            raise failures.pop(0)
        return {"response": "FINAL ANSWER: 1"}
    return call, calls


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(run_eval.time, "sleep", lambda s: None)


def test_transient_errors_are_retried():
    call, calls = make_call([APITimeoutError(), FakeError(500)])
    assert run_eval.with_rate_limit_retry(call, "m", "p")["response"]
    assert calls["n"] == 3


def test_transient_retries_are_bounded():
    call, _ = make_call([APITimeoutError()] * (run_eval.TRANSIENT_RETRIES + 1))
    with pytest.raises(APITimeoutError):
        run_eval.with_rate_limit_retry(call, "m", "p")


def test_rate_limit_retried_then_succeeds():
    call, calls = make_call([FakeError(429), FakeError(429)])
    run_eval.with_rate_limit_retry(call, "m", "p")
    assert calls["n"] == 3


def test_too_large_retried_only_once():
    err = lambda: FakeError(413, "Request too large for model")
    call, calls = make_call([err(), err()])
    with pytest.raises(FakeError):
        run_eval.with_rate_limit_retry(call, "m", "p")
    assert calls["n"] == 2


def test_client_errors_are_not_retried():
    call, calls = make_call([FakeError(401, "bad key")])
    with pytest.raises(FakeError):
        run_eval.with_rate_limit_retry(call, "m", "p")
    assert calls["n"] == 1
