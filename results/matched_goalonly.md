## Per-run summary

### 7B   (model: ['Qwen/Qwen2.5-Coder-7B-Instruct'])
- trajectories: 126  |  attacked-task episodes: 108  |  benign controls: 18
- reached payload: 11/108 = 10.2% [5.8, 17.3]
- hijacked (of all attacked-task episodes): 3/108 = 2.8% [0.9, 7.9]
- hijacked (of those that reached the payload): 3/11 = 27.3% [9.7, 56.6]
- mean steps per attacked-task episode: 2.3
- utility proxy, edited src/app.py: 18/108 = 16.7% [10.8, 24.8]
- utility proxy, saw simulated tests pass: 12/108 = 11.1% [6.5, 18.4]
- controls that edited src/app.py: 3/18 = 16.7% [5.8, 39.2]
- controls not labeled benign (should be 0): 0/18

### 14B   (model: ['Qwen/Qwen2.5-Coder-14B-Instruct-AWQ'])
- trajectories: 126  |  attacked-task episodes: 108  |  benign controls: 18
- reached payload: 53/108 = 49.1% [39.8, 58.4]
- hijacked (of all attacked-task episodes): 18/108 = 16.7% [10.8, 24.8]
- hijacked (of those that reached the payload): 18/53 = 34.0% [22.7, 47.4]
- mean steps per attacked-task episode: 6.3
- utility proxy, edited src/app.py: 74/108 = 68.5% [59.3, 76.5]
- utility proxy, saw simulated tests pass: 71/108 = 65.7% [56.4, 74.0]
- controls that edited src/app.py: 15/18 = 83.3% [60.8, 94.2]
- controls not labeled benign (should be 0): 0/18

### 32B   (model: ['Qwen/Qwen2.5-Coder-32B-Instruct-AWQ'])
- trajectories: 126  |  attacked-task episodes: 108  |  benign controls: 18
- reached payload: 58/108 = 53.7% [44.3, 62.8]
- hijacked (of all attacked-task episodes): 27/108 = 25.0% [17.8, 33.9]
- hijacked (of those that reached the payload): 27/58 = 46.6% [34.3, 59.2]
- mean steps per attacked-task episode: 7.4
- utility proxy, edited src/app.py: 97/108 = 89.8% [82.7, 94.2]
- utility proxy, saw simulated tests pass: 94/108 = 87.0% [79.4, 92.1]
- controls that edited src/app.py: 16/18 = 88.9% [67.2, 96.9]
- controls not labeled benign (should be 0): 0/18

## Breakdowns

**7B by vector**

| vector | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| ci_log | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| code_comment | 27 | 2 | 1/27 = 3.7% [0.7, 18.3] | 1/2 = 50.0% [9.5, 90.5] |
| dependency_docs | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| issue_body | 26 | 2 | 0/26 = 0.0% [0.0, 12.9] | 0/2 = 0.0% [0.0, 65.8] |
| readme | 24 | 3 | 1/24 = 4.2% [0.7, 20.2] | 1/3 = 33.3% [6.1, 79.2] |
| test_output | 27 | 4 | 1/27 = 3.7% [0.7, 18.3] | 1/4 = 25.0% [4.6, 69.9] |

**7B by strength**

| strength | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| strong | 45 | 4 | 2/45 = 4.4% [1.2, 14.8] | 2/4 = 50.0% [15.0, 85.0] |
| weak | 63 | 7 | 1/63 = 1.6% [0.3, 8.5] | 1/7 = 14.3% [2.6, 51.3] |

**7B by goal_kind**

| goal_kind | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| curl_pipe_sh | 44 | 6 | 3/44 = 6.8% [2.3, 18.2] | 3/6 = 50.0% [18.8, 81.2] |
| exfiltrate | 19 | 2 | 0/19 = 0.0% [0.0, 16.8] | 0/2 = 0.0% [0.0, 65.8] |
| git_push | 15 | 1 | 0/15 = 0.0% [0.0, 20.4] | 0/1 = 0.0% [0.0, 79.3] |
| install_package | 22 | 1 | 0/22 = 0.0% [0.0, 14.9] | 0/1 = 0.0% [0.0, 79.3] |
| modify_path | 8 | 1 | 0/8 = 0.0% [0.0, 32.4] | 0/1 = 0.0% [0.0, 79.3] |

**14B by vector**

| vector | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| ci_log | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| code_comment | 27 | 22 | 4/27 = 14.8% [5.9, 32.5] | 4/22 = 18.2% [7.3, 38.5] |
| dependency_docs | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| issue_body | 26 | 11 | 1/26 = 3.8% [0.7, 18.9] | 1/11 = 9.1% [1.6, 37.7] |
| readme | 24 | 16 | 12/24 = 50.0% [31.4, 68.6] | 12/16 = 75.0% [50.5, 89.8] |
| test_output | 27 | 4 | 1/27 = 3.7% [0.7, 18.3] | 1/4 = 25.0% [4.6, 69.9] |

