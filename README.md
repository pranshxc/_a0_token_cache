# _a0_token_cache

Per-call token meter for Agent Zero. Shows **input, output, cached tokens** and **cost estimate** after every LLM call. Writes JSONL log for offline analysis.

## What it shows

```
🪙 Token Meter — Call #7 (claude-sonnet-4-5)
  input       :     68,423
  output      :        892
  cache_read  :     61,210  (89.5% of input)
  cache_write :          0
  cost (call) : $0.0312

📊 Token Meter — Session Totals (7 calls)
  total input       :    420,100
  total output      :      5,604
  total cache_read  :    381,200  (90.7% of input)
  total cache_write :      8,400
  cache savings     : $0.9842
  total cost        : $1.2341
  avg input/call    :     60,014
```

## Why this matters

A0 sends the **full conversation history on every tool call**. Without cache:
- 10 tool calls × 60k input = 600k tokens billed

With cache working (90% hit rate):
- 10 × 60k = 600k sent, but 540k served from cache at ~10% the price

### Reading cache health

| Signal | Meaning |
|---|---|
| `cache_read > 0` | ✅ Cache working |
| `cache_read = 0, cache_write = 0` | ⚠️ Not supported or prefix too short |
| High `cache_read / input` ratio | 💰 Well optimised |

Anthropic requires >1024 tokens before caching kicks in.

## JSONL log

Every call appended to `work/token_meter/<chat_id>.jsonl`:
```json
{"ts": 1746, "model": "claude-sonnet-4-5", "call": 7, "input": 68423, "output": 892, "cache_read": 61210, "cache_write": 0, "cost_usd": 0.0312, "cache_hit_pct": 89.5}
```

## Configuration

Set prices in `docker-compose.yml`:
```yaml
environment:
  - TOKEN_METER_PRICE_INPUT_PER_1M=3.00
  - TOKEN_METER_PRICE_OUTPUT_PER_1M=15.00
  - TOKEN_METER_PRICE_CACHE_READ_PER_1M=0.30
  - TOKEN_METER_PRICE_CACHE_WRITE_PER_1M=3.75
```

### Model pricing reference (per 1M tokens)

| Model | Input | Output | Cache Read | Cache Write |
|---|---|---|---|---|
| Claude Sonnet 4.5 | $3.00 | $15.00 | $0.30 | $3.75 |
| Claude Haiku 3.5 | $0.80 | $4.00 | $0.08 | $1.00 |
| GPT-4o | $2.50 | $10.00 | $1.25 | $0 |
| GPT-4o-mini | $0.15 | $0.60 | $0.075 | $0 |
| Gemini 2.5 Flash | $0.15 | $0.60 | $0.0375 | $1.00 |
| Gemini 2.5 Pro | $1.25 | $10.00 | $0.3125 | $4.50 |
| Local / GLM | $0 | $0 | $0 | $0 |

## Install

```bash
git clone https://github.com/pranshxc/_a0_token_cache /path/to/agent-zero/plugins/_a0_token_cache
docker restart agent-zero
```
