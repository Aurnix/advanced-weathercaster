# milestone1_report

## Headline: BSS vs station climatology (cell A: train stations, 2020-2024)

| target     |   climatology |   logreg |   persistence |   sager_cal |   sager_faithful |   zambretti_cal |
|:-----------|--------------:|---------:|--------------:|------------:|-----------------:|----------------:|
| pfall_12h  |         0.000 |    0.107 |        -0.608 |      -0.111 |          nan     |          -0.077 |
| pfall_24h  |         0.000 |    0.064 |        -0.762 |      -0.115 |          nan     |          -0.096 |
| pfall_6h   |         0.000 |    0.156 |        -0.918 |      -0.098 |          nan     |          -0.020 |
| precip_12h |         0.000 |    0.232 |        -0.185 |       0.131 |           -0.481 |          -0.058 |
| precip_24h |         0.000 |    0.149 |        -0.681 |       0.053 |           -0.610 |          -0.073 |
| precip_6h  |         0.000 |    0.327 |         0.109 |       0.212 |           -0.602 |          -0.051 |
| windup_12h |         0.000 |    0.324 |        -0.664 |       0.016 |           -1.039 |          -0.012 |
| windup_24h |         0.000 |    0.283 |        -1.138 |       0.007 |           -1.100 |          -0.016 |
| windup_6h  |         0.000 |    0.281 |        -0.362 |       0.014 |           -1.272 |          -0.008 |

## Categorical skill (Heidke / Peirce)

| cell                     | target   | model       |   brier |   bss |   auc |      n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:---------|:------------|--------:|------:|------:|-------:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | cond_12h | persistence |     nan |   nan |   nan | 670280 |      nan |      nan |    0.279 |    0.273 |
| A_trainstation_testyears | cond_12h | zambretti   |     nan |   nan |   nan | 667341 |      nan |      nan |    0.062 |    0.058 |
| A_trainstation_testyears | cond_12h | sager       |     nan |   nan |   nan | 632314 |      nan |      nan |    0.145 |    0.157 |
| A_trainstation_testyears | cond_24h | persistence |     nan |   nan |   nan | 670545 |      nan |      nan |    0.234 |    0.229 |
| A_trainstation_testyears | cond_24h | zambretti   |     nan |   nan |   nan | 667606 |      nan |      nan |    0.046 |    0.043 |
| A_trainstation_testyears | cond_24h | sager       |     nan |   nan |   nan | 632462 |      nan |      nan |    0.120 |    0.130 |
| C_teststation_testyears  | cond_12h | persistence |     nan |   nan |   nan |  90276 |      nan |      nan |    0.266 |    0.263 |
| C_teststation_testyears  | cond_12h | zambretti   |     nan |   nan |   nan |  90112 |      nan |      nan |    0.038 |    0.036 |
| C_teststation_testyears  | cond_12h | sager       |     nan |   nan |   nan |  87254 |      nan |      nan |    0.116 |    0.128 |
| C_teststation_testyears  | cond_24h | persistence |     nan |   nan |   nan |  90265 |      nan |      nan |    0.232 |    0.229 |
| C_teststation_testyears  | cond_24h | zambretti   |     nan |   nan |   nan |  90103 |      nan |      nan |    0.038 |    0.036 |
| C_teststation_testyears  | cond_24h | sager       |     nan |   nan |   nan |  87248 |      nan |      nan |    0.095 |    0.105 |
| B_teststation_trainyears | cond_12h | persistence |     nan |   nan |   nan | 440463 |      nan |      nan |    0.195 |    0.185 |
| B_teststation_trainyears | cond_12h | zambretti   |     nan |   nan |   nan | 435296 |      nan |      nan |    0.030 |    0.029 |
| B_teststation_trainyears | cond_12h | sager       |     nan |   nan |   nan | 288422 |      nan |      nan |    0.118 |    0.133 |
| B_teststation_trainyears | cond_24h | persistence |     nan |   nan |   nan | 442262 |      nan |      nan |    0.168 |    0.159 |
| B_teststation_trainyears | cond_24h | zambretti   |     nan |   nan |   nan | 437079 |      nan |      nan |    0.027 |    0.026 |
| B_teststation_trainyears | cond_24h | sager       |     nan |   nan |   nan | 289165 |      nan |      nan |    0.092 |    0.104 |

## Reliability (headline cell)

![](reports/figures/reliability_precip12_A_trainstation_testyears.png)

## All cells (full table)

