"""Send every task to every model and save the raw responses.

    python -m src.run_eval --list-models gemini     # see which model ids you can use
    python -m src.run_eval --models gemini:<model-id> anthropic:claude-opus-5-5
    python -m src.run_eval --dry-run          # print prompts, no API calls

Output: results/raw/<timestamp>.jsonl (one line per task x model x sample).
Then grade with:  python -m src.grade results/raw/<timestamp>.jsonl
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

DEFAULT_MODELS = ["anthropic:claude-opus-5-5", "anthropic:claude-sonnet-5-5", "openai:gpt-5"]
EFFORT = "high"  # same reasoning-effort label for every provider, recorded in the output


def call_anthropic(model: str, prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
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

    client = openai.OpenAI()
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
    "github": ("https://models.github.ai/inference", "GITHUB_TOKEN"),
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
    return openai.OpenAI(base_url=base_url, api_key=key)


def make_compatible_caller(provider: str):
    def call(model: str, prompt: str) -> dict:
        import openai

        client = _compatible_client(provider)
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, reasoning_effort=EFFORT)
        except openai.BadRequestError:
            # Models without a reasoning mode reject reasoning_effort.
            resp = client.chat.completions.create(model=model, messages=messages)
        choice = resp.choices[0]
        usage = resp.usage
        return {
            "response": choice.message.content or "",
            "stop_reason": choice.finish_reason,
            "usage": {"input_tokens": getattr(usage, "prompt_tokens", None),
                      "output_tokens": getattr(usage, "completion_tokens", None)},
            "request_id": resp.id,
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
        client = anthropic.Anthropic()
    for m in sorted(m.id for m in client.models.list()):
        print(f"{provider}:{m}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help="provider:model, e.g. anthropic:claude-opus-5-5 openai:gpt-5")
    ap.add_argument("--samples", type=int, default=1, help="answers per task per model")
    ap.add_argument("--tasks", nargs="*", help="only run these task ids")
    ap.add_argument("--dry-run", action="store_true", help="print prompts, make no API calls")
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
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RAW_DIR / f"{stamp}.jsonl"

    with out_path.open("w") as f:
        for spec in args.models:
            provider, model = spec.split(":", 1)
            call = PROVIDERS[provider]
            for t in tasks:
                for s in range(args.samples):
                    print(f"{spec:35s} {t['id']:35s} sample {s} ...", end=" ", flush=True)
                    rec = {"task_id": t["id"], "model": spec, "sample": s, "effort": EFFORT}
                    start = time.time()
                    try:
                        rec.update(call(model, t["prompt"]))
                        print("done")
                    except Exception as e:  # record and continue; graded as "error"
                        rec["error"] = f"{type(e).__name__}: {e}"
                        print(f"ERROR {rec['error'][:120]}")
                    rec["latency_s"] = round(time.time() - start, 1)
                    f.write(json.dumps(rec) + "\n")
                    f.flush()

    print(f"\nSaved {out_path.relative_to(ROOT)}")
    print(f"Grade with: python -m src.grade {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
