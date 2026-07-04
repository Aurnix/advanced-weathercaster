# gbm_fullscale_report

## GBM vs calibrated Sager — BSS vs climatology (cell A, 2020-2024)

| target     |   bss |   bss_val |   auc |   bss_minus_sager |   diff_lo |   diff_hi |       n |
|:-----------|------:|----------:|------:|------------------:|----------:|----------:|--------:|
| precip_6h  | 0.377 |     0.385 | 0.875 |             0.169 |     0.167 |     0.170 | 3509914 |
| precip_12h | 0.311 |     0.320 | 0.846 |             0.183 |     0.181 |     0.184 | 3510655 |
| precip_24h | 0.243 |     0.255 | 0.822 |             0.194 |     0.191 |     0.196 | 3507943 |
| windup_6h  | 0.383 |     0.383 | 0.868 |             0.365 |     0.364 |     0.366 | 3477936 |
| windup_12h | 0.411 |     0.409 | 0.871 |             0.390 |     0.389 |     0.391 | 3482719 |
| windup_24h | 0.359 |     0.362 | 0.850 |             0.348 |     0.347 |     0.349 | 3480732 |
| pfall_6h   | 0.481 |     0.482 | 0.949 |             0.559 |     0.555 |     0.563 | 3505228 |
| pfall_12h  | 0.401 |     0.408 | 0.906 |             0.491 |     0.487 |     0.494 | 3506269 |
| pfall_24h  | 0.243 |     0.255 | 0.834 |             0.336 |     0.333 |     0.339 | 3503019 |

`bss_minus_sager` is the paired block-bootstrap difference; the CI excludes 0 when the GBM's edge over Sager is significant.

## Conditions (Heidke/Peirce)

| cell                     | target   | model   |   bss |   bss_val |   auc |       n |   bss_minus_sager |   diff_lo |   diff_hi |   heidke |   peirce |
|:-------------------------|:---------|:--------|------:|----------:|------:|--------:|------------------:|----------:|----------:|---------:|---------:|
| A_trainstation_testyears | cond_12h | gbm     |   nan |       nan |   nan | 3512322 |               nan |       nan |       nan |    0.348 |    0.326 |
| C_teststation_testyears  | cond_12h | gbm     |   nan |       nan |   nan |  577938 |               nan |       nan |       nan |    0.306 |    0.282 |
| B_teststation_trainyears | cond_12h | gbm     |   nan |       nan |   nan | 2815764 |               nan |       nan |       nan |    0.289 |    0.267 |
| A_trainstation_testyears | cond_24h | gbm     |   nan |       nan |   nan | 3512738 |               nan |       nan |       nan |    0.284 |    0.261 |
| C_teststation_testyears  | cond_24h | gbm     |   nan |       nan |   nan |  577862 |               nan |       nan |       nan |    0.242 |    0.218 |
| B_teststation_trainyears | cond_24h | gbm     |   nan |       nan |   nan | 2827034 |               nan |       nan |       nan |    0.235 |    0.213 |

## All cells

| cell                     | target     | model   |   bss |   bss_val |   auc |       n |   bss_minus_sager |   diff_lo |   diff_hi |   heidke |   peirce |
|:-------------------------|:-----------|:--------|------:|----------:|------:|--------:|------------------:|----------:|----------:|---------:|---------:|
| A_trainstation_testyears | precip_6h  | gbm     | 0.377 |     0.385 | 0.875 | 3509914 |             0.169 |     0.167 |     0.170 |      nan |      nan |
| C_teststation_testyears  | precip_6h  | gbm     | 0.347 |     0.385 | 0.850 |  576854 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | gbm     | 0.288 |     0.385 | 0.842 | 2805176 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | gbm     | 0.311 |     0.320 | 0.846 | 3510655 |             0.183 |     0.181 |     0.184 |      nan |      nan |
| C_teststation_testyears  | precip_12h | gbm     | 0.263 |     0.320 | 0.813 |  577242 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | gbm     | 0.232 |     0.320 | 0.812 | 2803090 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | gbm     | 0.243 |     0.255 | 0.822 | 3507943 |             0.194 |     0.191 |     0.196 |      nan |      nan |
| C_teststation_testyears  | precip_24h | gbm     | 0.183 |     0.255 | 0.783 |  576647 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | gbm     | 0.174 |     0.255 | 0.788 | 2789475 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | gbm     | 0.383 |     0.383 | 0.868 | 3477936 |             0.365 |     0.364 |     0.366 |      nan |      nan |
| C_teststation_testyears  | windup_6h  | gbm     | 0.351 |     0.383 | 0.853 |  573293 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | gbm     | 0.258 |     0.383 | 0.814 | 2794107 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | gbm     | 0.411 |     0.409 | 0.871 | 3482719 |             0.390 |     0.389 |     0.391 |      nan |      nan |
| C_teststation_testyears  | windup_12h | gbm     | 0.376 |     0.409 | 0.856 |  574380 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | gbm     | 0.295 |     0.409 | 0.821 | 2792235 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | gbm     | 0.359 |     0.362 | 0.850 | 3480732 |             0.348 |     0.347 |     0.349 |      nan |      nan |
| C_teststation_testyears  | windup_24h | gbm     | 0.330 |     0.362 | 0.835 |  574107 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | gbm     | 0.259 |     0.362 | 0.798 | 2785244 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | gbm     | 0.481 |     0.482 | 0.949 | 3505228 |             0.559 |     0.555 |     0.563 |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | gbm     | 0.418 |     0.482 | 0.934 |  575982 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | gbm     | 0.392 |     0.482 | 0.931 | 2785346 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | gbm     | 0.401 |     0.408 | 0.906 | 3506269 |             0.491 |     0.487 |     0.494 |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | gbm     | 0.360 |     0.408 | 0.891 |  576435 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | gbm     | 0.333 |     0.408 | 0.884 | 2783799 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | gbm     | 0.243 |     0.255 | 0.834 | 3503019 |             0.336 |     0.333 |     0.339 |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | gbm     | 0.218 |     0.255 | 0.820 |  575659 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | gbm     | 0.217 |     0.255 | 0.819 | 2777328 |           nan     |   nan     |   nan     |      nan |      nan |

## Reliability

![](reports/figures/reliability_gbm_precip_12h.png)