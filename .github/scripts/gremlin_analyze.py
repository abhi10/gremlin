#!/usr/bin/env python3
"""Run Gremlin analysis and write results to JSON file for GitHub Actions."""

import json
import os
import sys
import time


def main():
    scope = sys.argv[1] if len(sys.argv) > 1 else "PR changes"
    context_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else "/tmp/gremlin-report.json"

    context = ""
    if context_file and os.path.exists(context_file):
        with open(context_file) as f:
            context = f.read()

    try:
        from gremlin import Gremlin

        g = Gremlin()
        last_error = None

        for attempt in range(3):
            try:
                if attempt > 0:
                    wait = 15 * attempt
                    print(f"Retry {attempt}/2 after {wait}s...")
                    time.sleep(wait)

                result = g.analyze(scope, context=context if context else None)

                with open(output_file, "w") as f:
                    f.write(result.to_json())

                print(f"Done: {len(result.risks)} risk(s) found")
                sys.exit(0)

            except Exception as e:
                last_error = e
                if "529" in str(e) or "overloaded" in str(e).lower():
                    print(f"API overloaded (attempt {attempt + 1}/3), retrying...", file=sys.stderr)
                    continue
                raise

        raise last_error

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        with open(output_file, "w") as f:
            json.dump({"error": str(e), "risks": [], "scope": scope}, f, indent=2)
        sys.exit(1)


if __name__ == "__main__":
    main()
