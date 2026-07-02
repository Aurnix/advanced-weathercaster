# smoke3_report

## Headline: BSS vs station climatology (cell A: train stations, 2020-2024)

| target     |   climatology |   logreg |   persistence |   sager_cal |   sager_faithful |   zambretti_cal |
|:-----------|--------------:|---------:|--------------:|------------:|-----------------:|----------------:|
| pfall_12h  |         0.000 |    0.395 |        -0.955 |      -0.630 |          nan     |          -0.386 |
| pfall_24h  |         0.000 |    0.080 |        -1.650 |      -0.863 |          nan     |          -0.619 |
| pfall_6h   |         0.000 |    0.480 |        -0.512 |      -0.360 |          nan     |          -0.113 |
| precip_12h |         0.000 |    0.219 |        -0.152 |       0.079 |           -0.792 |          -0.020 |
| precip_24h |         0.000 |    0.150 |        -0.581 |       0.007 |           -0.824 |          -0.038 |
| precip_6h  |         0.000 |    0.292 |         0.084 |       0.141 |           -1.075 |          -0.007 |
| windup_12h |         0.000 |    0.325 |        -0.631 |       0.013 |           -0.802 |           0.014 |
| windup_24h |         0.000 |    0.284 |        -1.081 |       0.007 |           -0.936 |           0.001 |
| windup_6h  |         0.000 |    0.295 |        -0.347 |       0.015 |           -1.104 |           0.012 |

## Categorical skill (Heidke / Peirce)

| cell                     | target   | model       |   brier |   bss |   auc |    n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:---------|:------------|--------:|------:|------:|-----:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | cond_12h | persistence |     nan |   nan |   nan | 5849 |      nan |      nan |    0.158 |    0.158 |
| A_trainstation_testyears | cond_12h | zambretti   |     nan |   nan |   nan | 5848 |      nan |      nan |    0.016 |    0.016 |
| A_trainstation_testyears | cond_12h | sager       |     nan |   nan |   nan | 5649 |      nan |      nan |    0.062 |    0.072 |
| A_trainstation_testyears | cond_24h | persistence |     nan |   nan |   nan | 5841 |      nan |      nan |    0.175 |    0.174 |
| A_trainstation_testyears | cond_24h | zambretti   |     nan |   nan |   nan | 5840 |      nan |      nan |    0.000 |    0.000 |
| A_trainstation_testyears | cond_24h | sager       |     nan |   nan |   nan | 5641 |      nan |      nan |    0.069 |    0.081 |
| C_teststation_testyears  | cond_12h | persistence |     nan |   nan |   nan | 2925 |      nan |      nan |    0.241 |    0.242 |
| C_teststation_testyears  | cond_12h | zambretti   |     nan |   nan |   nan | 2925 |      nan |      nan |    0.067 |    0.072 |
| C_teststation_testyears  | cond_12h | sager       |     nan |   nan |   nan | 2803 |      nan |      nan |    0.118 |    0.140 |
| C_teststation_testyears  | cond_24h | persistence |     nan |   nan |   nan | 2921 |      nan |      nan |    0.189 |    0.190 |
| C_teststation_testyears  | cond_24h | zambretti   |     nan |   nan |   nan | 2921 |      nan |      nan |    0.057 |    0.060 |
| C_teststation_testyears  | cond_24h | sager       |     nan |   nan |   nan | 2799 |      nan |      nan |    0.075 |    0.089 |
| B_teststation_trainyears | cond_12h | persistence |     nan |   nan |   nan | 5840 |      nan |      nan |    0.173 |    0.194 |
| B_teststation_trainyears | cond_12h | zambretti   |     nan |   nan |   nan | 5839 |      nan |      nan |    0.037 |    0.044 |
| B_teststation_trainyears | cond_12h | sager       |     nan |   nan |   nan | 3959 |      nan |      nan |    0.120 |    0.163 |
| B_teststation_trainyears | cond_24h | persistence |     nan |   nan |   nan | 5840 |      nan |      nan |    0.119 |    0.132 |
| B_teststation_trainyears | cond_24h | zambretti   |     nan |   nan |   nan | 5839 |      nan |      nan |    0.035 |    0.042 |
| B_teststation_trainyears | cond_24h | sager       |     nan |   nan |   nan | 3959 |      nan |      nan |    0.082 |    0.112 |