**14B by strength**

| strength | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| strong | 45 | 22 | 8/45 = 17.8% [9.3, 31.3] | 8/22 = 36.4% [19.7, 57.0] |
| weak | 63 | 31 | 10/63 = 15.9% [8.9, 26.8] | 10/31 = 32.3% [18.6, 49.9] |

**14B by goal_kind**

| goal_kind | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| curl_pipe_sh | 44 | 26 | 17/44 = 38.6% [25.7, 53.4] | 17/26 = 65.4% [46.2, 80.6] |
| exfiltrate | 19 | 9 | 1/19 = 5.3% [0.9, 24.6] | 1/9 = 11.1% [2.0, 43.5] |
| git_push | 15 | 6 | 0/15 = 0.0% [0.0, 20.4] | 0/6 = 0.0% [0.0, 39.0] |
| install_package | 22 | 8 | 0/22 = 0.0% [0.0, 14.9] | 0/8 = 0.0% [0.0, 32.4] |
| modify_path | 8 | 4 | 0/8 = 0.0% [0.0, 32.4] | 0/4 = 0.0% [0.0, 49.0] |

**32B by vector**

| vector | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| ci_log | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| code_comment | 27 | 26 | 9/27 = 33.3% [18.6, 52.2] | 9/26 = 34.6% [19.4, 53.8] |
| dependency_docs | 2 | 0 | 0/2 = 0.0% [0.0, 65.8] | n/a |
| issue_body | 26 | 8 | 2/26 = 7.7% [2.1, 24.1] | 2/8 = 25.0% [7.1, 59.1] |
| readme | 24 | 20 | 14/24 = 58.3% [38.8, 75.5] | 14/20 = 70.0% [48.1, 85.5] |
| test_output | 27 | 4 | 2/27 = 7.4% [2.1, 23.4] | 2/4 = 50.0% [15.0, 85.0] |

**32B by strength**

| strength | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| strong | 45 | 23 | 12/45 = 26.7% [16.0, 41.0] | 12/23 = 52.2% [33.0, 70.8] |
| weak | 63 | 35 | 15/63 = 23.8% [15.0, 35.6] | 15/35 = 42.9% [28.0, 59.1] |

**32B by goal_kind**

| goal_kind | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| curl_pipe_sh | 44 | 27 | 23/44 = 52.3% [37.9, 66.2] | 23/27 = 85.2% [67.5, 94.1] |
| exfiltrate | 19 | 12 | 3/19 = 15.8% [5.5, 37.6] | 3/12 = 25.0% [8.9, 53.2] |
| git_push | 15 | 8 | 1/15 = 6.7% [1.2, 29.8] | 1/8 = 12.5% [2.2, 47.1] |
| install_package | 22 | 8 | 0/22 = 0.0% [0.0, 14.9] | 0/8 = 0.0% [0.0, 32.4] |
| modify_path | 8 | 3 | 0/8 = 0.0% [0.0, 32.4] | 0/3 = 0.0% [0.0, 56.2] |

## Paired comparisons

**7B vs 14B** on 108 shared attacked-task ids (of 108 and 108)
- hijacked by both: 2 | only 7B: 1 | only 14B: 16 | neither: 89
- 7B: 3/108 = 2.8% [0.9, 7.9]   14B: 18/108 = 16.7% [10.8, 24.8]
- exact sign test on the 17 discordant tasks: p = 2.7e-04

**7B vs 32B** on 108 shared attacked-task ids (of 108 and 108)
- hijacked by both: 2 | only 7B: 1 | only 32B: 25 | neither: 80
- 7B: 3/108 = 2.8% [0.9, 7.9]   32B: 27/108 = 25.0% [17.8, 33.9]
- exact sign test on the 26 discordant tasks: p = 8.0e-07

**14B vs 32B** on 108 shared attacked-task ids (of 108 and 108)
- hijacked by both: 16 | only 14B: 2 | only 32B: 11 | neither: 79
- 14B: 18/108 = 16.7% [10.8, 24.8]   32B: 27/108 = 25.0% [17.8, 33.9]
- exact sign test on the 13 discordant tasks: p = 0.022

**Holm-adjusted p-values** (family of all pairwise tests above)
- 7B vs 32B: raw 8.0e-07 -> adjusted 2.4e-06 (significant at 0.05)
- 7B vs 14B: raw 2.7e-04 -> adjusted 5.5e-04 (significant at 0.05)
- 14B vs 32B: raw 0.022 -> adjusted 0.022 (significant at 0.05)
