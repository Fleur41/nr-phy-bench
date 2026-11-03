| Model | Correct | Wrong | No answer | Truncated | Error | Accuracy |
|---|---|---|---|---|---|---|
| gemini:gemini-3.8-flash | 5 | 0 | 0 | 0 | 4 | 5/5 (100%) +4 excl. |
| gemini:gemma-4-31b-it | 0 | 42 | 0 | 0 | 0 | 0/42 (0%) |
| groq:openai/gpt-oss-120b | 0 | 42 | 0 | 0 | 0 | 0/42 (0%) |

| Model | L1 explicit | L2 derived | L3 chained | L4 LBRM | L5 context |
|---|---|---|---|---|---|
| gemini:gemini-3.8-flash | 2/2 (100%) +1 excl. | 1/1 (100%) | 1/1 (100%) +3 excl. | 1/1 (100%) | - |
| gemini:gemma-4-31b-it | 0/12 (0%) | 0/9 (0%) | 0/9 (0%) | 0/6 (0%) | 0/6 (0%) |
| groq:openai/gpt-oss-120b | 0/12 (0%) | 0/9 (0%) | 0/9 (0%) | 0/6 (0%) | 0/6 (0%) |

| Task | Level | Expected | gemini:gemini-3.8-flash | gemini:gemma-4-31b-it | groq:openai/gpt-oss-120b |
|---|---|---|---|---|---|
| ldpc-filler-bits-bg2-large-tb | L1 | 96 |  | ❌ 2892, ❌ 0, ❌ 233 | ❌ 216, ❌ 280, ❌ 2664 |
| tbs-156-cap | L1 | 54296 | ✅, ✅, error | ❌ 67392, ❌ 40416, ❌ 54789 | ❌ 81880, ❌ 24920, ❌ 86144 |
| tbs-256qam-xoverhead | L1 | 143400 |  | ❌ 160225, ❌ 106848, ❌ 44055 | ❌ 38240, ❌ 47280, ❌ 94184 |
| tbs-low-rate-segmentation | L1 | 59496 |  | ❌ 314496, ❌ 448058, ❌ 64471 | ❌ 94600, ❌ 61440, ❌ 73632 |
| cfg-tbs-100mhz-256qam-4layer | L2 | 868584 | ✅ | ❌ 742210, ❌ 560990, ❌ 804000 | ❌ 53824, ❌ 737328, ❌ 860104 |
| cfg-tbs-156-cap-derived | L2 | 100392 |  | ❌ 25876, ❌ 81357, ❌ 175960 | ❌ 38240, ❌ 65104, ❌ 194360 |
| cfg-tbs-dmrs-type2-xoverhead | L2 | 65576 |  | ❌ 41167, ❌ 12868, ❌ 40296 | ❌ 102912, ❌ 55152, ❌ 61992 |
| cfg-filler-bits-ld-trap | L3 | 136 | ✅, error, error | ❌ 7, ❌ 268, ❌ 64 | ❌ 51, ❌ 1, ❌ 741 |
| cfg-ratematch-E-last-cb | L3 | 9088 |  | ❌ 11948, ❌ 13794, ❌ 22071 | ❌ 9059, ❌ 19110, ❌ 11772 |
| cfg-ratematch-E-xoverhead | L3 | 13992 | error | ❌ 16718, ❌ 16808, ❌ 8549 | ❌ 5551, ❌ 10176, ❌ 10175 |
| lbrm-k0-rv2-2layer | L4 | 8832 |  | ❌ 340704, ❌ 7776, ❌ 72831 | ❌ 4068, ❌ 6336, ❌ 3168 |
| lbrm-k0-rv3-maxmimo8 | L4 | 14592 | ✅ | ❌ 92160, ❌ 166584, ❌ 51840 | ❌ 12288, ❌ 31980, ❌ 7626 |
| ctx-2cw-7layer-tb2 | L5 | 655800 |  | ❌ 264045, ❌ 219596, ❌ 49227 | ❌ 117856, ❌ 138160, ❌ 136880 |
| ctx-paging-tb-scaling | L5 | 3824 |  | ❌ 2451, ❌ 3712, ❌ 3797 | ❌ 3264, ❌ 8640, ❌ 808 |

Accuracy = correct / (correct + wrong + no_answer). `truncated` and `error` are infrastructure failures: excluded from accuracy and shown as "+N excl.".
