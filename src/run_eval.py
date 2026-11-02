"""Send every task to every model and save the raw responses.

    python -m src.run_eval --list-models gemini     # see which model ids you can use
    python -m src.run_eval --models gemini:<model-id> anthropic:claude-opus-5-5
    python -m src.run_eval --dry-run          # print prompts, no API calls

Output: results/raw/<timestamp>[_<tag>].jsonl (one line per task x model x sample).
Then grade with:  python -m src.grade results/raw/<file>.jsonl [more files ...] --name <report>
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks" / "tasks.json"
RAW_DIR = ROOT / "results" / "raw"

# Free-tier lineup used for the published results (see README > Limitations).
DEFAULT_MODELS = ["gemini:gemini-3.8-flash", "gemini:gemma-4-31b-it", "groq:openai/gpt-oss-120b"]
EFFORT = "high"  # same reasoning-effort label for every provider, recorded in the output
# Thinking tokens count against this limit on some providers (e.g. Gemini), so it must
# be generous: a 32k limit cut off a correct Gemini answer before its FINAL ANSWER line.
MAX_OUTPUT_TOKENS = 65536
FALLBACK_OUTPUT_TOKENS = 32000  # for models whose maximum output is lower
RATE_LIMIT_RETRIES = 3  # free tiers have per-minute quotas; wait and retry
RATE_LIMIT_WAIT_S = 65
# Hard per-request timeout. Without it a stalled free-tier connection hung for ~100 min.
# The slowest genuine answer observed (Gemini Flash, high effort) took ~8.5 min.
REQUEST_TIMEOUT_S = 900
TRANSIENT_RETRIES = 2  # timeouts, 5xx, dropped connections
TRANSIENT_WAIT_S = 30


def _is_transient(e: Exception) -> bool:
    """Timeouts, dropped connections and 5xx server errors (any provider SDK)."""
    name = type(e).__name__
    status = getattr(e, "status_code", None)
    return ("Timeout" in name or "Connection" in name
            or (isinstance(status, int) and status >= 500))


def with_rate_limit_retry(call, model: str, prompt: str,
                          transient_wait: int = TRANSIENT_WAIT_S) -> dict:
    """Retry quota errors and transient failures; anything else is raised immediately.

    - HTTP 429, or Groq's 413 'request too large' (its estimate depends on recent usage,
      so it is retried once after the window resets): wait RATE_LIMIT_WAIT_S.
    - Timeouts, dropped connections, 5xx: wait `transient_wait`, at most TRANSIENT_RETRIES.
      On a daily-capped free tier every failed attempt still costs one request of the
      day's quota, so a long wait (spread over the day) beats fast retries in a spike.
    """
    quota_tries = transient_tries = 0
    while True:
        try:
            return call(model, prompt)
        except Exception as e:
            status = getattr(e, "status_code", None)
            too_large = "request too large" in str(e).lower()
            if status == 429 or (status == 413 and too_large):
                quota_tries += 1
                if quota_tries > RATE_LIMIT_RETRIES or (too_large and quota_tries > 1):
                    raise
                wait = RATE_LIMIT_WAIT_S
            elif _is_transient(e):
                transient_tries += 1
                if transient_tries > TRANSIENT_RETRIES:
                    raise
                wait = transient_wait
            else:
                raise
            print(f"({status or type(e).__name__}, waiting {wait}s)", end=" ", flush=True)
            time.sleep(wait)


def call_anthropic(model: str, prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(timeout=REQUEST_TIMEOUT_S, max_retries=0)
    # Streaming avoids HTTP timeouts on long reasoning. No refusal fallback is
    # configured on purpose: a fallback would silently answer with a different
    # model and corrupt the per-model scores. Refusals are recorded instead.
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if b.type == "text")
    return {
        "response": text,
        "stop_reason": msg.stop_reason,
        "usage": {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens},
        "request_id": msg._request_id,
    }


def call_openai(model: str, prompt: str) -> dict:
    import openai

    client = openai.OpenAI(timeout=REQUEST_TIMEOUT_S, max_retries=0)
    try:
        resp = client.responses.create(model=model, input=prompt, reasoning={"effort": EFFORT})
    except openai.BadRequestError:
        # Non-reasoning models reject the reasoning parameter.
        resp = client.responses.create(model=model, input=prompt)
    return {
        "response": resp.output_text,
        "stop_reason": resp.status,
        "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
        "request_id": resp.id,
    }


# Free-tier providers that expose an OpenAI-compatible Chat Completions API.
# provider -> (base_url, env var holding the key)
COMPATIBLE = {
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
}


def _compatible_client(provider: str):
    import os

    import openai

    base_url, env_var = COMPATIBLE[provider]
    key = os.environ.get(env_var)
    if not key:
        raise RuntimeError(f"{env_var} is not set in .env")
    return openai.OpenAI(base_url=base_url, api_key=key,
                         timeout=REQUEST_TIMEOUT_S, max_retries=0)


def make_compatible_caller(provider: str):
    def call(model: str, prompt: str) -> dict:
        import openai

        client = _compatible_client(provider)
        # Set the output limit explicitly: provider defaults (e.g. Groq's) are small
        # enough to cut a reasoning model off mid-working, which would be a false fail.
        base = dict(model=model, messages=[{"role": "user", "content": prompt}])
        # Try the most generous settings first; fall back when a model rejects them
        # (no reasoning mode, or a lower maximum output). The settings used are recorded.
        attempts = [
            dict(max_tokens=MAX_OUTPUT_TOKENS, reasoning_effort=EFFORT),
            dict(max_tokens=MAX_OUTPUT_TOKENS),
            dict(max_tokens=FALLBACK_OUTPUT_TOKENS, reasoning_effort=EFFORT),
            dict(max_tokens=FALLBACK_OUTPUT_TOKENS),
        ]
        for i, extra in enumerate(attempts):
            try:
                resp = client.chat.completions.create(**base, **extra)
                break
            except openai.BadRequestError:
                if i == len(attempts) - 1:
                    raise
        choice = resp.choices[0]
        usage = resp.usage
        return {
            "response": choice.message.content or "",
            "stop_reason": choice.finish_reason,
            "usage": {"input_tokens": getattr(usage, "prompt_tokens", None),
                      "output_tokens": getattr(usage, "completion_tokens", None)},
            "request_id": resp.id,
            "settings": extra,
        }
    return call


PROVIDERS = {"anthropic": call_anthropic, "openai": call_openai,
             **{p: make_compatible_caller(p) for p in COMPATIBLE}}


def list_models(provider: str) -> None:
    load_dotenv(ROOT / ".env")
    if provider in COMPATIBLE:
        client = _compatible_client(provider)
    elif provider == "openai":
        import openai
        client = openai.OpenAI()
    else:
        import anthropic
        client = anthropic.Anthropic(timeout=REQUEST_TIMEOUT_S, max_retries=0)
    for m in sorted(m.id for m in client.models.list()):
        print(f"{provider}:{m}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help="provider:model, e.g. anthropic:claude-opus-5-5 openai:gpt-5")
    ap.add_argument("--samples", type=int, default=1, help="answers per task per model")
    ap.add_argument("--tasks", nargs="*", help="only run these task ids")
    ap.add_argument("--dry-run", action="store_true", help="print prompts, make no API calls")
    ap.add_argument("--tag", default="", help="suffix for the output file name, e.g. gemini-flash")
    ap.add_argument("--out", type=Path,
                    help="output file; if it exists, finished answers are kept and only "
                         "missing or failed (error/truncated) ones are re-run")
    ap.add_argument("--transient-wait", type=int, default=TRANSIENT_WAIT_S, metavar="S",
                    help=f"seconds to wait before retrying a timeout/5xx (default "
                         f"{TRANSIENT_WAIT_S}); use a long wait for daily-capped free tiers")
    ap.add_argument("--stop-after-quota-failures", type=int, default=0, metavar="N",
                    help="stop a model after N consecutive samples fail with HTTP 429 even "
                         "after retries (daily quota used up); 0 = never stop")
    ap.add_argument("--list-models", metavar="PROVIDER", choices=sorted(PROVIDERS),
                    help="print the model ids your key can use, then exit")
    args = ap.parse_args()

    if args.list_models:
        list_models(args.list_models)
        return

    load_dotenv(ROOT / ".env")
    tasks = json.loads(TASKS.read_text())
    if args.tasks:
        tasks = [t for t in tasks if t["id"] in args.tasks]

    if args.dry_run:
        for t in tasks:
            print(f"=== {t['id']} (expected {t['answer']}) ===\n{t['prompt']}\n")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RAW_DIR / (f"{stamp}_{args.tag}.jsonl" if args.tag else f"{stamp}.jsonl")

    # Resume: keep finished answers, drop failed ones so they are re-run.
    kept, done = [], set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            failed = rec.get("error") or rec.get("stop_reason") in ("length", "max_tokens", "incomplete")
            if not failed:
                kept.append(line)
                done.add((rec["model"], rec["task_id"], rec["sample"]))
        print(f"Resuming {out_path.name}: keeping {len(kept)} finished answers")

    with out_path.open("w") as f:
        for line in kept:
            f.write(line + "\n")
        f.flush()
        for spec in args.models:
            provider, model = spec.split(":", 1)
            call = PROVIDERS[provider]
            quota_failures = 0  # consecutive samples that ended in a 429
            for t, s in ((t, s) for t in tasks for s in range(args.samples)):
                if (spec, t["id"], s) in done:
                    continue
                if args.stop_after_quota_failures and quota_failures >= args.stop_after_quota_failures:
                    print(f"{spec}: {quota_failures} consecutive quota failures, "
                          f"stopping this model (rerun with --out later to resume)")
                    break
                print(f"{spec:35s} {t['id']:35s} sample {s} ...", end=" ", flush=True)
                rec = {"task_id": t["id"], "model": spec, "sample": s, "effort": EFFORT}
                start = time.time()
                try:
                    rec.update(with_rate_limit_retry(call, model, t["prompt"],
                                                     args.transient_wait))
                    print("done")
                    quota_failures = 0
                except Exception as e:  # record and continue; graded as "error"
                    rec["error"] = f"{type(e).__name__}: {e}"
                    quota_failures = quota_failures + 1 if getattr(e, "status_code", None) == 429 else 0
                    print(f"ERROR {rec['error'][:120]}")
                rec["latency_s"] = round(time.time() - start, 1)
                f.write(json.dumps(rec) + "\n")
                f.flush()

    shown = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
    print(f"\nSaved {shown}")
    print(f"Grade with: python -m src.grade {shown}")


if __name__ == "__main__":
    main()
