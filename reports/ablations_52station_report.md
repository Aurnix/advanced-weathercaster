# ablations_52station_report

## Feature tiers (what manual inputs buy)

| target     |   full_manual |   plus_auto |   pressure_only |
|:-----------|--------------:|------------:|----------------:|
| precip_12h |         0.322 |       0.152 |           0.117 |
| precip_24h |         0.250 |       0.127 |           0.097 |
| precip_6h  |         0.391 |       0.163 |           0.123 |

## Missing-input robustness

| target     |   mask_0pct |   mask_100pct |   mask_50pct |
|:-----------|------------:|--------------:|-------------:|
| pfall_12h  |       0.409 |         0.366 |        0.387 |
| precip_12h |       0.322 |         0.140 |        0.232 |
| precip_24h |       0.250 |         0.118 |        0.183 |
| precip_6h  |       0.391 |         0.150 |        0.272 |
| windup_12h |       0.402 |         0.168 |        0.285 |

## Tide correction on/off

| target     |   off |    on |
|:-----------|------:|------:|
| pfall_12h  | 0.456 | 0.409 |
| pfall_24h  | 0.271 | 0.242 |
| pfall_6h   | 0.534 | 0.493 |
| precip_12h | 0.324 | 0.322 |
| precip_24h | 0.251 | 0.250 |
| precip_6h  | 0.393 | 0.391 |
