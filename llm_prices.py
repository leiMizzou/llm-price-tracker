#!/usr/bin/env python3
"""
💰 llm-price-tracker — Compare LLM API prices across providers.

Instantly compare input/output token costs, calculate job costs,
and find the cheapest model for your use case.

Usage:
    python llm_prices.py                        # Show all prices
    python llm_prices.py --sort output          # Sort by output price
    python llm_prices.py --calc 10000 5000      # Cost for 10K in / 5K out
    python llm_prices.py --budget 1.00          # Models within $1 budget
    python llm_prices.py --filter claude        # Filter by name
    python llm_prices.py --category reasoning   # Filter by category

Zero dependencies. Python 3.8+.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import List, Optional

__version__ = "0.1.0"

# ─── Price Database (per 1M tokens, USD) ────────────────────────────────────
# Last updated: 2026-02-12
# Sources: Official API pricing pages

@dataclass
class Model:
    provider: str
    name: str
    input_price: float   # per 1M input tokens
    output_price: float  # per 1M output tokens
    context: int         # context window size
    category: str        # reasoning, general, fast, embedding, image
    notes: str = ""

MODELS = [
    # OpenAI
    Model("OpenAI", "GPT-5", 10.00, 30.00, 256000, "reasoning", "Latest flagship"),
    Model("OpenAI", "GPT-5-mini", 1.50, 6.00, 256000, "fast", "Efficient"),
    Model("OpenAI", "GPT-4o", 2.50, 10.00, 128000, "general", "Multimodal"),
    Model("OpenAI", "GPT-4o-mini", 0.15, 0.60, 128000, "fast", "Cheapest OpenAI"),
    Model("OpenAI", "GPT-4-turbo", 10.00, 30.00, 128000, "general", "Legacy"),
    Model("OpenAI", "o3", 10.00, 40.00, 200000, "reasoning", "Chain-of-thought"),
    Model("OpenAI", "o3-mini", 1.10, 4.40, 200000, "reasoning", "Efficient reasoning"),
    Model("OpenAI", "o4-mini", 1.10, 4.40, 200000, "reasoning", "Latest reasoning"),
    
    # Anthropic
    Model("Anthropic", "Claude Opus 4", 15.00, 75.00, 200000, "reasoning", "Flagship"),
    Model("Anthropic", "Claude Sonnet 4", 3.00, 15.00, 200000, "general", "Balanced"),
    Model("Anthropic", "Claude Haiku 4", 0.25, 1.25, 200000, "fast", "Fastest Claude"),
    Model("Anthropic", "Claude Sonnet 3.5", 3.00, 15.00, 200000, "general", "Previous gen"),
    
    # Google
    Model("Google", "Gemini 2.5 Pro", 1.25, 10.00, 1000000, "reasoning", "1M context"),
    Model("Google", "Gemini 2.5 Flash", 0.15, 0.60, 1000000, "fast", "1M context, fast"),
    Model("Google", "Gemini 2.0 Flash", 0.10, 0.40, 1000000, "fast", "Cheapest 1M"),
    Model("Google", "Gemini 3 Pro", 2.50, 15.00, 2000000, "reasoning", "2M context"),
    
    # Meta (via API providers)
    Model("Meta", "Llama 3.3 70B", 0.60, 0.60, 128000, "general", "Open source"),
    Model("Meta", "Llama 3.1 405B", 3.00, 3.00, 128000, "reasoning", "Open source, largest"),
    Model("Meta", "Llama 4 Scout", 0.15, 0.60, 512000, "general", "512K context"),
    Model("Meta", "Llama 4 Maverick", 0.30, 0.90, 256000, "general", "Open source"),
    
    # Mistral
    Model("Mistral", "Mistral Large", 2.00, 6.00, 128000, "general", "Flagship"),
    Model("Mistral", "Mistral Small", 0.10, 0.30, 128000, "fast", "Budget"),
    Model("Mistral", "Codestral", 0.30, 0.90, 256000, "general", "Code-focused"),
    
    # DeepSeek
    Model("DeepSeek", "DeepSeek-V3", 0.27, 1.10, 128000, "general", "Very cheap"),
    Model("DeepSeek", "DeepSeek-R1", 0.55, 2.19, 128000, "reasoning", "Reasoning, cheap"),
    
    # xAI
    Model("xAI", "Grok-3", 3.00, 15.00, 131072, "reasoning", "xAI flagship"),
    Model("xAI", "Grok-3 Mini", 0.30, 0.50, 131072, "fast", "Efficient"),
    
    # Cohere
    Model("Cohere", "Command R+", 2.50, 10.00, 128000, "general", "RAG-optimized"),
    Model("Cohere", "Command R", 0.15, 0.60, 128000, "fast", "Budget RAG"),
    
    # Chinese providers
    Model("Zhipu", "GLM-5", 1.00, 4.00, 128000, "reasoning", "Chinese flagship"),
    Model("Moonshot", "Kimi K2.5", 0.50, 2.00, 256000, "general", "256K context"),
    Model("ByteDance", "Doubao Pro", 0.40, 1.20, 128000, "general", "ByteDance"),
    Model("Alibaba", "Qwen-Max", 1.60, 6.40, 128000, "reasoning", "Alibaba flagship"),
    Model("Alibaba", "Qwen-Plus", 0.40, 1.20, 128000, "general", "Budget Qwen"),
]

# ─── Cost Calculator ────────────────────────────────────────────────────────

def calc_cost(model: Model, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for given token counts."""
    return (model.input_price * input_tokens / 1_000_000 + 
            model.output_price * output_tokens / 1_000_000)

