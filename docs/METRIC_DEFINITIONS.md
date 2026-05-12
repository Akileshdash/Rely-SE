# RELY-SE Metric Definitions

## HIR — Human Intervention Rate
**Formula:** `HIR = (# tasks requiring intervention) / N`  
**Range:** [0.0, 1.0] — lower is better  
**Adapted from:** Autonomous vehicle disengagement rate (NHTSA)  
A task requires intervention when the agent crashes, exceeds resource limits
without proposing a patch, or produces unsafe operations needing human review.

## CFR — Commit Failure Rate
**Formula:** `CFR = (# patches breaking build/tests) / M`  
where M = # patches proposed  
**Range:** [0.0, 1.0] — lower is better  
**Adapted from:** SRE Change Failure Rate (Google SRE Book)  
Captures CI stability impact. An agent with high TSR but high CFR is unsafe
for production deployment because it destabilises the test suite.

## TSR — Task Success Rate
**Formula:** `TSR = (# tasks correctly resolved, no regression) / N`  
**Range:** [0.0, 1.0] — higher is better  
**Adapted from:** Medical AI treatment success rate  
Equivalent to SWE-bench's pass@1. A task is successful iff the originally
failing tests now pass AND no previously passing tests are broken.

## AGAR — Agent Goal Achievement Reliability
**Formula:** `AGAR = (# successful completions) / (# completions)`  
where completion = finished within time/resource limits  
**Range:** [0.0, 1.0] — higher is better  
**Adapted from:** Aviation MTBF / goal reliability  
Differs from TSR: AGAR conditions on completion, excluding timeout runs.
Measures quality of attempts that actually finish.

## DSM — Decision Stability Metric
**Formula:** `DSM = max(k/n, (n-k)/n)` where k = successes, n = trials  
**Range:** [0.5, 1.0] — higher is better  
**Adapted from:** Stochastic process stability  
Measures behavioural consistency across identical repeated runs.
- 0.5 = coin-flip (maximally stochastic)
- 1.0 = perfectly consistent (always succeeds or always fails)
An agent with DSM < 0.7 is unpredictable and requires monitoring.
