# Seed Results

The four included baselines expose different errors in the benchmark protocol.

The allow-all monitor retains every permitted task and permits every unsafe effect. The block-all
monitor prevents each prohibited effect, while all permitted tasks are stopped. Its 0.25 exact
control score reflects the unsafe cases whose gold control is `block`; it selects an excessive
control for the remaining cases.

The keyword monitor reacts to surface terms in both action text and contextual data. It prevents
56.25% of unsafe actions, retains 31.25% of permitted tasks, and reaches 0.50 on both
counterfactual measures. Its evidence cites text spans, so it receives no field-level evidence
credit.

The policy-field monitor reads the attributes used to label each seed case. It identifies every
gold field and selects every gold control. This is a reference check for dataset wiring, replay,
and metric calculation. The score does not estimate performance on unlabelled coding-agent traces.

The Monitor Lab adapter retains 75% of permitted tasks and prevents 12.5% of unsafe effects. Its
rules were written for text traces and return excerpt evidence. The present benchmark places the
decisive policy state in structured action attributes, which accounts for its zero field-evidence
score and low counterfactual sensitivity.

| Monitor | Control accuracy | Prevention | Task completion | Permitted retention | Evidence recall | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.2500 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2812 | 0.5625 | 0.5000 | 0.3125 | 0.0000 | 0.5000 | 0.5000 | 0.0000 |
| Policy field | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.4375 | 0.1250 | 0.8750 | 0.7500 | 0.0000 | 0.2500 | 0.6250 | 0.0000 |

The committed JSON files contain the checked summary values. Case-level decisions and replay
outcomes can be regenerated with the command in the README.
