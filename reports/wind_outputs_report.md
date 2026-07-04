# wind_outputs_report

## Wind-output predictands (cell A, Heidke/Peirce)

| target       | model       |   heidke |   peirce |       n |
|:-------------|:------------|---------:|---------:|--------:|
| windband_6h  | gbm         |    0.514 |    0.482 | 3485504 |
| windband_6h  | persistence |    0.307 |    0.320 | 3472839 |
| windband_12h | gbm         |    0.485 |    0.469 | 3491840 |
| windband_12h | persistence |    0.184 |    0.198 | 3477741 |
| windband_12h | sager_ring  |    0.128 |    0.149 | 3320514 |
| windband_24h | gbm         |    0.385 |    0.354 | 3478108 |
| windband_24h | persistence |    0.086 |    0.105 | 3464525 |
| windband_24h | sager_ring  |    0.124 |    0.145 | 3309310 |
| winddir_6h   | gbm         |    0.262 |    0.240 | 2817434 |
| winddir_6h   | persistence |    0.000 |    0.000 | 2817434 |
| winddir_12h  | gbm         |    0.281 |    0.274 | 2815035 |
| winddir_12h  | persistence |    0.000 |    0.000 | 2815035 |
| winddir_12h  | sager_ring  |    0.007 |    0.006 | 2790290 |
| winddir_24h  | gbm         |    0.226 |    0.220 | 2815487 |
| winddir_24h  | persistence |    0.000 |    0.000 | 2815487 |
| winddir_24h  | sager_ring  |    0.005 |    0.004 | 2790344 |

Strong-or-gale recall at 12h: 0.28 (n=231218)

windband classes: calm/light/moderate-fresh/strong/gale (max within window). winddir classes: steady/veer/veer-sharp/back/back-sharp/calm-variable (at lead vs now).

Sager ring mappings are committed in eval/run_wind.py's docstring.