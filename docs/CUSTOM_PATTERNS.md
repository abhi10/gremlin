# Custom Patterns Guide

Add domain-specific patterns to make Gremlin smarter for your codebase.

---

## Quick Start

### 1. Create a patterns file

```yaml
# .gremlin/patterns.yaml (project-level, auto-loaded)
# OR my-patterns.yaml (passed via --patterns flag)

domain_specific:
  image_processing:
    keywords: [image, photo, upload, resize, thumbnail, cdn]
    patterns:
      - "What if EXIF rotation metadata is ignored during resize?"
      - "What if CDN cache serves stale image after update?"
      - "What if concurrent uploads overwrite each other?"
```

### 2. Use your patterns

```bash
# Auto-loaded from .gremlin/patterns.yaml
gremlin review "image upload flow"

# Or explicitly via --patterns flag
gremlin review "image upload" --patterns @my-patterns.yaml
```

---

## Pattern File Format

```yaml
# Universal patterns (apply to every analysis)
universal:
  - category: "Your Category Name"
    patterns:
      - "What if X happens?"
      - "What if Y fails?"

# Domain-specific patterns (apply when keywords match)
domain_specific:
  your_domain:
    keywords: [keyword1, keyword2, keyword3]
    patterns:
      - "What if scenario A?"
      - "What if scenario B?"
```

### Key Rules

1. **Keywords trigger domains** - When user's scope contains any keyword, that domain's patterns are included
2. **Universal patterns always apply** - Use for cross-cutting concerns
3. **Patterns merge, don't replace** - Your patterns add to built-in patterns (93+)
4. **Duplicates are auto-removed** - Safe to overlap with built-in patterns

---

## Writing Effective Patterns

### Pattern Anatomy

```
What if [condition/event] [causes/leads to] [negative outcome]?
```

### Good Patterns

| Pattern | Why It Works |
|---------|--------------|
| `What if the CDN cache serves stale images after S3 update?` | Specific, actionable, real failure mode |
| `What if EXIF rotation is ignored and portrait images display sideways?` | Technical detail + user impact |
| `What if two users upload to the same filename simultaneously?` | Concrete race condition |

### Weak Patterns (Avoid)

| Pattern | Problem |
|---------|---------|
| `What if something goes wrong?` | Too vague |
| `What if the database fails?` | Generic, no specific scenario |
| `What if there's a security issue?` | No actionable detail |

### Pattern Sources

Best patterns come from:
1. **Production incidents** - "This broke last month"
2. **Code reviews** - "I've seen this bug pattern before"
3. **Postmortems** - "Root cause was X"
4. **Domain expertise** - "In image processing, you always need to handle..."

---

## Real-World Examples

### E-commerce Domain

```yaml
domain_specific:
  ecommerce:
    keywords: [cart, checkout, order, inventory, sku, product]
    patterns:
      - "What if inventory is reserved but payment fails, leaving phantom holds?"
      - "What if a flash sale causes thundering herd on inventory checks?"
      - "What if SKU changes mid-checkout and price differs at confirmation?"
      - "What if order confirmation email sends before payment is finalized?"
```

### Media Processing Domain

```yaml
domain_specific:
  media:
    keywords: [video, audio, transcode, ffmpeg, stream, encode]
    patterns:
      - "What if transcoding job times out on large files?"
      - "What if source video has unsupported codec?"
      - "What if HLS segments are generated out of order?"
      - "What if audio track is missing and player crashes?"
```

### Multi-tenant SaaS

```yaml
domain_specific:
  multitenancy:
    keywords: [tenant, organization, workspace, team, account]
    patterns:
      - "What if tenant ID is missing from query and data leaks across orgs?"
      - "What if admin impersonation bypasses tenant isolation?"
      - "What if shared cache key returns wrong tenant's data?"
      - "What if tenant deletion leaves orphaned resources?"
```

### Machine Learning Pipeline

```yaml
domain_specific:
  ml_pipeline:
    keywords: [model, inference, training, feature, embedding, prediction]
    patterns:
      - "What if model version mismatch between training and inference?"
      - "What if feature store returns stale embeddings?"
      - "What if batch prediction job processes same record twice?"
      - "What if model A/B routing sends traffic to untested variant?"
```

