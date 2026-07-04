# distill_52station_report

## Skill retained through distillation (cell A, BSS vs climatology)

| target     |   bss_gbm |   bss_additive_float |   bss_quantized_int8 |
|:-----------|----------:|---------------------:|---------------------:|
| precip_6h  |     0.397 |                0.338 |                0.337 |
| precip_12h |     0.337 |                0.252 |                0.252 |
| precip_24h |     0.278 |                0.173 |                0.173 |
| windup_6h  |     0.387 |                0.275 |                0.274 |
| windup_12h |     0.416 |                0.293 |                0.292 |
| windup_24h |     0.366 |                0.272 |                0.272 |
| pfall_6h   |     0.493 |                0.209 |                0.209 |
| pfall_12h  |     0.416 |                0.151 |                0.151 |
| pfall_24h  |     0.263 |                0.074 |                0.074 |

**Artifact size: 2515 bytes (2.46 KB) for 9 heads + bin edges** (budget: 32-64 KB).

Artifact written to `D:\neosager-data\artifacts\neosager_tables.json`.