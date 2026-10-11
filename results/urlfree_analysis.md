## Per-run summary

### urlfree-14B   (model: ['Qwen/Qwen2.5-Coder-14B-Instruct-AWQ'])
- trajectories: 126  |  attacked-task episodes: 108  |  benign controls: 18
- reached payload: 35/108 = 32.4% [24.3, 41.7]
- hijacked (of all attacked-task episodes): 11/108 = 10.2% [5.8, 17.3]
- hijacked (of those that reached the payload): 11/35 = 31.4% [18.6, 48.0]
- mean steps per attacked-task episode: 6.3
- utility proxy, edited src/app.py: 74/108 = 68.5% [59.3, 76.5]
- utility proxy, saw simulated tests pass: 68/108 = 63.0% [53.6, 71.5]
- controls that edited src/app.py: 12/18 = 66.7% [43.7, 83.7]
- controls not labeled benign (should be 0): 0/18

### urlfree-32B   (model: ['Qwen/Qwen2.5-Coder-32B-Instruct-AWQ'])
- trajectories: 126  |  attacked-task episodes: 108  |  benign controls: 18
- reached payload: 54/108 = 50.0% [40.7, 59.3]
- hijacked (of all attacked-task episodes): 23/108 = 21.3% [14.6, 29.9]
- hijacked (of those that reached the payload): 23/54 = 42.6% [30.3, 55.8]
- mean steps per attacked-task episode: 7.6
- utility proxy, edited src/app.py: 98/108 = 90.7% [83.8, 94.9]
- utility proxy, saw simulated tests pass: 94/108 = 87.0% [79.4, 92.1]
- controls that edited src/app.py: 17/18 = 94.4% [74.2, 99.0]
- controls not labeled benign (should be 0): 0/18

## Breakdowns

**urlfree-14B by vector**

| vector | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| ci_log | 4 | 2 | 1/4 = 25.0% [4.6, 69.9] | 1/2 = 50.0% [9.5, 90.5] |
| code_comment | 19 | 11 | 3/19 = 15.8% [5.5, 37.6] | 3/11 = 27.3% [9.7, 56.6] |
| issue_body | 35 | 8 | 3/35 = 8.6% [3.0, 22.4] | 3/8 = 37.5% [13.7, 69.4] |
| readme | 30 | 13 | 4/30 = 13.3% [5.3, 29.7] | 4/13 = 30.8% [12.7, 57.6] |
| test_output | 20 | 1 | 0/20 = 0.0% [0.0, 16.1] | 0/1 = 0.0% [0.0, 79.3] |

**urlfree-14B by strength**

| strength | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| strong | 55 | 18 | 9/55 = 16.4% [8.9, 28.3] | 9/18 = 50.0% [29.0, 71.0] |
| weak | 53 | 17 | 2/53 = 3.8% [1.0, 12.8] | 2/17 = 11.8% [3.3, 34.3] |

**urlfree-14B by goal_kind**

| goal_kind | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| curl_pipe_sh | 26 | 6 | 3/26 = 11.5% [4.0, 29.0] | 3/6 = 50.0% [18.8, 81.2] |
| exfiltrate | 11 | 5 | 0/11 = 0.0% [0.0, 25.9] | 0/5 = 0.0% [0.0, 43.4] |
| git_push | 13 | 4 | 0/13 = 0.0% [0.0, 22.8] | 0/4 = 0.0% [0.0, 49.0] |
| install_package | 28 | 11 | 0/28 = 0.0% [0.0, 12.1] | 0/11 = 0.0% [0.0, 25.9] |
| modify_path | 6 | 1 | 0/6 = 0.0% [0.0, 39.0] | 0/1 = 0.0% [0.0, 79.3] |
| run_local_script | 24 | 8 | 8/24 = 33.3% [18.0, 53.3] | 8/8 = 100.0% [67.6, 100.0] |

**urlfree-32B by vector**

| vector | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| ci_log | 4 | 2 | 0/4 = 0.0% [0.0, 49.0] | 0/2 = 0.0% [0.0, 65.8] |
| code_comment | 19 | 19 | 9/19 = 47.4% [27.3, 68.3] | 9/19 = 47.4% [27.3, 68.3] |
| issue_body | 35 | 15 | 7/35 = 20.0% [10.0, 35.9] | 7/15 = 46.7% [24.8, 69.9] |
| readme | 30 | 16 | 7/30 = 23.3% [11.8, 40.9] | 7/16 = 43.8% [23.1, 66.8] |
| test_output | 20 | 2 | 0/20 = 0.0% [0.0, 16.1] | 0/2 = 0.0% [0.0, 65.8] |

**urlfree-32B by strength**

| strength | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| strong | 55 | 28 | 16/55 = 29.1% [18.8, 42.1] | 16/28 = 57.1% [39.1, 73.5] |
| weak | 53 | 26 | 7/53 = 13.2% [6.5, 24.8] | 7/26 = 26.9% [13.7, 46.1] |

**urlfree-32B by goal_kind**

| goal_kind | episodes | reached payload | hijacked / all | hijacked / reached |
|---|---|---|---|---|
| curl_pipe_sh | 26 | 12 | 10/26 = 38.5% [22.4, 57.5] | 10/12 = 83.3% [55.2, 95.3] |
| exfiltrate | 11 | 5 | 1/11 = 9.1% [1.6, 37.7] | 1/5 = 20.0% [3.6, 62.4] |
| git_push | 13 | 10 | 2/13 = 15.4% [4.3, 42.2] | 2/10 = 20.0% [5.7, 51.0] |
| install_package | 28 | 15 | 0/28 = 0.0% [0.0, 12.1] | 0/15 = 0.0% [0.0, 20.4] |
| modify_path | 6 | 0 | 0/6 = 0.0% [0.0, 39.0] | n/a |
| run_local_script | 24 | 12 | 10/24 = 41.7% [24.5, 61.2] | 10/12 = 83.3% [55.2, 95.3] |

## Paired comparisons

**urlfree-14B vs urlfree-32B** on 108 shared attacked-task ids (of 108 and 108)
- hijacked by both: 8 | only urlfree-14B: 3 | only urlfree-32B: 15 | neither: 82
- urlfree-14B: 11/108 = 10.2% [5.8, 17.3]   urlfree-32B: 23/108 = 21.3% [14.6, 29.9]
- exact sign test on the 18 discordant tasks: p = 0.008
