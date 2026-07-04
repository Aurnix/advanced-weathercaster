# milestone2_report

## Headline: BSS vs station climatology (cell A: train stations, 2020-2024)

| target     |   climatology |   logreg |   persistence |   sager_cal |   sager_faithful |   zambretti_cal |
|:-----------|--------------:|---------:|--------------:|------------:|-----------------:|----------------:|
| pfall_12h  |         0.000 |    0.110 |        -0.644 |      -0.090 |          nan     |          -0.065 |
| pfall_24h  |         0.000 |    0.067 |        -0.775 |      -0.093 |          nan     |          -0.079 |
| pfall_6h   |         0.000 |    0.149 |        -1.017 |      -0.078 |          nan     |          -0.017 |
| precip_12h |         0.000 |    0.228 |        -0.179 |       0.128 |           -0.514 |          -0.065 |
| precip_24h |         0.000 |    0.144 |        -0.654 |       0.050 |           -0.614 |          -0.080 |
| precip_6h  |         0.000 |    0.320 |         0.105 |       0.209 |           -0.666 |          -0.058 |
| windup_12h |         0.000 |    0.344 |        -0.650 |       0.021 |           -1.046 |          -0.010 |
| windup_24h |         0.000 |    0.291 |        -1.108 |       0.011 |           -1.083 |          -0.013 |
| windup_6h  |         0.000 |    0.305 |        -0.357 |       0.017 |           -1.273 |          -0.006 |

## Categorical skill (Heidke / Peirce)

| cell                     | target   | model       |   brier |   bss |   auc |       n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:---------|:------------|--------:|------:|------:|--------:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | cond_12h | persistence |     nan |   nan |   nan | 3512322 |      nan |      nan |    0.278 |    0.271 |
| A_trainstation_testyears | cond_12h | zambretti   |     nan |   nan |   nan | 3501680 |      nan |      nan |    0.055 |    0.051 |
| A_trainstation_testyears | cond_12h | sager       |     nan |   nan |   nan | 3331362 |      nan |      nan |    0.146 |    0.159 |
| A_trainstation_testyears | cond_24h | persistence |     nan |   nan |   nan | 3512738 |      nan |      nan |    0.229 |    0.223 |
| A_trainstation_testyears | cond_24h | zambretti   |     nan |   nan |   nan | 3501781 |      nan |      nan |    0.037 |    0.034 |
| A_trainstation_testyears | cond_24h | sager       |     nan |   nan |   nan | 3331087 |      nan |      nan |    0.116 |    0.126 |
| C_teststation_testyears  | cond_12h | persistence |     nan |   nan |   nan |  577938 |      nan |      nan |    0.265 |    0.258 |
| C_teststation_testyears  | cond_12h | zambretti   |     nan |   nan |   nan |  575352 |      nan |      nan |    0.031 |    0.029 |
| C_teststation_testyears  | cond_12h | sager       |     nan |   nan |   nan |  553140 |      nan |      nan |    0.129 |    0.142 |
| C_teststation_testyears  | cond_24h | persistence |     nan |   nan |   nan |  577862 |      nan |      nan |    0.222 |    0.216 |
| C_teststation_testyears  | cond_24h | zambretti   |     nan |   nan |   nan |  575269 |      nan |      nan |    0.014 |    0.013 |
| C_teststation_testyears  | cond_24h | sager       |     nan |   nan |   nan |  553022 |      nan |      nan |    0.099 |    0.109 |
| B_teststation_trainyears | cond_12h | persistence |     nan |   nan |   nan | 2815764 |      nan |      nan |    0.202 |    0.188 |
| B_teststation_trainyears | cond_12h | zambretti   |     nan |   nan |   nan | 2780509 |      nan |      nan |    0.029 |    0.027 |
| B_teststation_trainyears | cond_12h | sager       |     nan |   nan |   nan | 1846315 |      nan |      nan |    0.134 |    0.149 |
| B_teststation_trainyears | cond_24h | persistence |     nan |   nan |   nan | 2827034 |      nan |      nan |    0.165 |    0.154 |
| B_teststation_trainyears | cond_24h | zambretti   |     nan |   nan |   nan | 2791089 |      nan |      nan |    0.010 |    0.009 |
| B_teststation_trainyears | cond_24h | sager       |     nan |   nan |   nan | 1851385 |      nan |      nan |    0.101 |    0.112 |

## Reliability (headline cell)

