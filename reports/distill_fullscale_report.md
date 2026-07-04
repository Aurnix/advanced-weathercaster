# distill_fullscale_report

## Skill retained through distillation (cell A, BSS vs climatology)

| target     |   bss_gbm |   bss_additive_float |   bss_quantized_int8 |
|:-----------|----------:|---------------------:|---------------------:|
| precip_6h  |     0.377 |                0.316 |                0.316 |
| precip_12h |     0.311 |                0.222 |                0.222 |
| precip_24h |     0.243 |                0.133 |                0.133 |
| windup_6h  |     0.383 |                0.270 |                0.269 |
| windup_12h |     0.411 |                0.286 |                0.286 |
| windup_24h |     0.359 |                0.264 |                0.264 |
| pfall_6h   |     0.481 |                0.191 |                0.191 |
| pfall_12h  |     0.401 |                0.130 |                0.130 |
| pfall_24h  |     0.243 |                0.049 |                0.049 |

**Artifact size: 2515 bytes (2.46 KB) for 9 heads + bin edges** (budget: 32-64 KB).

Artifact written to `D:\neosager-data\artifacts\neosager_tables.json`.