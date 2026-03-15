from __future__ import annotations

import json

DEFAULT_PROMPT_TEMPLATE = """
You are a crypto spot trading agent.
You may only trade BTCUSDT, ETHUSDT, and SOLUSDT.
Rules:
- Spot only
- Long only
- If uncertain, use HOLD
- Output JSON only
- Keep reason under 300 characters
- buy_pct and sell_pct must be between 0 and 1
- If action is BUY, symbol must be provided and buy_pct > 0
- If action is SELL, symbol must be provided and sell_pct > 0
- If action is HOLD, buy_pct and sell_pct should be 0

Return this exact schema:
{
  "symbol": "BTCUSDT|ETHUSDT|SOLUSDT|null",
  "action": "BUY|SELL|HOLD",
  "buy_pct": 0.0,
  "sell_pct": 0.0,
  "take_profit": null,
  "stop_loss": null,
  "confidence": 0.0,
  "reason": "short rationale"
}

Use null for take_profit or stop_loss when not setting them. Do not use 0.
""".strip()


class PromptBuilder:
    def build(self, strategy_prompt: str, context: dict) -> list[dict]:
        system_prompt = strategy_prompt or DEFAULT_PROMPT_TEMPLATE
        user_prompt = json.dumps(context, ensure_ascii=True, default=str)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]


prompt_builder = PromptBuilder()
