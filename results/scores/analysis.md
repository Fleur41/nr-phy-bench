First step where the working leaves the reference procedure (wrong answers only).

| Model | Wrong | n_PRB | N_RE | N_info | K' |
|---|---|---|---|---|---|
| gemini:gemma-4-31b-it | 42 | 8 | 19 | 12 | 3 |
| groq:openai/gpt-oss-120b | 42 | 9 | 19 | 11 | 3 |

| Task | Level | Model | Sample | Answer | Expected | First break |
|---|---|---|---|---|---|---|
| ldpc-filler-bits-bg2-large-tb | L1 | gemini:gemma-4-31b-it | 0 | 2892 | 96 | K' |
| ldpc-filler-bits-bg2-large-tb | L1 | gemini:gemma-4-31b-it | 1 | 0 | 96 | K' |
| ldpc-filler-bits-bg2-large-tb | L1 | gemini:gemma-4-31b-it | 2 | 233 | 96 | K' |
| ldpc-filler-bits-bg2-large-tb | L1 | groq:openai/gpt-oss-120b | 0 | 216 | 96 | K' |
| ldpc-filler-bits-bg2-large-tb | L1 | groq:openai/gpt-oss-120b | 1 | 280 | 96 | K' |
| ldpc-filler-bits-bg2-large-tb | L1 | groq:openai/gpt-oss-120b | 2 | 2664 | 96 | K' |
| tbs-156-cap | L1 | gemini:gemma-4-31b-it | 0 | 67392 | 54296 | N_RE |
| tbs-156-cap | L1 | gemini:gemma-4-31b-it | 1 | 40416 | 54296 | N_RE |
| tbs-156-cap | L1 | gemini:gemma-4-31b-it | 2 | 54789 | 54296 | N_RE |
| tbs-156-cap | L1 | groq:openai/gpt-oss-120b | 0 | 81880 | 54296 | N_RE |
| tbs-156-cap | L1 | groq:openai/gpt-oss-120b | 1 | 24920 | 54296 | N_RE |
| tbs-156-cap | L1 | groq:openai/gpt-oss-120b | 2 | 86144 | 54296 | N_RE |
| tbs-256qam-xoverhead | L1 | gemini:gemma-4-31b-it | 0 | 44055 | 143400 | N_info |
| tbs-256qam-xoverhead | L1 | gemini:gemma-4-31b-it | 1 | 160225 | 143400 | N_info |
| tbs-256qam-xoverhead | L1 | gemini:gemma-4-31b-it | 2 | 106848 | 143400 | N_info |
| tbs-256qam-xoverhead | L1 | groq:openai/gpt-oss-120b | 0 | 38240 | 143400 | N_info |
| tbs-256qam-xoverhead | L1 | groq:openai/gpt-oss-120b | 1 | 94184 | 143400 | N_info |
| tbs-256qam-xoverhead | L1 | groq:openai/gpt-oss-120b | 2 | 47280 | 143400 | N_info |
| tbs-low-rate-segmentation | L1 | gemini:gemma-4-31b-it | 0 | 314496 | 59496 | N_RE |
| tbs-low-rate-segmentation | L1 | gemini:gemma-4-31b-it | 1 | 448058 | 59496 | N_info |
| tbs-low-rate-segmentation | L1 | gemini:gemma-4-31b-it | 2 | 64471 | 59496 | N_info |
| tbs-low-rate-segmentation | L1 | groq:openai/gpt-oss-120b | 0 | 94600 | 59496 | N_info |
| tbs-low-rate-segmentation | L1 | groq:openai/gpt-oss-120b | 1 | 61440 | 59496 | N_info |
| tbs-low-rate-segmentation | L1 | groq:openai/gpt-oss-120b | 2 | 73632 | 59496 | N_info |
| cfg-tbs-100mhz-256qam-4layer | L2 | gemini:gemma-4-31b-it | 0 | 742210 | 868584 | N_RE |
| cfg-tbs-100mhz-256qam-4layer | L2 | gemini:gemma-4-31b-it | 1 | 560990 | 868584 | N_RE |
| cfg-tbs-100mhz-256qam-4layer | L2 | gemini:gemma-4-31b-it | 2 | 804000 | 868584 | N_RE |
| cfg-tbs-100mhz-256qam-4layer | L2 | groq:openai/gpt-oss-120b | 0 | 53824 | 868584 | N_RE |
| cfg-tbs-100mhz-256qam-4layer | L2 | groq:openai/gpt-oss-120b | 1 | 860104 | 868584 | N_RE |
| cfg-tbs-100mhz-256qam-4layer | L2 | groq:openai/gpt-oss-120b | 2 | 737328 | 868584 | N_RE |
| cfg-tbs-156-cap-derived | L2 | gemini:gemma-4-31b-it | 0 | 25876 | 100392 | N_info |
| cfg-tbs-156-cap-derived | L2 | gemini:gemma-4-31b-it | 1 | 81357 | 100392 | N_info |
| cfg-tbs-156-cap-derived | L2 | gemini:gemma-4-31b-it | 2 | 175960 | 100392 | N_RE |
| cfg-tbs-156-cap-derived | L2 | groq:openai/gpt-oss-120b | 0 | 38240 | 100392 | N_RE |
| cfg-tbs-156-cap-derived | L2 | groq:openai/gpt-oss-120b | 1 | 194360 | 100392 | N_info |
| cfg-tbs-156-cap-derived | L2 | groq:openai/gpt-oss-120b | 2 | 65104 | 100392 | N_info |
| cfg-tbs-dmrs-type2-xoverhead | L2 | gemini:gemma-4-31b-it | 0 | 41167 | 65576 | n_PRB |
| cfg-tbs-dmrs-type2-xoverhead | L2 | gemini:gemma-4-31b-it | 1 | 12868 | 65576 | n_PRB |
| cfg-tbs-dmrs-type2-xoverhead | L2 | gemini:gemma-4-31b-it | 2 | 40296 | 65576 | N_RE |
| cfg-tbs-dmrs-type2-xoverhead | L2 | groq:openai/gpt-oss-120b | 0 | 61992 | 65576 | N_RE |
| cfg-tbs-dmrs-type2-xoverhead | L2 | groq:openai/gpt-oss-120b | 1 | 102912 | 65576 | n_PRB |
| cfg-tbs-dmrs-type2-xoverhead | L2 | groq:openai/gpt-oss-120b | 2 | 55152 | 65576 | n_PRB |
| cfg-filler-bits-ld-trap | L3 | gemini:gemma-4-31b-it | 0 | 7 | 136 | N_RE |
| cfg-filler-bits-ld-trap | L3 | gemini:gemma-4-31b-it | 1 | 268 | 136 | n_PRB |
| cfg-filler-bits-ld-trap | L3 | gemini:gemma-4-31b-it | 2 | 64 | 136 | N_RE |
| cfg-filler-bits-ld-trap | L3 | groq:openai/gpt-oss-120b | 0 | 1 | 136 | N_RE |
| cfg-filler-bits-ld-trap | L3 | groq:openai/gpt-oss-120b | 1 | 51 | 136 | n_PRB |
| cfg-filler-bits-ld-trap | L3 | groq:openai/gpt-oss-120b | 2 | 741 | 136 | N_RE |
| cfg-ratematch-E-last-cb | L3 | gemini:gemma-4-31b-it | 0 | 22071 | 9088 | N_RE |
| cfg-ratematch-E-last-cb | L3 | gemini:gemma-4-31b-it | 1 | 11948 | 9088 | N_RE |
| cfg-ratematch-E-last-cb | L3 | gemini:gemma-4-31b-it | 2 | 13794 | 9088 | N_RE |
| cfg-ratematch-E-last-cb | L3 | groq:openai/gpt-oss-120b | 0 | 11772 | 9088 | N_RE |
| cfg-ratematch-E-last-cb | L3 | groq:openai/gpt-oss-120b | 1 | 9059 | 9088 | N_RE |
| cfg-ratematch-E-last-cb | L3 | groq:openai/gpt-oss-120b | 2 | 19110 | 9088 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | gemini:gemma-4-31b-it | 0 | 16718 | 13992 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | gemini:gemma-4-31b-it | 1 | 16808 | 13992 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | gemini:gemma-4-31b-it | 2 | 8549 | 13992 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | groq:openai/gpt-oss-120b | 0 | 5551 | 13992 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | groq:openai/gpt-oss-120b | 1 | 10175 | 13992 | N_RE |
| cfg-ratematch-E-xoverhead | L3 | groq:openai/gpt-oss-120b | 2 | 10176 | 13992 | N_RE |
| lbrm-k0-rv2-2layer | L4 | gemini:gemma-4-31b-it | 0 | 340704 | 8832 | n_PRB |
| lbrm-k0-rv2-2layer | L4 | gemini:gemma-4-31b-it | 1 | 7776 | 8832 | n_PRB |
| lbrm-k0-rv2-2layer | L4 | gemini:gemma-4-31b-it | 2 | 72831 | 8832 | n_PRB |
| lbrm-k0-rv2-2layer | L4 | groq:openai/gpt-oss-120b | 0 | 3168 | 8832 | n_PRB |
| lbrm-k0-rv2-2layer | L4 | groq:openai/gpt-oss-120b | 1 | 4068 | 8832 | n_PRB |
| lbrm-k0-rv2-2layer | L4 | groq:openai/gpt-oss-120b | 2 | 6336 | 8832 | n_PRB |
| lbrm-k0-rv3-maxmimo8 | L4 | gemini:gemma-4-31b-it | 0 | 92160 | 14592 | n_PRB |
| lbrm-k0-rv3-maxmimo8 | L4 | gemini:gemma-4-31b-it | 1 | 166584 | 14592 | n_PRB |
| lbrm-k0-rv3-maxmimo8 | L4 | gemini:gemma-4-31b-it | 2 | 51840 | 14592 | N_info |
| lbrm-k0-rv3-maxmimo8 | L4 | groq:openai/gpt-oss-120b | 0 | 12288 | 14592 | N_RE |
| lbrm-k0-rv3-maxmimo8 | L4 | groq:openai/gpt-oss-120b | 1 | 7626 | 14592 | n_PRB |
| lbrm-k0-rv3-maxmimo8 | L4 | groq:openai/gpt-oss-120b | 2 | 31980 | 14592 | n_PRB |
| ctx-2cw-7layer-tb2 | L5 | gemini:gemma-4-31b-it | 0 | 219596 | 655800 | N_RE |
| ctx-2cw-7layer-tb2 | L5 | gemini:gemma-4-31b-it | 1 | 49227 | 655800 | N_info |
| ctx-2cw-7layer-tb2 | L5 | gemini:gemma-4-31b-it | 2 | 264045 | 655800 | N_RE |
| ctx-2cw-7layer-tb2 | L5 | groq:openai/gpt-oss-120b | 0 | 117856 | 655800 | n_PRB |
| ctx-2cw-7layer-tb2 | L5 | groq:openai/gpt-oss-120b | 1 | 138160 | 655800 | N_RE |
| ctx-2cw-7layer-tb2 | L5 | groq:openai/gpt-oss-120b | 2 | 136880 | 655800 | N_RE |
| ctx-paging-tb-scaling | L5 | gemini:gemma-4-31b-it | 0 | 2451 | 3824 | N_info |
| ctx-paging-tb-scaling | L5 | gemini:gemma-4-31b-it | 1 | 3712 | 3824 | N_info |
| ctx-paging-tb-scaling | L5 | gemini:gemma-4-31b-it | 2 | 3797 | 3824 | N_info |
| ctx-paging-tb-scaling | L5 | groq:openai/gpt-oss-120b | 0 | 8640 | 3824 | N_info |
| ctx-paging-tb-scaling | L5 | groq:openai/gpt-oss-120b | 1 | 3264 | 3824 | N_info |
| ctx-paging-tb-scaling | L5 | groq:openai/gpt-oss-120b | 2 | 808 | 3824 | N_info |

`answer` = every reference intermediate value appears in the working, only the last step is wrong. Heuristic: see `src/analyze.py`.
