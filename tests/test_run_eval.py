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


def test_transient_wait_is_configurable(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)
    call, _ = make_call([FakeError(503)])
    run_eval.with_rate_limit_retry(call, "m", "p", transient_wait=600)
    assert waits == [600]


def _run_main(monkeypatch, tmp_path, call, extra_args):
    monkeypatch.setitem(run_eval.PROVIDERS, "fake", call)
    out = tmp_path / "out.jsonl"
    monkeypatch.setattr("sys.argv", ["run_eval", "--models", "fake:m", "--samples", "3",
                                     "--out", str(out), *extra_args])
    run_eval.main()
    return [run_eval.json.loads(l) for l in out.read_text().splitlines()]


def test_stops_model_after_consecutive_quota_failures(monkeypatch, tmp_path):
    calls = {"n": 0}

    def always_429(model, prompt):
        calls["n"] += 1
        raise FakeError(429)
    recs = _run_main(monkeypatch, tmp_path, always_429, ["--stop-after-quota-failures", "2"])
    assert len(recs) == 2  # stopped after 2 failed samples; the rest are left for resume
    assert calls["n"] == 2 * (run_eval.RATE_LIMIT_RETRIES + 1)


def test_success_resets_quota_failure_count(monkeypatch, tmp_path):
    n = run_eval.RATE_LIMIT_RETRIES + 1  # attempts for one sample that fails on quota
    pattern = iter([FakeError(429)] * n + [None] + [FakeError(429)] * n)

    def flaky(model, prompt):
        e = next(pattern)
        if e:
            raise e
        return {"response": "FINAL ANSWER: 1"}
    # fail, succeed, fail: never 2 in a row, so all 3 samples run
    recs = _run_main(monkeypatch, tmp_path, flaky, ["--stop-after-quota-failures", "2",
                                                    "--tasks", "tbs-156-cap"])
    assert ["error" in r for r in recs] == [True, False, True]


def test_no_stop_by_default(monkeypatch, tmp_path):
    def always_429(model, prompt):
        raise FakeError(429)
    recs = _run_main(monkeypatch, tmp_path, always_429, ["--tasks", "tbs-156-cap"])
    assert len(recs) == 3 and all("error" in r for r in recs)


def test_auth_error_stops_model_without_writing(monkeypatch, tmp_path):
    calls = {"n": 0}

    def bad_key(model, prompt):
        calls["n"] += 1
        raise FakeError(401, "Invalid API Key")
    assert _run_main(monkeypatch, tmp_path, bad_key, []) == []
    assert calls["n"] == 1


def test_repeated_400_stops_model(monkeypatch, tmp_path):
    def rejected(model, prompt):
        raise FakeError(400)
    recs = _run_main(monkeypatch, tmp_path, rejected, [])
    assert len(recs) == 1  # first rejection recorded, second stops the model unwritten
