"""Demo script showing Phase 1 API usage."""

from gremlin import Gremlin

# Basic usage - as specified in Phase 1 requirements
gremlin = Gremlin()

print("=== Gremlin Phase 1 API Demo ===\n")

# Example 1: Simple analysis
print("1. Simple analysis:")
result = gremlin.analyze("user authentication with JWT tokens")
print(f"   Scope: {result.scope}")
print(f"   Risks found: {len(result.risks)}")
print(f"   Pattern count: {result.pattern_count}")
print(f"   Matched domains: {result.matched_domains}")

if result.risks:
    print("\n   First risk:")
    risk = result.risks[0]
    print(f"   - Severity: {risk.severity} ({risk.confidence}%)")
    print(f"   - Scenario: {risk.scenario[:80]}...")
    print(f"   - Impact: {risk.impact[:80]}...")

# Example 2: Different output formats
print("\n2. Output formats:")
print(f"   - JSON: {len(result.to_json())} chars")
print(f"   - JUnit XML: {len(result.to_junit())} chars")
print(f"   - LLM format: {len(result.format_for_llm())} chars")

# Example 3: Check for critical risks
print("\n3. Risk detection:")
print(f"   - Has critical risks: {result.has_critical_risks()}")
print(f"   - Has high severity: {result.has_high_severity_risks()}")
print(f"   - Critical count: {result.critical_count}")
print(f"   - High count: {result.high_count}")

print("\n✅ Phase 1 API is working correctly!")
print("   You can now use: from gremlin import Gremlin")