![](reports/figures/reliability_precip12_A_trainstation_testyears.png)

## All cells (full table)

| cell                     | target     | model          |   brier |    bss |   auc |       n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:-----------|:---------------|--------:|-------:|------:|--------:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | precip_6h  | climatology    |   0.183 |  0.000 | 0.660 | 3509914 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | persistence    |   0.164 |  0.105 | 0.715 | 3509914 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | zambretti_cal  |   0.194 | -0.058 | 0.567 | 3499315 |   -0.060 |   -0.056 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_cal      |   0.146 |  0.209 | 0.768 | 3328907 |    0.206 |    0.211 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | logreg         |   0.124 |  0.320 | 0.834 | 3509914 |    0.318 |    0.322 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_faithful |   0.307 | -0.666 | 0.677 | 3328907 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | climatology    |   0.214 |  0.000 | 0.663 | 3510655 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | persistence    |   0.253 | -0.179 | 0.662 | 3510655 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | zambretti_cal  |   0.228 | -0.065 | 0.574 | 3500119 |   -0.068 |   -0.063 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_cal      |   0.188 |  0.128 | 0.727 | 3329849 |    0.126 |    0.131 |      nan |      nan |
| A_trainstation_testyears | precip_12h | logreg         |   0.166 |  0.228 | 0.793 | 3510655 |    0.226 |    0.230 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_faithful |   0.326 | -0.514 | 0.654 | 3329849 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | climatology    |   0.228 |  0.000 | 0.674 | 3507943 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | persistence    |   0.377 | -0.654 | 0.624 | 3507943 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | zambretti_cal  |   0.246 | -0.080 | 0.576 | 3497603 |   -0.083 |   -0.077 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_cal      |   0.217 |  0.050 | 0.692 | 3327636 |    0.047 |    0.053 |      nan |      nan |
| A_trainstation_testyears | precip_24h | logreg         |   0.195 |  0.144 | 0.761 | 3507943 |    0.141 |    0.146 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_faithful |   0.368 | -0.614 | 0.633 | 3327636 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | climatology    |   0.187 |  0.000 | 0.577 | 3477936 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | persistence    |   0.253 | -0.357 | 0.500 | 3477936 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | zambretti_cal  |   0.188 | -0.006 | 0.561 | 3467542 |   -0.007 |   -0.006 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_cal      |   0.182 |  0.017 | 0.608 | 3320665 |    0.017 |    0.018 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | logreg         |   0.130 |  0.305 | 0.831 | 3477936 |    0.304 |    0.306 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_faithful |   0.420 | -1.273 | 0.496 | 3320665 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | climatology    |   0.233 |  0.000 | 0.574 | 3482719 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | persistence    |   0.384 | -0.650 | 0.500 | 3482719 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | zambretti_cal  |   0.235 | -0.010 | 0.551 | 3472348 |   -0.010 |   -0.009 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_cal      |   0.228 |  0.021 | 0.607 | 3324787 |    0.020 |    0.021 |      nan |      nan |
| A_trainstation_testyears | windup_12h | logreg         |   0.153 |  0.344 | 0.839 | 3482719 |    0.342 |    0.345 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_faithful |   0.475 | -1.046 | 0.485 | 3324787 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | climatology    |   0.245 |  0.000 | 0.576 | 3480732 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | persistence    |   0.517 | -1.108 | 0.500 | 3480732 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | zambretti_cal  |   0.249 | -0.013 | 0.543 | 3470579 |   -0.014 |   -0.013 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_cal      |   0.243 |  0.011 | 0.595 | 3323243 |    0.011 |    0.012 |      nan |      nan |
| A_trainstation_testyears | windup_24h | logreg         |   0.174 |  0.291 | 0.814 | 3480732 |    0.290 |    0.292 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_faithful |   0.511 | -1.083 | 0.493 | 3323243 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | climatology    |   0.106 |  0.000 | 0.771 | 3505228 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | persistence    |   0.214 | -1.017 | 0.682 | 3505228 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | zambretti_cal  |   0.108 | -0.017 | 0.682 | 3494966 |   -0.019 |   -0.016 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | sager_cal      |   0.114 | -0.078 | 0.654 | 3324989 |   -0.080 |   -0.076 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | logreg         |   0.090 |  0.149 | 0.842 | 3505228 |    0.147 |    0.150 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | climatology    |   0.174 |  0.000 | 0.719 | 3506269 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | persistence    |   0.286 | -0.644 | 0.610 | 3506269 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | zambretti_cal  |   0.185 | -0.065 | 0.627 | 3496075 |   -0.067 |   -0.064 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | sager_cal      |   0.190 | -0.090 | 0.620 | 3326199 |   -0.092 |   -0.087 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | logreg         |   0.155 |  0.110 | 0.780 | 3506269 |    0.108 |    0.111 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | climatology    |   0.215 |  0.000 | 0.701 | 3503019 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | persistence    |   0.381 | -0.775 | 0.579 | 3503019 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | zambretti_cal  |   0.232 | -0.079 | 0.623 | 3493163 |   -0.081 |   -0.077 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | sager_cal      |   0.235 | -0.093 | 0.615 | 3323747 |   -0.096 |   -0.091 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | logreg         |   0.200 |  0.067 | 0.746 | 3503019 |    0.066 |    0.069 |      nan |      nan |
| C_teststation_testyears  | precip_6h  | climatology    |   0.182 |  0.000 | 0.634 |  576854 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | persistence    |   0.159 |  0.125 | 0.711 |  576854 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | zambretti_cal  |   0.191 | -0.051 | 0.525 |  574443 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_cal      |   0.145 |  0.205 | 0.754 |  552289 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | logreg         |   0.125 |  0.312 | 0.817 |  576854 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_faithful |   0.324 | -0.771 | 0.660 |  552289 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | climatology    |   0.216 |  0.000 | 0.642 |  577242 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | persistence    |   0.249 | -0.151 | 0.656 |  577242 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | zambretti_cal  |   0.229 | -0.060 | 0.537 |  574764 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_cal      |   0.190 |  0.124 | 0.710 |  552610 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | logreg         |   0.170 |  0.213 | 0.771 |  577242 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_faithful |   0.343 | -0.579 | 0.636 |  552610 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | climatology    |   0.231 |  0.000 | 0.661 |  576647 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | persistence    |   0.376 | -0.626 | 0.617 |  576647 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | zambretti_cal  |   0.250 | -0.082 | 0.541 |  574191 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_cal      |   0.222 |  0.041 | 0.673 |  552080 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | logreg         |   0.204 |  0.118 | 0.735 |  576647 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_faithful |   0.384 | -0.658 | 0.615 |  552080 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | climatology    |   0.186 |  0.000 | 0.574 |  573293 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | persistence    |   0.250 | -0.349 | 0.500 |  573293 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | zambretti_cal  |   0.186 | -0.004 | 0.560 |  570908 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_cal      |   0.180 |  0.018 | 0.608 |  551209 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | logreg         |   0.130 |  0.298 | 0.828 |  573293 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_faithful |   0.420 | -1.294 | 0.498 |  551209 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | climatology    |   0.233 |  0.000 | 0.570 |  574380 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | persistence    |   0.382 | -0.641 | 0.500 |  574380 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | zambretti_cal  |   0.235 | -0.007 | 0.551 |  571908 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_cal      |   0.228 |  0.020 | 0.603 |  552172 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | logreg         |   0.157 |  0.328 | 0.832 |  574380 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_faithful |   0.473 | -1.036 | 0.488 |  552172 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | climatology    |   0.246 |  0.000 | 0.567 |  574107 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | persistence    |   0.518 | -1.106 | 0.500 |  574107 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | zambretti_cal  |   0.248 | -0.009 | 0.545 |  571647 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_cal      |   0.243 |  0.013 | 0.592 |  551941 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | logreg         |   0.177 |  0.281 | 0.810 |  574107 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_faithful |   0.508 | -1.061 | 0.497 |  551941 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | climatology    |   0.109 |  0.000 | 0.752 |  575982 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | persistence    |   0.211 | -0.937 | 0.688 |  575982 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | zambretti_cal  |   0.108 |  0.006 | 0.676 |  573651 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | sager_cal      |   0.115 | -0.055 | 0.663 |  551574 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | logreg         |   0.091 |  0.168 | 0.851 |  575982 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | climatology    |   0.178 |  0.000 | 0.704 |  576435 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | persistence    |   0.288 | -0.617 | 0.609 |  576435 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | zambretti_cal  |   0.187 | -0.052 | 0.621 |  574053 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | sager_cal      |   0.191 | -0.069 | 0.627 |  551981 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | logreg         |   0.151 |  0.149 | 0.801 |  576435 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | climatology    |   0.217 |  0.000 | 0.692 |  575659 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | persistence    |   0.382 | -0.757 | 0.580 |  575659 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | zambretti_cal  |   0.233 | -0.071 | 0.621 |  573369 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | sager_cal      |   0.234 | -0.073 | 0.625 |  551362 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | logreg         |   0.197 |  0.093 | 0.757 |  575659 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | climatology    |   0.166 |  0.000 | 0.645 | 2805176 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | persistence    |   0.166 | -0.004 | 0.648 | 2805176 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | zambretti_cal  |   0.175 | -0.056 | 0.542 | 2772672 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_cal      |   0.133 |  0.210 | 0.766 | 1840992 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | logreg         |   0.129 |  0.220 | 0.787 | 2805176 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_faithful |   0.316 | -0.886 | 0.669 | 1840992 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | climatology    |   0.202 |  0.000 | 0.649 | 2803090 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | persistence    |   0.249 | -0.236 | 0.610 | 2803090 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | zambretti_cal  |   0.215 | -0.067 | 0.550 | 2770668 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_cal      |   0.176 |  0.133 | 0.723 | 1840140 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | logreg         |   0.172 |  0.149 | 0.748 | 2803090 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_faithful |   0.328 | -0.617 | 0.648 | 1840140 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | climatology    |   0.225 |  0.000 | 0.664 | 2789475 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | persistence    |   0.372 | -0.650 | 0.581 | 2789475 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | zambretti_cal  |   0.246 | -0.092 | 0.550 | 2763128 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_cal      |   0.215 |  0.050 | 0.684 | 1838591 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | logreg         |   0.209 |  0.074 | 0.715 | 2789475 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_faithful |   0.362 | -0.604 | 0.626 | 1838591 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | climatology    |   0.177 |  0.000 | 0.580 | 2794107 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | persistence    |   0.234 | -0.325 | 0.500 | 2794107 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | zambretti_cal  |   0.178 | -0.011 | 0.542 | 2762693 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_cal      |   0.171 |  0.011 | 0.603 | 1838014 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | logreg         |   0.140 |  0.204 | 0.782 | 2794107 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_faithful |   0.416 | -1.402 | 0.492 | 1838014 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | climatology    |   0.229 |  0.000 | 0.573 | 2792235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | persistence    |   0.367 | -0.606 | 0.500 | 2792235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | zambretti_cal  |   0.231 | -0.011 | 0.539 | 2760918 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_cal      |   0.224 |  0.014 | 0.597 | 1836973 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | logreg         |   0.173 |  0.242 | 0.792 | 2792235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_faithful |   0.467 | -1.059 | 0.486 | 1836973 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | climatology    |   0.246 |  0.000 | 0.572 | 2785244 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | persistence    |   0.507 | -1.062 | 0.500 | 2785244 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | zambretti_cal  |   0.249 | -0.012 | 0.537 | 2756755 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_cal      |   0.244 |  0.009 | 0.587 | 1837234 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | logreg         |   0.196 |  0.200 | 0.762 | 2785244 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_faithful |   0.501 | -1.037 | 0.498 | 1837234 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | climatology    |   0.103 |  0.000 | 0.756 | 2785346 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | persistence    |   0.212 | -1.061 | 0.679 | 2785346 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | zambretti_cal  |   0.104 | -0.012 | 0.667 | 2757540 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | sager_cal      |   0.108 | -0.049 | 0.674 | 1833288 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | logreg         |   0.089 |  0.134 | 0.837 | 2785346 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | climatology    |   0.174 |  0.000 | 0.705 | 2783799 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | persistence    |   0.280 | -0.609 | 0.612 | 2783799 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | zambretti_cal  |   0.183 | -0.052 | 0.620 | 2755569 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | sager_cal      |   0.183 | -0.054 | 0.643 | 1831954 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | logreg         |   0.154 |  0.117 | 0.787 | 2783799 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | climatology    |   0.217 |  0.000 | 0.687 | 2777328 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | persistence    |   0.375 | -0.730 | 0.582 | 2777328 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | zambretti_cal  |   0.230 | -0.061 | 0.625 | 2753189 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | sager_cal      |   0.230 | -0.059 | 0.634 | 1832827 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | logreg         |   0.198 |  0.087 | 0.754 | 2777328 |  nan     |  nan     |      nan |      nan |