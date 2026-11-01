| Model | Correct | Wrong | No answer | Truncated | Error | Accuracy |
|---|---|---|---|---|---|---|
| gemini:gemini-3.8-flash | 4 | 0 | 0 | 0 | 0 | 100% |
| gemini:gemma-4-31b-it | 0 | 1 | 0 | 0 | 1 | 0% |
| groq:openai/gpt-oss-120b | 0 | 5 | 0 | 0 | 1 | 0% |

| Model | L1 explicit | L2 derived | L3 chained |
|---|---|---|---|
| gemini:gemini-3.8-flash | 2/2 (100%) | 1/1 (100%) | 1/1 (100%) |
| gemini:gemma-4-31b-it | 0/2 (0%) | - | - |
| groq:openai/gpt-oss-120b | 0/6 (0%) | - | - |

| Task | Level | Expected | gemini:gemini-3.8-flash | gemini:gemma-4-31b-it | groq:openai/gpt-oss-120b |
|---|---|---|---|---|---|
| tbs-156-cap | L1 | 54296 | ✅, ✅ | ❌ 67392, error | ❌ 81880, ❌ 24920, error |
| tbs-low-rate-segmentation | L1 | 59496 |  |  | ❌ 94600, ❌ 61440, ❌ 73632 |
| cfg-tbs-100mhz-256qam-4layer | L2 | 868584 | ✅ |  |  |
| cfg-filler-bits-ld-trap | L3 | 136 | ✅ |  |  |