| cell                     | target     | model          |   brier |    bss |   auc |      n |   bss_lo |   bss_hi |   heidke |   peirce |
|:-------------------------|:-----------|:---------------|--------:|-------:|------:|-------:|---------:|---------:|---------:|---------:|
| A_trainstation_testyears | precip_6h  | climatology    |   0.190 |  0.000 | 0.664 | 669057 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | persistence    |   0.169 |  0.109 | 0.721 | 669057 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_6h  | zambretti_cal  |   0.199 | -0.051 | 0.579 | 666221 |   -0.055 |   -0.046 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_cal      |   0.151 |  0.212 | 0.771 | 631162 |    0.207 |    0.217 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | logreg         |   0.128 |  0.327 | 0.833 | 669057 |    0.323 |    0.332 |      nan |      nan |
| A_trainstation_testyears | precip_6h  | sager_faithful |   0.307 | -0.602 | 0.682 | 631162 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | climatology    |   0.219 |  0.000 | 0.666 | 669382 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | persistence    |   0.260 | -0.185 | 0.668 | 669382 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_12h | zambretti_cal  |   0.232 | -0.058 | 0.585 | 666492 |   -0.063 |   -0.052 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_cal      |   0.192 |  0.131 | 0.730 | 631518 |    0.126 |    0.136 |      nan |      nan |
| A_trainstation_testyears | precip_12h | logreg         |   0.168 |  0.232 | 0.793 | 669382 |    0.227 |    0.237 |      nan |      nan |
| A_trainstation_testyears | precip_12h | sager_faithful |   0.326 | -0.481 | 0.658 | 631518 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | climatology    |   0.228 |  0.000 | 0.676 | 668829 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | persistence    |   0.384 | -0.681 | 0.629 | 668829 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | precip_24h | zambretti_cal  |   0.245 | -0.073 | 0.587 | 666074 |   -0.079 |   -0.065 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_cal      |   0.216 |  0.053 | 0.696 | 631213 |    0.047 |    0.060 |      nan |      nan |
| A_trainstation_testyears | precip_24h | logreg         |   0.194 |  0.149 | 0.765 | 668829 |    0.144 |    0.155 |      nan |      nan |
| A_trainstation_testyears | precip_24h | sager_faithful |   0.368 | -0.610 | 0.637 | 631213 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | climatology    |   0.188 |  0.000 | 0.579 | 661937 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | persistence    |   0.256 | -0.362 | 0.500 | 661937 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_6h  | zambretti_cal  |   0.189 | -0.008 | 0.555 | 659133 |   -0.009 |   -0.007 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_cal      |   0.183 |  0.014 | 0.601 | 629495 |    0.012 |    0.015 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | logreg         |   0.135 |  0.281 | 0.823 | 661937 |    0.277 |    0.285 |      nan |      nan |
| A_trainstation_testyears | windup_6h  | sager_faithful |   0.422 | -1.272 | 0.500 | 629495 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | climatology    |   0.234 |  0.000 | 0.578 | 663278 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | persistence    |   0.389 | -0.664 | 0.500 | 663278 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_12h | zambretti_cal  |   0.236 | -0.012 | 0.542 | 660425 |   -0.013 |   -0.011 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_cal      |   0.230 |  0.016 | 0.601 | 630557 |    0.014 |    0.017 |      nan |      nan |
| A_trainstation_testyears | windup_12h | logreg         |   0.158 |  0.324 | 0.832 | 663278 |    0.320 |    0.328 |      nan |      nan |
| A_trainstation_testyears | windup_12h | sager_faithful |   0.476 | -1.039 | 0.488 | 630557 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | climatology    |   0.245 |  0.000 | 0.580 | 662910 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | persistence    |   0.523 | -1.138 | 0.500 | 662910 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | windup_24h | zambretti_cal  |   0.249 | -0.016 | 0.537 | 660165 |   -0.017 |   -0.015 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_cal      |   0.243 |  0.007 | 0.592 | 630378 |    0.006 |    0.009 |      nan |      nan |
| A_trainstation_testyears | windup_24h | logreg         |   0.175 |  0.283 | 0.811 | 662910 |    0.280 |    0.287 |      nan |      nan |
| A_trainstation_testyears | windup_24h | sager_faithful |   0.514 | -1.100 | 0.493 | 630378 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | climatology    |   0.105 |  0.000 | 0.788 | 667575 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | persistence    |   0.202 | -0.918 | 0.695 | 667575 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | zambretti_cal  |   0.108 | -0.020 | 0.694 | 664824 |   -0.024 |   -0.016 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | sager_cal      |   0.116 | -0.098 | 0.656 | 629889 |   -0.102 |   -0.092 |      nan |      nan |
| A_trainstation_testyears | pfall_6h   | logreg         |   0.089 |  0.156 | 0.851 | 667575 |    0.152 |    0.160 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | climatology    |   0.169 |  0.000 | 0.737 | 668217 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | persistence    |   0.272 | -0.608 | 0.622 | 668217 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | zambretti_cal  |   0.182 | -0.077 | 0.634 | 665424 |   -0.081 |   -0.073 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | sager_cal      |   0.188 | -0.111 | 0.624 | 630539 |   -0.116 |   -0.105 |      nan |      nan |
| A_trainstation_testyears | pfall_12h  | logreg         |   0.151 |  0.107 | 0.790 | 668217 |    0.103 |    0.111 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | climatology    |   0.210 |  0.000 | 0.717 | 667597 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | persistence    |   0.370 | -0.762 | 0.587 | 667597 |  nan     |  nan     |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | zambretti_cal  |   0.230 | -0.096 | 0.627 | 664978 |   -0.101 |   -0.091 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | sager_cal      |   0.234 | -0.115 | 0.617 | 630225 |   -0.122 |   -0.109 |      nan |      nan |
| A_trainstation_testyears | pfall_24h  | logreg         |   0.196 |  0.064 | 0.756 | 667597 |    0.059 |    0.069 |      nan |      nan |
| C_teststation_testyears  | precip_6h  | climatology    |   0.203 |  0.000 | 0.597 |  90203 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | persistence    |   0.179 |  0.120 | 0.715 |  90203 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | zambretti_cal  |   0.211 | -0.038 | 0.525 |  90044 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_cal      |   0.165 |  0.193 | 0.742 |  87193 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | logreg         |   0.140 |  0.310 | 0.812 |  90203 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_6h  | sager_faithful |   0.363 | -0.773 | 0.635 |  87193 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | climatology    |   0.238 |  0.000 | 0.593 |  90234 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | persistence    |   0.278 | -0.169 | 0.661 |  90234 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | zambretti_cal  |   0.245 | -0.030 | 0.538 |  90072 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_cal      |   0.208 |  0.129 | 0.696 |  87217 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | logreg         |   0.186 |  0.219 | 0.763 |  90234 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_12h | sager_faithful |   0.377 | -0.578 | 0.616 |  87217 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | climatology    |   0.247 |  0.000 | 0.600 |  90199 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | persistence    |   0.414 | -0.676 | 0.622 |  90199 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | zambretti_cal  |   0.253 | -0.023 | 0.549 |  90037 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_cal      |   0.227 |  0.079 | 0.665 |  87190 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | logreg         |   0.211 |  0.144 | 0.727 |  90199 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | precip_24h | sager_faithful |   0.406 | -0.642 | 0.602 |  87190 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | climatology    |   0.191 |  0.000 | 0.572 |  89920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | persistence    |   0.263 | -0.371 | 0.500 |  89920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | zambretti_cal  |   0.193 | -0.006 | 0.558 |  89761 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_cal      |   0.185 |  0.020 | 0.613 |  87108 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | logreg         |   0.140 |  0.267 | 0.810 |  89920 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_6h  | sager_faithful |   0.437 | -1.314 | 0.507 |  87108 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | climatology    |   0.236 |  0.000 | 0.574 |  89984 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | persistence    |   0.397 | -0.687 | 0.500 |  89984 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | zambretti_cal  |   0.239 | -0.013 | 0.541 |  89822 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_cal      |   0.230 |  0.022 | 0.611 |  87162 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | logreg         |   0.165 |  0.298 | 0.817 |  89984 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_12h | sager_faithful |   0.493 | -1.101 | 0.480 |  87162 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | climatology    |   0.244 |  0.000 | 0.576 |  89952 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | persistence    |   0.536 | -1.196 | 0.500 |  89952 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | zambretti_cal  |   0.249 | -0.019 | 0.531 |  89790 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_cal      |   0.242 |  0.012 | 0.604 |  87134 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | logreg         |   0.181 |  0.258 | 0.801 |  89952 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | windup_24h | sager_faithful |   0.534 | -1.181 | 0.474 |  87134 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | climatology    |   0.137 |  0.000 | 0.689 |  90142 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | persistence    |   0.239 | -0.744 | 0.683 |  90142 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | zambretti_cal  |   0.133 |  0.029 | 0.680 |  89984 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | sager_cal      |   0.139 | -0.024 | 0.673 |  87140 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_6h   | logreg         |   0.111 |  0.188 | 0.832 |  90142 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | climatology    |   0.211 |  0.000 | 0.633 |  90188 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | persistence    |   0.330 | -0.567 | 0.601 |  90188 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | zambretti_cal  |   0.214 | -0.016 | 0.630 |  90028 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | sager_cal      |   0.216 | -0.025 | 0.641 |  87177 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_12h  | logreg         |   0.173 |  0.179 | 0.781 |  90188 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | climatology    |   0.237 |  0.000 | 0.627 |  90144 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | persistence    |   0.428 | -0.803 | 0.570 |  90144 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | zambretti_cal  |   0.243 | -0.023 | 0.633 |  89984 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | sager_cal      |   0.243 | -0.024 | 0.643 |  87141 |  nan     |  nan     |      nan |      nan |
| C_teststation_testyears  | pfall_24h  | logreg         |   0.206 |  0.133 | 0.743 |  90144 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | climatology    |   0.175 |  0.000 | 0.634 | 440399 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | persistence    |   0.179 | -0.021 | 0.647 | 440399 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | zambretti_cal  |   0.185 | -0.058 | 0.534 | 435257 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_cal      |   0.145 |  0.183 | 0.754 | 287998 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | logreg         |   0.139 |  0.206 | 0.781 | 440399 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_6h  | sager_faithful |   0.352 | -0.984 | 0.647 | 287998 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | climatology    |   0.211 |  0.000 | 0.635 | 439628 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | persistence    |   0.265 | -0.258 | 0.610 | 439628 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | zambretti_cal  |   0.224 | -0.062 | 0.548 | 434503 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_cal      |   0.186 |  0.122 | 0.712 | 287671 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | logreg         |   0.180 |  0.145 | 0.744 | 439628 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_12h | sager_faithful |   0.358 | -0.685 | 0.631 | 287671 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | climatology    |   0.233 |  0.000 | 0.642 | 438130 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | persistence    |   0.392 | -0.684 | 0.582 | 438130 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | zambretti_cal  |   0.248 | -0.067 | 0.556 | 433730 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_cal      |   0.219 |  0.058 | 0.679 | 287694 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | logreg         |   0.213 |  0.086 | 0.713 | 438130 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | precip_24h | sager_faithful |   0.380 | -0.633 | 0.616 | 287694 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | climatology    |   0.182 |  0.000 | 0.582 | 437695 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | persistence    |   0.244 | -0.345 | 0.500 | 437695 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | zambretti_cal  |   0.184 | -0.012 | 0.545 | 433339 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_cal      |   0.176 |  0.013 | 0.608 | 286980 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | logreg         |   0.148 |  0.183 | 0.769 | 437695 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_6h  | sager_faithful |   0.435 | -1.432 | 0.503 | 286980 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | climatology    |   0.231 |  0.000 | 0.577 | 435791 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | persistence    |   0.380 | -0.643 | 0.500 | 435791 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | zambretti_cal  |   0.235 | -0.015 | 0.533 | 431443 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_cal      |   0.226 |  0.018 | 0.607 | 285819 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | logreg         |   0.180 |  0.223 | 0.779 | 435791 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_12h | sager_faithful |   0.488 | -1.124 | 0.479 | 285819 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | climatology    |   0.245 |  0.000 | 0.578 | 434235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | persistence    |   0.521 | -1.130 | 0.500 | 434235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | zambretti_cal  |   0.249 | -0.017 | 0.528 | 430397 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_cal      |   0.243 |  0.011 | 0.599 | 285702 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | logreg         |   0.200 |  0.183 | 0.752 | 434235 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | windup_24h | sager_faithful |   0.525 | -1.140 | 0.478 | 285702 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | climatology    |   0.136 |  0.000 | 0.695 | 435103 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | persistence    |   0.255 | -0.882 | 0.659 | 435103 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | zambretti_cal  |   0.136 | -0.004 | 0.663 | 430430 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | sager_cal      |   0.139 | -0.040 | 0.667 | 285081 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_6h   | logreg         |   0.116 |  0.148 | 0.814 | 435103 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | climatology    |   0.209 |  0.000 | 0.641 | 431511 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | persistence    |   0.336 | -0.607 | 0.595 | 431511 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | zambretti_cal  |   0.216 | -0.034 | 0.621 | 427253 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | sager_cal      |   0.215 | -0.032 | 0.645 | 283166 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_12h  | logreg         |   0.181 |  0.133 | 0.760 | 431511 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | climatology    |   0.236 |  0.000 | 0.630 | 432462 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | persistence    |   0.431 | -0.826 | 0.569 | 432462 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | zambretti_cal  |   0.243 | -0.032 | 0.627 | 429258 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | sager_cal      |   0.242 | -0.027 | 0.647 | 285328 |  nan     |  nan     |      nan |      nan |
| B_teststation_trainyears | pfall_24h  | logreg         |   0.212 |  0.100 | 0.726 | 432462 |  nan     |  nan     |      nan |      nan |