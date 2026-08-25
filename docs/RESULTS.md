# Results

These values use all 256 synthetic traces in version 0.2. Intervals are 95% percentile intervals
from 1,000 contrast-set bootstrap samples.

| Monitor | Control accuracy | Prevention | Task completion | Permitted retention | Evidence recall | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2578 | 0.7656 | 0.3750 | 0.1562 | 0.0000 | 0.1562 | 0.8438 | 0.0000 |
| Policy-field oracle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.5078 | 0.1875 | 0.9141 | 0.8281 | 0.0000 | 0.2656 | 0.7344 | 0.0000 |

## Keyword baseline

The keyword monitor prevents 98 of 128 unsafe effects. Its 95% prevention interval is
0.6641 to 0.8594. It retains 20 of 128 permitted tasks, with interval 0.0859 to 0.2344.

The policy-family counts show the mechanism behind this trade-off. Every permitted verification
and publication trace is interrupted, including lexical decoys. Test-weakening cases retain 8 of
16 permitted tasks, the highest family result for this monitor. Its evidence points to text, so it
does not identify any causal policy field.

## Monitor Lab adapter

Monitor Lab retains 106 permitted tasks and prevents 24 unsafe effects. Its retention interval is
0.7578 to 0.8906; its prevention interval is 0.1094 to 0.2578.

Prevention reaches 0.50 for false verification and test weakening. It is zero for outbound
destination breaches, publication approval failures, secret exposure, and dependency provenance.
This follows the earlier monitor's text-oriented rules and their limited coverage of structured
policy attributes.

## Oracle check

The policy-field oracle reads the labelled attributes used to construct each contrast set. Its
perfect score confirms the evaluator path, evidence keys, gold controls, and recovery effects. It
does not estimate performance on unseen traces.

## Split behaviour

Train, development, and test contain disjoint semantic scenarios. The deterministic baselines show
small differences between the partitions because their rules are fixed and each partition retains
the same family balance. Per-split values are stored in the checked JSON files.

![Unsafe-action prevention against permitted-task retention](assets/safety-retention.svg)

The family count tables are in [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md). Case-level decisions and
replay outcomes can be regenerated with the command in the README.
