# Pattern Refinement from Eval Losses

## Process

### 1. Identify Losses
```bash
# Find cases where baseline won
python evals/analyze_losses.py --min-delta 10
```

### 2. Manual Review
For each loss:
- Read baseline output
- Extract superior risk scenarios
- Identify pattern gaps

### 3. Pattern Enhancement
Options:
- **Add new pattern:** If baseline found novel risk
- **Sharpen existing:** If pattern too vague
- **Add few-shot example:** If pattern needs context

### 4. Validate
- Re-run same case
- Measure score improvement
- If improved, add to pattern library

## Example: Frontend Loss Analysis

**Case:** `frontend-vuejs-vue-ENV-00`
**Baseline score:** 100%
**Gremlin score:** 80%

**Baseline output:**
```
Risk: Environment variable exposure through Webpack
What if: .env vars bundled into client-side code?
```

**Action:** Add to `patterns/breaking.yaml`:
```yaml
frontend:
  patterns:
    - "What if environment variables are accidentally bundled into client-side code and exposed in browser?"
    - "What if sensitive config (API keys, tokens) leaks through build process?"
```

**Re-run result:** Score 80% → 100% ✓

---

## Automation Idea

```python
# evals/pattern_learner.py
def extract_winning_patterns(baseline_output: str) -> list[str]:
    """Extract 'what if' scenarios from baseline that beat Gremlin."""
    # Parse baseline output
    # Extract novel risks
    # Format as pattern
    return new_patterns

def suggest_pattern_additions(losses: list[EvalResult]):
    """Suggest new patterns based on eval losses."""
    for loss in losses:
        if loss.baseline_score - loss.gremlin_score > 10:
            patterns = extract_winning_patterns(loss.baseline_output)
            print(f"Suggest adding to {loss.domain}:")
            for p in patterns:
                print(f"  - {p}")
```