# ─── Output Formatters ──────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"

CATEGORY_ICON = {
    "reasoning": "🧠",
    "general": "⚡",
    "fast": "🚀",
    "embedding": "📐",
    "image": "🖼️",
}

def format_price(price: float) -> str:
    if price < 0.50:
        return f"{GREEN}${price:.2f}{RESET}"
    elif price < 5.00:
        return f"{YELLOW}${price:.2f}{RESET}"
    else:
        return f"{RED}${price:.2f}{RESET}"

def format_table(models: List[Model], show_cost: bool = False,
                 input_tokens: int = 0, output_tokens: int = 0) -> str:
    """Format as terminal table."""
    lines = []
    lines.append(f"\n{BOLD}💰 llm-price-tracker v{__version__}{RESET}")
    lines.append(f"{DIM}{'─' * 95}{RESET}")
    
    if show_cost:
        lines.append(f"  Cost estimate for {BOLD}{input_tokens:,}{RESET} input + {BOLD}{output_tokens:,}{RESET} output tokens\n")
        header = f"  {'Provider':<12} {'Model':<24} {'Input/1M':>10} {'Output/1M':>10} {'Context':>10} {'Cat':>4} {'Cost':>10}"
    else:
        header = f"  {'Provider':<12} {'Model':<24} {'Input/1M':>10} {'Output/1M':>10} {'Context':>10} {'Cat':>4}"
    
    lines.append(f"{BOLD}{header}{RESET}")
    lines.append(f"  {'─' * 90}")
    
    for m in models:
        icon = CATEGORY_ICON.get(m.category, "")
        ctx = f"{m.context:,}"
        ip = format_price(m.input_price)
        op = format_price(m.output_price)
        
        if show_cost:
            cost = calc_cost(m, input_tokens, output_tokens)
            cost_str = format_price(cost)
            lines.append(f"  {m.provider:<12} {m.name:<24} {ip:>20} {op:>20} {ctx:>10} {icon:>4} {cost_str:>20}")
        else:
            lines.append(f"  {m.provider:<12} {m.name:<24} {ip:>20} {op:>20} {ctx:>10} {icon:>4}")
    
    lines.append(f"\n{DIM}  Prices per 1M tokens (USD). Last updated: 2026-02-12{RESET}")
    lines.append(f"{DIM}  ⚠ Prices change frequently. Verify at provider's pricing page.{RESET}\n")
    return '\n'.join(lines)

def format_json(models: List[Model]) -> str:
    return json.dumps([{
        "provider": m.provider, "model": m.name,
        "input_price_per_1m": m.input_price, "output_price_per_1m": m.output_price,
        "context_window": m.context, "category": m.category, "notes": m.notes,
    } for m in models], indent=2)

def format_markdown(models: List[Model]) -> str:
    lines = ["# 💰 LLM Price Comparison\n"]
    lines.append(f"*Last updated: 2026-02-12*\n")
    lines.append("| Provider | Model | Input/1M | Output/1M | Context | Category |")
    lines.append("|----------|-------|----------|-----------|---------|----------|")
    for m in models:
        lines.append(f"| {m.provider} | {m.name} | ${m.input_price:.2f} | ${m.output_price:.2f} | {m.context:,} | {m.category} |")
    return '\n'.join(lines)

# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="llm-price-tracker",
        description="💰 Compare LLM API prices across providers",
    )
    parser.add_argument("--sort", "-s", choices=["input", "output", "provider", "context", "name"],
                       default="output", help="Sort by field (default: output)")
    parser.add_argument("--filter", "-f", help="Filter by model/provider name")
    parser.add_argument("--category", "-c", choices=["reasoning", "general", "fast"],
                       help="Filter by category")
    parser.add_argument("--calc", nargs=2, type=int, metavar=("IN", "OUT"),
                       help="Calculate cost for IN input and OUT output tokens")
    parser.add_argument("--budget", "-b", type=float,
                       help="Show models within budget (for --calc tokens)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown")
    parser.add_argument("--cheap", action="store_true", help="Sort cheapest first (by output)")
    parser.add_argument("--version", "-v", action="version", version=f"llm-price-tracker {__version__}")
    
    args = parser.parse_args()
    models = list(MODELS)
    
    # Filter
    if args.filter:
        q = args.filter.lower()
        models = [m for m in models if q in m.name.lower() or q in m.provider.lower()]
    
    if args.category:
        models = [m for m in models if m.category == args.category]
    
    # Sort
    sort_keys = {
        "input": lambda m: m.input_price,
        "output": lambda m: m.output_price,
        "provider": lambda m: m.provider.lower(),
        "context": lambda m: -m.context,
        "name": lambda m: m.name.lower(),
    }
    
    if args.cheap:
        models.sort(key=lambda m: m.output_price)
    else:
        models.sort(key=sort_keys.get(args.sort, sort_keys["output"]))
    
    # Budget filter
    if args.budget and args.calc:
        input_t, output_t = args.calc
        models = [m for m in models if calc_cost(m, input_t, output_t) <= args.budget]
    
    # Output
    if args.json:
        print(format_json(models))
    elif args.markdown:
        print(format_markdown(models))
    elif args.calc:
        input_t, output_t = args.calc
        models.sort(key=lambda m: calc_cost(m, input_t, output_t))
        print(format_table(models, show_cost=True, input_tokens=input_t, output_tokens=output_t))
    else:
        print(format_table(models))

if __name__ == "__main__":
    main()
