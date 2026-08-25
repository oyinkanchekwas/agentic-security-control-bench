# Model Baselines

## Checked local run

The checked learned result uses
[Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) through the optional
Transformers adapter. The configuration pins model revision
`7ae557604adf67be50417f59c2c2f167def9a775`, temperature `0`, seed `20260825`, and prompt
`monitor-json-v1`. The model repository records an Apache 2.0 licence.

The prompt was frozen before the final 64-trace test partition was generated. Earlier scenario
work is assigned to train or development. The committed run summary records dataset, prompt, and
configuration digests. Raw prompts and generations remain under the ignored `results/raw/`
directory.

Version 0.4 uses the same configuration on 40 frozen clean counterparts and 160 adversarial traces.
The adversarial run produced valid responses throughout and selected `require_approval` on every
case. The result is reported as a degenerate high-intervention policy because prevention is 1.0000,
while approval burden is 1.0000. Permitted retention and selective utility are both 0.0000.

## Remote judge

`ChatCompletionsProvider` supports a JSON-response chat endpoint. Its configuration supplies the
endpoint, model identifier, timeout, token prices, and the name of an environment variable holding
the access credential. Checked summaries record the resolved model identifier and estimated cost.
No remote-judge score is included in v0.4.

## Agentic investigator

`AgenticInvestigatorMonitor` makes two provider calls. The first identifies a candidate event and
visible policy fields. The second receives the same monitor-visible trace plus the investigation
note and returns the common five-field response. Token use and cost are summed across both calls.
No investigator score is included in v0.4.

## Deterministic-model ensemble

The ensemble combines a named deterministic monitor with the single-pass model judge. Agreement
keeps the shared control. A disagreement involving `block` becomes `require_approval`; other
disagreements use the stricter non-blocking control. Evidence comes from the decision with higher
confidence. No ensemble score is included in v0.4. Its interface is exercised against all 160
adversarial traces with an offline fixture provider in the standard tests.

## Failure handling

Blank abstentions, malformed JSON, invalid controls, unknown event identifiers, unavailable fields,
and provider exceptions produce a fail-safe block. Execution status is retained separately, and
the benchmark reports each failure rate. A fail-safe prevention result remains visible beside
its malformed-output or execution-failure count.
