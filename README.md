# 💰 llm-price-tracker

**Compare LLM API prices across all providers. Instantly.**

Find the cheapest model. Calculate job costs. Stay within budget.

```
$ llm-price-tracker --cheap

💰 llm-price-tracker v0.1.0
───────────────────────────────────────────────────────────────────────────────────────────────
  Provider     Model                      Input/1M   Output/1M    Context  Cat
  ──────────────────────────────────────────────────────────────────────────────────────────
  Mistral      Mistral Small                 $0.10       $0.30    128,000  🚀
  Google       Gemini 2.0 Flash              $0.10       $0.40  1,000,000  🚀
  OpenAI       GPT-4o-mini                   $0.15       $0.60    128,000  🚀
  Google       Gemini 2.5 Flash              $0.15       $0.60  1,000,000  🚀
  Meta         Llama 4 Scout                 $0.15       $0.60    512,000  ⚡
  DeepSeek     DeepSeek-V3                   $0.27       $1.10    128,000  ⚡
  Anthropic    Claude Haiku 4                $0.25       $1.25    200,000  🚀
  ...
```

## Install

```bash
pip install llm-price-tracker
```

Or download:

```bash
curl -O https://raw.githubusercontent.com/leiMizzou/llm-price-tracker/main/llm_prices.py
python3 llm_prices.py
```

## Usage

```bash
# Show all prices (sorted by output cost)
llm-price-tracker

# Cheapest first
llm-price-tracker --cheap

# Calculate cost for a job (100K input, 50K output tokens)
llm-price-tracker --calc 100000 50000

# Find models within $0.50 budget for that job
llm-price-tracker --calc 100000 50000 --budget 0.50

# Filter by provider
llm-price-tracker --filter anthropic

# Only reasoning models
llm-price-tracker --category reasoning

# Only fast/cheap models
llm-price-tracker --category fast

# JSON output
llm-price-tracker --json

# Markdown table
llm-price-tracker --markdown > prices.md
```

## 35+ Models Covered

OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, xAI, Cohere, Zhipu, Moonshot, ByteDance, Alibaba

## Features

- **35+ models** from 12 providers
- **Cost calculator** — estimate cost for any job
- **Budget filter** — find models within your budget  
- **Category filter** — reasoning, general, fast
- **Multiple outputs** — terminal, JSON, Markdown
- **Zero dependencies** — pure Python 3.8+
- **Single file** — works standalone

## Contributing

Prices change fast! PRs welcome to update the price database. Just edit the `MODELS` list in `llm_prices.py`.

## License

MIT
