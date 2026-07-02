# gbm_52station_report

## GBM vs calibrated Sager — BSS vs climatology (cell A, 2020-2024)

| target     |   bss |   bss_val |   auc |   bss_minus_sager |   diff_lo |   diff_hi |      n |
|:-----------|------:|----------:|------:|------------------:|----------:|----------:|-------:|
| precip_6h  | 0.391 |     0.397 | 0.878 |             0.179 |     0.175 |     0.183 | 669057 |
| precip_12h | 0.322 |     0.331 | 0.848 |             0.191 |     0.186 |     0.195 | 669382 |
| precip_24h | 0.250 |     0.264 | 0.824 |             0.197 |     0.191 |     0.202 | 668829 |
| windup_6h  | 0.376 |     0.379 | 0.865 |             0.362 |     0.359 |     0.365 | 661937 |
| windup_12h | 0.402 |     0.406 | 0.869 |             0.387 |     0.384 |     0.390 | 663278 |
| windup_24h | 0.356 |     0.363 | 0.850 |             0.349 |     0.346 |     0.353 | 662910 |
| pfall_6h   | 0.493 |     0.489 | 0.953 |             0.591 |     0.582 |     0.598 | 667575 |
| pfall_12h  | 0.409 |     0.415 | 0.912 |             0.520 |     0.512 |     0.527 | 668217 |
| pfall_24h  | 0.242 |     0.253 | 0.840 |             0.357 |     0.350 |     0.364 | 667597 |

`bss_minus_sager` is the paired block-bootstrap difference; the CI excludes 0 when the GBM's edge over Sager is significant.

## Conditions (Heidke/Peirce)

| cell                     | target   | model   |   bss |   bss_val |   auc |      n |   bss_minus_sager |   diff_lo |   diff_hi |   heidke |   peirce |
|:-------------------------|:---------|:--------|------:|----------:|------:|-------:|------------------:|----------:|----------:|---------:|---------:|
| A_trainstation_testyears | cond_12h | gbm     |   nan |       nan |   nan | 670280 |               nan |       nan |       nan |    0.355 |    0.336 |
| C_teststation_testyears  | cond_12h | gbm     |   nan |       nan |   nan |  90276 |               nan |       nan |       nan |    0.307 |    0.294 |
| B_teststation_trainyears | cond_12h | gbm     |   nan |       nan |   nan | 440463 |               nan |       nan |       nan |    0.296 |    0.284 |
| A_trainstation_testyears | cond_24h | gbm     |   nan |       nan |   nan | 670545 |               nan |       nan |       nan |    0.294 |    0.275 |
| C_teststation_testyears  | cond_24h | gbm     |   nan |       nan |   nan |  90265 |               nan |       nan |       nan |    0.254 |    0.239 |
| B_teststation_trainyears | cond_24h | gbm     |   nan |       nan |   nan | 442262 |               nan |       nan |       nan |    0.259 |    0.245 |

## All cells

| cell                     | target     | model   |   bss |   bss_val |   auc |      n |   bss_minus_sager |   diff_lo |   diff_hi |   heidke |   peirce |
|:-------------------------|:-----------|:--------|------:|----------:|------:|-------:|------------------:|----------:|----------:|---------:|---------:|
| A_trainstation_testyears | precip_6h  | gbm     | 0.391 |     0.397 | 0.878 | 669057 |             0.179 |     0.175 |     0.183 |      nan |      nan |
| C_teststation_testyears  | precip_6h  | gbm     | 0.321 |     0.397 | 0.829 |  90203 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | gbm     | 0.239 |     0.397 | 0.823 | 440399 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | gbm     | 0.322 |     0.331 | 0.848 | 669382 |             0.191 |     0.186 |     0.195 |      nan |      nan |
| C_teststation_testyears  | precip_12h | gbm     | 0.233 |     0.331 | 0.784 |  90234 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | gbm     | 0.184 |     0.331 | 0.792 | 439628 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | gbm     | 0.250 |     0.264 | 0.824 | 668829 |             0.197 |     0.191 |     0.202 |      nan |      nan |
| C_teststation_testyears  | precip_24h | gbm     | 0.173 |     0.264 | 0.750 |  90199 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | gbm     | 0.126 |     0.264 | 0.763 | 438130 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | gbm     | 0.376 |     0.379 | 0.865 | 661937 |             0.362 |     0.359 |     0.365 |      nan |      nan |
| C_teststation_testyears  | windup_6h  | gbm     | 0.290 |     0.379 | 0.829 |  89920 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | gbm     | 0.213 |     0.379 | 0.791 | 437695 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | gbm     | 0.402 |     0.406 | 0.869 | 663278 |             0.387 |     0.384 |     0.390 |      nan |      nan |
| C_teststation_testyears  | windup_12h | gbm     | 0.317 |     0.406 | 0.833 |  89984 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | gbm     | 0.255 |     0.406 | 0.801 | 435791 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | gbm     | 0.356 |     0.363 | 0.850 | 662910 |             0.349 |     0.346 |     0.353 |      nan |      nan |
| C_teststation_testyears  | windup_24h | gbm     | 0.264 |     0.363 | 0.812 |  89952 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | gbm     | 0.210 |     0.363 | 0.773 | 434235 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | gbm     | 0.493 |     0.489 | 0.953 | 667575 |             0.591 |     0.582 |     0.598 |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | gbm     | 0.326 |     0.489 | 0.895 |  90142 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | gbm     | 0.342 |     0.489 | 0.898 | 435103 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | gbm     | 0.409 |     0.415 | 0.912 | 668217 |             0.520 |     0.512 |     0.527 |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | gbm     | 0.289 |     0.415 | 0.843 |  90188 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | gbm     | 0.296 |     0.415 | 0.846 | 431511 |           nan     |   nan     |   nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | gbm     | 0.242 |     0.253 | 0.840 | 667597 |             0.357 |     0.350 |     0.364 |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | gbm     | 0.157 |     0.253 | 0.765 |  90144 |           nan     |   nan     |   nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | gbm     | 0.176 |     0.253 | 0.774 | 432462 |           nan     |   nan     |   nan     |      nan |      nan |

## Reliability

![](reports/figures/reliability_gbm_precip_12h.png)