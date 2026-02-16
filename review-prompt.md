# Task: Review and Update CLAUDE.md for Gremlin

You are tasked with reviewing and updating the CLAUDE.md file for the Gremlin repository — a Python CLI + library that surfaces QA risk scenarios using curated patterns and LLM reasoning.

## Your Mission

Conduct a comprehensive analysis of the entire codebase and update the CLAUDE.md file to ensure it is 100% accurate, complete, and helpful for future Claude Code interactions.

**Do not make any code changes.** Only update CLAUDE.md.

---

## Analysis Requirements

### 1. Project Overview Verification
- Verify the project description is accurate against actual implementation
- Check if all stated capabilities (CLI, API, Agent) actually exist and work as described
- Confirm the version number matches across all files where it appears
- Confirm the PyPI package name matches what's configured in the build system
- Identify any missing key features or capabilities not mentioned

### 2. Tech Stack & Dependencies
- Read the project build configuration and verify:
  - All runtime dependencies and their version constraints
  - All development dependencies
  - The build system being used
  - The Python version requirement
  - The CLI entry point configuration
- Cross-reference: are any installed packages used in code but missing from docs?
- Cross-reference: are any documented technologies not actually used?

### 3. Development Commands Verification
- Verify all documented setup, test, lint, and run commands actually work
- Check the build config for any additional scripts or commands not documented
- Ensure command descriptions and examples are accurate
- Add any missing commonly-used commands (e.g., coverage, type checking)

### 4. Architecture & Directory Structure
- Scan the entire directory structure using recursive listing
- Verify all documented file paths actually exist
- Identify any significant directories or files not mentioned in CLAUDE.md
- Document actual file naming conventions and patterns used throughout
- Map out the module hierarchy and how packages are organized
- Check for any dead code, deprecated modules, or orphaned files

### 5. Analysis Pipeline Verification
- Trace the actual data flow from user input to final output
- Follow the code path in **both** the CLI and the API entry points
- Document where these paths converge and where they diverge
- **Critical**: Determine if the CLI wraps the API or reimplements the pipeline independently
- Identify any middleware, validation passes, or optional processing steps
- Document what happens at each stage with actual module references

### 6. LLM Provider Layer
- Scan the LLM module directory structure
- Identify which providers are **actually implemented** vs merely referenced or stubbed
- Check the provider registry to see what's registered at runtime
- Identify any deprecated modules and what still imports them
- Document default configuration values (model, temperature, timeouts)
- **Critical**: CLAUDE.md should only claim support for providers that actually work

### 7. Pattern System
- Scan all YAML pattern files across the repository
- Count the actual total patterns (don't trust documented numbers — count them)
- Identify all universal categories and domain-specific domains
- Check for any additional pattern sources (incident files, project-level overrides)
- Document how patterns are discovered, loaded, and merged at runtime
- Document the project-level pattern override convention (if any)

### 8. CLI Commands Deep Scan
- Read the CLI module and catalog every command and subcommand
- For each command, document all flags/options and their defaults
- Verify the documented examples actually work with the current CLI interface
- Identify any commands or flags that exist in code but are missing from docs
- Document context resolution modes (how different input types are handled)

### 9. Programmatic API Surface
- Read the API module and catalog every public class, method, and property
- Verify the documented usage examples match the actual signatures
- Check what's exported from the package's `__init__.py`
- Document any recent changes to initialization or calling patterns

### 10. Agent & Plugin System
- Scan the plugins directory structure
- Read any agent specification files
- Scan for integration/bridge modules that connect agent and CLI
- Document the relationship between agent patterns and CLI patterns
- Verify stated pattern counts for each system

### 11. Evaluation Framework
- Scan the entire evals directory structure
- Document what each script and module does
- Count all test cases (curated and real-world)
- Identify where results, fixtures, and reports are stored
- Document the evaluation methodology (what gets compared, how)
- Verify documented eval commands match the actual script interfaces

### 12. Environment Variables & Configuration
- Search the entire codebase for environment variable references
- Document each variable: where it's used, whether required or optional, default value
- Check if any env vars exist in code but are missing from CLAUDE.md
- Check if any documented env vars no longer exist

### 13. Configuration Files
- Document all configuration files in the project root and their purposes:
  - Build configuration
  - Linter settings
  - Test runner settings
  - Git ignore rules (note any surprising patterns)
  - Any other tooling configuration
- Identify settings that would affect a developer's workflow

### 14. Test Suite
- Scan all test files and count test functions per file
- Verify the total test count matches what CLAUDE.md claims
- Identify the organization: which tests are pure unit tests vs integration tests requiring API keys
- Check the test configuration in the build file
- Document any test fixtures or helpers

### 15. Documentation Inventory
- List all markdown documentation across the repository (root, docs/, evals/)
- Categorize by type: strategic, technical, architecture, guides, blog
- Check for any architecture diagrams or visual assets
- Verify version references in documentation match the actual version
- Note the current project status as stated in the roadmap

### 16. Scripts & Automation
- Scan for any standalone scripts (demo files, utility scripts, generators)
- Check for any CI/CD workflows or GitHub Actions
- Document any build, deployment, or release scripts
- Identify any automation that a developer should know about

### 17. Gotchas & Non-Obvious Behaviors
- Document anything that would trip up Claude Code or a new developer:
  - Modules that are deprecated but still present
  - Features that exist in code but aren't wired into the main flow
  - Configuration defaults that might be surprising
  - `.gitignore` rules that affect which files can be committed
  - Any workarounds currently in use
  - Places where documentation and code disagree

---

## Verification Checklist

Before finalizing the updated CLAUDE.md, run these checks:

- [ ] Every file path mentioned in CLAUDE.md exists on disk
- [ ] Every command documented in CLAUDE.md runs without error
- [ ] Every count (patterns, tests, domains) was independently verified
- [ ] Every claimed capability was confirmed by reading the source
- [ ] No provider, feature, or integration is listed that doesn't actually work
- [ ] All environment variables in the codebase are documented
- [ ] Architecture description matches the actual code flow when traced
- [ ] Version number is consistent across all files

---

## Output Requirements

Create an updated CLAUDE.md that:

1. **Fixes all inaccuracies** found during analysis
2. **Adds missing sections** for undocumented features, commands, or modules
3. **Removes misleading claims** about capabilities that don't exist
4. **Updates all counts** (patterns, tests, domains) to match verified reality
5. **Documents gotchas** that would cause incorrect assumptions
6. **Preserves the branch-first workflow rule** — this is intentional policy, must stay prominent
7. **Keeps the existing structure** where it works — update content, don't reorganize
8. **Is concise** — every line should provide value for working with the code

---

## Process

1. Read the current CLAUDE.md in full
2. Scan the entire directory structure to understand what exists
3. Systematically work through each analysis area above, reading source files
4. Track every discrepancy between CLAUDE.md and reality
5. Write the updated CLAUDE.md with all corrections applied
6. Do a final verification pass: re-read key source files to confirm accuracy

**Remember**: When documentation and code disagree, code wins. Every claim in CLAUDE.md must be verifiable by reading the source.
