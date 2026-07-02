# distill_52station_report

## Skill retained through distillation (cell A, BSS vs climatology)

| target     |   bss_gbm |   bss_additive_float |   bss_quantized_int8 |
|:-----------|----------:|---------------------:|---------------------:|
| precip_6h  |     0.391 |                0.324 |                0.324 |
| precip_12h |     0.322 |                0.228 |                0.227 |
| precip_24h |     0.250 |                0.142 |                0.142 |
| windup_6h  |     0.376 |                0.242 |                0.242 |
| windup_12h |     0.402 |                0.264 |                0.264 |
| windup_24h |     0.356 |                0.253 |                0.253 |
| pfall_6h   |     0.493 |                0.224 |                0.222 |
| pfall_12h  |     0.409 |                0.145 |                0.145 |
| pfall_24h  |     0.242 |                0.053 |                0.052 |

**Artifact size: 2515 bytes (2.46 KB) for 9 heads + bin edges** (budget: 32-64 KB).

Artifact written to `D:\neosager-data\artifacts\neosager_tables.json`.