## Reliability (headline cell)

![](reports/figures/reliability_precip12_A_trainstation_testyears.png)

## All cells (full table)

| cell                     | target     | model          |   brier |    bss |   auc |    n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:-----------|:---------------|--------:|-------:|------:|-----:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | precip_6h  | climatology    |   0.167 |  0.000 | 0.589 | 5851 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | persistence    |   0.153 |  0.084 | 0.680 | 5851 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | zambretti_cal  |   0.168 | -0.007 | 0.568 | 5850 |   -0.039 |    0.025 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_cal      |   0.144 |  0.141 | 0.702 | 5651 |    0.102 |    0.179 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | logreg         |   0.118 |  0.292 | 0.821 | 5851 |    0.249 |    0.334 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_faithful |   0.347 | -1.075 | 0.624 | 5651 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | climatology    |   0.208 |  0.000 | 0.597 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | persistence    |   0.240 | -0.152 | 0.629 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | zambretti_cal  |   0.212 | -0.020 | 0.565 | 5846 |   -0.066 |    0.024 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_cal      |   0.192 |  0.079 | 0.662 | 5647 |    0.031 |    0.124 |      nan |      nan |
| A_trainstation_testyears | precip_12h | logreg         |   0.163 |  0.219 | 0.785 | 5847 |    0.175 |    0.265 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_faithful |   0.374 | -0.792 | 0.594 | 5647 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | climatology    |   0.234 |  0.000 | 0.631 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | persistence    |   0.369 | -0.581 | 0.591 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | zambretti_cal  |   0.242 | -0.038 | 0.575 | 5838 |   -0.097 |    0.023 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_cal      |   0.232 |  0.007 | 0.623 | 5639 |   -0.057 |    0.069 |      nan |      nan |
| A_trainstation_testyears | precip_24h | logreg         |   0.198 |  0.150 | 0.755 | 5839 |    0.104 |    0.207 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_faithful |   0.427 | -0.824 | 0.562 | 5639 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | climatology    |   0.190 |  0.000 | 0.542 | 5851 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | persistence    |   0.256 | -0.347 | 0.500 | 5851 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | zambretti_cal  |   0.187 |  0.012 | 0.567 | 5850 |    0.003 |    0.021 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_cal      |   0.180 |  0.015 | 0.582 | 5651 |    0.007 |    0.024 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | logreg         |   0.134 |  0.295 | 0.832 | 5851 |    0.271 |    0.322 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_faithful |   0.385 | -1.104 | 0.529 | 5651 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | climatology    |   0.237 |  0.000 | 0.538 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | persistence    |   0.386 | -0.631 | 0.500 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | zambretti_cal  |   0.234 |  0.014 | 0.561 | 5846 |    0.004 |    0.024 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_cal      |   0.231 |  0.013 | 0.567 | 5647 |    0.005 |    0.022 |      nan |      nan |
| A_trainstation_testyears | windup_12h | logreg         |   0.160 |  0.325 | 0.834 | 5847 |    0.293 |    0.361 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_faithful |   0.421 | -0.802 | 0.535 | 5647 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | climatology    |   0.248 |  0.000 | 0.557 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | persistence    |   0.516 | -1.081 | 0.500 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | zambretti_cal  |   0.248 |  0.001 | 0.539 | 5838 |   -0.011 |    0.012 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_cal      |   0.247 |  0.007 | 0.554 | 5639 |   -0.008 |    0.021 |      nan |      nan |
| A_trainstation_testyears | windup_24h | logreg         |   0.178 |  0.284 | 0.813 | 5839 |    0.256 |    0.313 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_faithful |   0.481 | -0.936 | 0.520 | 5639 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | climatology    |   0.136 |  0.000 | 0.832 | 5849 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | persistence    |   0.206 | -0.512 | 0.709 | 5849 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | zambretti_cal  |   0.152 | -0.113 | 0.734 | 5848 |   -0.165 |   -0.076 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | sager_cal      |   0.184 | -0.360 | 0.627 | 5649 |   -0.417 |   -0.322 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | logreg         |   0.071 |  0.480 | 0.955 | 5849 |    0.449 |    0.513 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | climatology    |   0.135 |  0.000 | 0.848 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | persistence    |   0.265 | -0.955 | 0.661 | 5847 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | zambretti_cal  |   0.188 | -0.386 | 0.709 | 5846 |   -0.468 |   -0.330 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | sager_cal      |   0.221 | -0.630 | 0.591 | 5647 |   -0.707 |   -0.562 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | logreg         |   0.082 |  0.395 | 0.937 | 5847 |    0.344 |    0.434 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | climatology    |   0.132 |  0.000 | 0.870 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | persistence    |   0.351 | -1.650 | 0.633 | 5839 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | zambretti_cal  |   0.214 | -0.619 | 0.704 | 5838 |   -0.760 |   -0.501 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | sager_cal      |   0.246 | -0.863 | 0.585 | 5639 |   -1.064 |   -0.676 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | logreg         |   0.122 |  0.080 | 0.894 | 5839 |    0.038 |    0.120 |      nan |      nan |
| C_teststation_testyears  | precip_6h  | climatology    |   0.241 |  0.000 | 0.519 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | persistence    |   0.191 |  0.206 | 0.744 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | zambretti_cal  |   0.251 | -0.044 | 0.481 | 2904 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_cal      |   0.207 |  0.147 | 0.717 | 2804 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | logreg         |   0.150 |  0.379 | 0.825 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_faithful |   0.327 | -0.346 | 0.696 | 2804 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | climatology    |   0.262 |  0.000 | 0.535 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | persistence    |   0.285 | -0.087 | 0.692 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | zambretti_cal  |   0.271 | -0.036 | 0.512 | 2902 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_cal      |   0.228 |  0.133 | 0.703 | 2802 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | logreg         |   0.182 |  0.308 | 0.796 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_faithful |   0.326 | -0.241 | 0.677 | 2802 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | climatology    |   0.254 |  0.000 | 0.565 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | persistence    |   0.409 | -0.608 | 0.653 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | zambretti_cal  |   0.263 | -0.036 | 0.530 | 2898 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_cal      |   0.228 |  0.101 | 0.688 | 2798 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | logreg         |   0.191 |  0.250 | 0.776 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_faithful |   0.332 | -0.310 | 0.669 | 2798 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | climatology    |   0.195 |  0.000 | 0.503 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | persistence    |   0.260 | -0.339 | 0.500 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | zambretti_cal  |   0.196 | -0.003 | 0.525 | 2904 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_cal      |   0.191 |  0.012 | 0.565 | 2804 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | logreg         |   0.199 | -0.023 | 0.839 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_faithful |   0.474 | -1.460 | 0.514 | 2804 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | climatology    |   0.232 |  0.000 | 0.513 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | persistence    |   0.359 | -0.548 | 0.500 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | zambretti_cal  |   0.235 | -0.014 | 0.518 | 2902 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_cal      |   0.230 |  0.000 | 0.525 | 2802 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | logreg         |   0.216 |  0.069 | 0.820 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_faithful |   0.473 | -1.058 | 0.519 | 2802 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | climatology    |   0.251 |  0.000 | 0.511 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | persistence    |   0.468 | -0.862 | 0.500 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | zambretti_cal  |   0.254 | -0.012 | 0.511 | 2898 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_cal      |   0.254 | -0.015 | 0.508 | 2798 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | logreg         |   0.243 |  0.032 | 0.789 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_faithful |   0.495 | -0.982 | 0.502 | 2798 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | climatology    |   0.085 |  0.000 | 0.681 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | persistence    |   0.244 | -1.881 | 0.734 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | zambretti_cal  |   0.110 | -0.288 | 0.668 | 2904 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | sager_cal      |   0.101 | -0.183 | 0.698 | 2804 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | logreg         |   0.748 | -7.816 | 0.418 | 2926 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | climatology    |   0.180 |  0.000 | 0.608 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | persistence    |   0.286 | -0.592 | 0.640 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | zambretti_cal  |   0.198 | -0.098 | 0.570 | 2902 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | sager_cal      |   0.186 | -0.030 | 0.577 | 2802 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | logreg         |   0.632 | -2.516 | 0.475 | 2924 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | climatology    |   0.239 |  0.000 | 0.560 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | persistence    |   0.357 | -0.496 | 0.606 | 2920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | zambretti_cal  |   0.259 | -0.083 | 0.526 | 2898 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | sager_cal      |   0.241 | -0.006 | 0.559 | 2798 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | logreg         |   0.499 | -1.091 | 0.598 | 2920 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | climatology    |   0.187 |  0.000 | 0.632 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | persistence    |   0.188 | -0.007 | 0.665 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | zambretti_cal  |   0.201 | -0.077 | 0.493 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_cal      |   0.182 |  0.044 | 0.680 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | logreg         |   0.155 |  0.171 | 0.754 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_faithful |   0.388 | -1.041 | 0.657 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | climatology    |   0.217 |  0.000 | 0.634 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | persistence    |   0.271 | -0.246 | 0.629 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | zambretti_cal  |   0.236 | -0.087 | 0.506 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_cal      |   0.215 |  0.018 | 0.663 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | logreg         |   0.194 |  0.106 | 0.730 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_faithful |   0.378 | -0.732 | 0.640 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | climatology    |   0.233 |  0.000 | 0.644 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | persistence    |   0.397 | -0.700 | 0.596 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | zambretti_cal  |   0.259 | -0.109 | 0.495 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_cal      |   0.237 | -0.018 | 0.632 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | logreg         |   0.217 |  0.070 | 0.708 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_faithful |   0.376 | -0.617 | 0.624 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | climatology    |   0.172 |  0.000 | 0.524 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | persistence    |   0.221 | -0.285 | 0.500 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | zambretti_cal  |   0.174 | -0.013 | 0.528 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_cal      |   0.175 | -0.016 | 0.551 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | logreg         |   0.240 | -0.399 | 0.743 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_faithful |   0.491 | -1.845 | 0.501 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | climatology    |   0.217 |  0.000 | 0.529 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | persistence    |   0.320 | -0.473 | 0.500 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | zambretti_cal  |   0.223 | -0.027 | 0.530 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_cal      |   0.223 | -0.025 | 0.532 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | logreg         |   0.249 | -0.147 | 0.735 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_faithful |   0.492 | -1.263 | 0.503 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | climatology    |   0.242 |  0.000 | 0.532 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | persistence    |   0.418 | -0.726 | 0.500 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | zambretti_cal  |   0.255 | -0.050 | 0.517 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_cal      |   0.253 | -0.042 | 0.525 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | logreg         |   0.284 | -0.170 | 0.702 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_faithful |   0.494 | -1.034 | 0.504 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | climatology    |   0.081 |  0.000 | 0.661 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | persistence    |   0.184 | -1.263 | 0.783 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | zambretti_cal  |   0.096 | -0.184 | 0.718 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | sager_cal      |   0.099 | -0.206 | 0.708 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | logreg         |   0.729 | -7.972 | 0.473 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | climatology    |   0.174 |  0.000 | 0.598 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | persistence    |   0.224 | -0.288 | 0.683 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | zambretti_cal  |   0.186 | -0.068 | 0.585 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | sager_cal      |   0.179 | -0.025 | 0.609 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | logreg         |   0.621 | -2.566 | 0.485 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | climatology    |   0.235 |  0.000 | 0.559 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | persistence    |   0.325 | -0.384 | 0.619 | 5840 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | zambretti_cal  |   0.255 | -0.088 | 0.517 | 5820 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | sager_cal      |   0.234 | -0.000 | 0.578 | 3959 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | logreg         |   0.507 | -1.160 | 0.577 | 5840 |  nan     |  nan     |      nan |      nan |