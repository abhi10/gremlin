#!/usr/bin/env python3
"""Check Anthropic API credits and usage."""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Make a minimal test call to verify API key works
try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print("✓ API key is valid and working")
    print(f"✓ Test call succeeded (used ~{response.usage.input_tokens + response.usage.output_tokens} tokens)")
    print("\nNote: Anthropic doesn't provide a direct API to check remaining credits.")
    print("You need to check your usage and limits via the Anthropic Console:")
    print("  → https://console.anthropic.com/settings/usage")
    print("\nEstimated cost for this eval run:")
    print("  • 54 cases × 3 trials × 2 models = 324 API calls")
    print("  • ~500-1000 tokens per call (avg)")
    print("  • Claude Sonnet 4: $3 per MTok input, $15 per MTok output")
    print("  • Estimated total: $2-5 USD")
    
except Exception as e:
    print(f"✗ API key error: {e}")
    print("\nMake sure ANTHROPIC_API_KEY is set correctly:")
    print(f"  Current value: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')[:20]}...")

