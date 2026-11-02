| Model | Correct | Wrong | No answer | Truncated | Error | Accuracy |
|---|---|---|---|---|---|---|
| gemini:gemini-3.8-flash | 5 | 0 | 0 | 0 | 11 | 5/5 (100%) +11 excl. |
| gemini:gemma-4-31b-it | 0 | 18 | 0 | 0 | 2 | 0/18 (0%) +2 excl. |
| groq:openai/gpt-oss-120b | 0 | 21 | 0 | 0 | 9 | 0/21 (0%) +9 excl. |

| Model | L1 explicit | L2 derived | L3 chained | L4 LBRM |
|---|---|---|---|---|
| gemini:gemini-3.8-flash | 2/2 (100%) +1 excl. | 1/1 (100%) | 1/1 (100%) +8 excl. | 1/1 (100%) +2 excl. |
| gemini:gemma-4-31b-it | 0/10 (0%) +2 excl. | 0/7 (0%) | - | 0/1 (0%) |
| groq:openai/gpt-oss-120b | 0/12 (0%) | 0/5 (0%) +4 excl. | 0/4 (0%) +5 excl. | - |

| Task | Level | Expected | gemini:gemini-3.8-flash | gemini:gemma-4-31b-it | groq:openai/gpt-oss-120b |
|---|---|---|---|---|---|
| ldpc-filler-bits-bg2-large-tb | L1 | 96 |  | ❌ 2892, error, error | ❌ 216, ❌ 280, ❌ 2664 |
| tbs-156-cap | L1 | 54296 | ✅, ✅, error | ❌ 67392, ❌ 40416, ❌ 54789 | ❌ 81880, ❌ 24920, ❌ 86144 |
| tbs-256qam-xoverhead | L1 | 143400 |  | ❌ 160225, ❌ 106848, ❌ 44055 | ❌ 38240, ❌ 47280, ❌ 94184 |
| tbs-low-rate-segmentation | L1 | 59496 |  | ❌ 314496, ❌ 448058, ❌ 64471 | ❌ 94600, ❌ 61440, ❌ 73632 |
| cfg-tbs-100mhz-256qam-4layer | L2 | 868584 | ✅ | ❌ 742210, ❌ 560990, ❌ 804000 | ❌ 53824, error, ❌ 737328 |
| cfg-tbs-156-cap-derived | L2 | 100392 |  | ❌ 25876 | ❌ 38240, error, ❌ 65104 |
| cfg-tbs-dmrs-type2-xoverhead | L2 | 65576 |  | ❌ 41167, ❌ 12868, ❌ 40296 | error, ❌ 102912, error |
| cfg-filler-bits-ld-trap | L3 | 136 | ✅, error, error |  | error, ❌ 51, error |
| cfg-ratematch-E-last-cb | L3 | 9088 | error, error, error |  | error, ❌ 9059, error |
| cfg-ratematch-E-xoverhead | L3 | 13992 | error, error, error |  | ❌ 5551, error, ❌ 10176 |
| lbrm-k0-rv3-maxmimo8 | L4 | 14592 | error, ✅, error | ❌ 92160 |  |

Accuracy = correct / (correct + wrong + no_answer). `truncated` and `error` are infrastructure failures: excluded from accuracy and shown as "+N excl.".