---

## Pattern Loading Priority

Patterns are loaded and merged in this order:

1. **Built-in patterns** (`patterns/breaking.yaml`) - 93 patterns
2. **Incident patterns** (`patterns/incidents/*.yaml`) - From `gremlin learn`
3. **Project patterns** (`.gremlin/patterns.yaml`) - Auto-loaded
4. **Custom patterns** (`--patterns @file.yaml`) - Explicit override

Later patterns merge with earlier ones. Duplicates are removed.

---

## Project-Level Configuration

Create `.gremlin/patterns.yaml` in your repo root for team-wide patterns:

```
my-project/
├── .gremlin/
│   └── patterns.yaml    # Auto-loaded by gremlin review
├── src/
└── README.md
```

Benefits:
- Shared across team (commit to repo)
- Auto-loaded without flags
- Domain expertise captured in code

---

## Testing Your Patterns

### Verify patterns load correctly

```bash
# Check that your domain appears in the list
gremlin patterns list

# Should show your custom domain with pattern count
```

### Test pattern triggering

```bash
# Use a scope that matches your keywords
gremlin review "image upload to CDN" --output md

# Check output mentions your patterns' risks
```

### Iterate on effectiveness

1. Run against known risky code
2. Check if your patterns surface expected risks
3. Refine wording for better LLM understanding
4. Add more specific patterns for missed cases

---

## Learning from Incidents

Use `gremlin learn` to capture patterns from real incidents:

```bash
# Add pattern from incident
gremlin learn "User saw login button after successful OAuth" --domain auth --source prod-incident-42

# Patterns saved to patterns/incidents/prod-incident-42.yaml
```

These are auto-merged into your pattern catalog.

---

## Best Practices

### Do

- **Be specific** - "EXIF rotation ignored" not "image processing fails"
- **Include impact** - "...causing portrait images to display sideways"
- **Use real scenarios** - From incidents, code reviews, postmortems
- **Keep keywords focused** - 3-6 precise keywords per domain
- **Review quarterly** - Remove stale patterns, add new incident learnings

### Don't

- Add generic patterns ("What if there's a bug?")
- Duplicate built-in patterns (they'll be deduplicated anyway)
- Create overly broad domains (split into focused domains instead)
- Forget to test patterns actually trigger on your scopes

---

## Sharing Patterns

### Team sharing

Commit `.gremlin/patterns.yaml` to your repo. Everyone gets team patterns.

### Cross-project sharing

```bash
# Use external patterns file
gremlin review "checkout" --patterns @~/shared-patterns/fintech.yaml
```

### Contributing to Gremlin

Have patterns that could help others? Open a PR to add them to `patterns/breaking.yaml`.

---

## Troubleshooting

### Patterns not loading

```bash
# Check file exists and is valid YAML
cat .gremlin/patterns.yaml | python -c "import yaml, sys; yaml.safe_load(sys.stdin)"

# Run with verbose output
gremlin review "test" --output rich
# Should show "Loaded project patterns: .gremlin/patterns.yaml"
```

### Domain not triggering

```bash
# Check your keywords match the scope
gremlin patterns list
# Look for your domain and its keywords

# Try a scope with exact keyword match
gremlin review "image upload" --output md
```

### Patterns not affecting output

- LLM may not surface every pattern - that's intentional (confidence filtering)
- Try `--threshold 50` to see lower-confidence matches
- Ensure pattern wording is clear and actionable

---

## Reference: Built-in Domains

Gremlin includes patterns for these domains (don't duplicate):

| Domain | Keywords |
|--------|----------|
| auth | auth, login, session, token, oauth, jwt |
| payments | payment, checkout, stripe, billing, charge |
| file_upload | upload, file, image, attachment, s3, storage |
| database | database, query, migration, transaction, sql |
| caching | cache, redis, memcached, invalidation |
| api | api, endpoint, rest, graphql, rate limit |
| concurrency | async, parallel, race, lock, mutex, thread |
| external | webhook, third-party, integration, api call |

See full list: `gremlin patterns list`
