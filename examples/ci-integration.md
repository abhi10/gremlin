# CI/CD Integration Examples

Integrate Gremlin into your continuous integration pipelines for automated risk analysis.

## GitHub Actions

### Example 1: PR Review Bot

Automatically review every pull request:

```yaml
# .github/workflows/gremlin-review.yml
name: Gremlin QA Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for diff

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Gremlin
        run: pip install gremlin-critic

      - name: Run Gremlin Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          git diff origin/${{ github.base_ref }}...HEAD | \
          gremlin review "changes in PR #${{ github.event.pull_request.number }}" \
            --context - \
            --threshold 85 \
            --output md >> $GITHUB_STEP_SUMMARY

      - name: Comment on PR (optional)
        uses: actions/github-script@v6
        if: always()
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync(process.env.GITHUB_STEP_SUMMARY, 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Gremlin QA Review\n\n${review}`
            });
```

### Example 2: Critical Risks Blocker

Block merges if critical risks found:

```yaml
# .github/workflows/gremlin-gate.yml
name: Gremlin Quality Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Gremlin
        run: pip install gremlin-critic

      - name: Analyze Changes
        id: analyze
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          RESULT=$(git diff origin/${{ github.base_ref }}...HEAD | \
            gremlin review "PR changes" --context - --output json)

          CRITICAL=$(echo "$RESULT" | jq '.summary.by_severity.CRITICAL // 0')
          echo "critical_count=$CRITICAL" >> $GITHUB_OUTPUT

          # Save full report
          echo "$RESULT" | jq '.' > gremlin-report.json

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: gremlin-report
          path: gremlin-report.json

      - name: Quality Gate Check
        if: steps.analyze.outputs.critical_count > 0
        run: |
          echo "❌ Found ${{ steps.analyze.outputs.critical_count }} CRITICAL risks"
          echo "Review the Gremlin report and address critical issues before merging."
          exit 1

      - name: Success Message
        if: steps.analyze.outputs.critical_count == 0
        run: echo "✅ No critical risks detected"
```

### Example 3: Scheduled Full Review

Weekly comprehensive review:

```yaml
# .github/workflows/gremlin-weekly.yml
name: Weekly Risk Assessment

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  full-review:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scope:
          - "authentication system"
          - "payment processing"
          - "data storage layer"
          - "API endpoints"
          - "frontend routes"

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Gremlin
        run: pip install gremlin-critic

      - name: Run Review for ${{ matrix.scope }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          gremlin review "${{ matrix.scope }}" \
            --depth deep \
            --threshold 70 \
            --output json > "risk-${{ matrix.scope }}.json"

          gremlin review "${{ matrix.scope }}" \
            --depth deep \
            --threshold 70 \
            --output md > "risk-${{ matrix.scope }}.md"

      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: weekly-risk-reports
          path: |
            risk-*.json
            risk-*.md

      - name: Create Issue for Critical Risks
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          CRITICAL=$(jq '.summary.by_severity.CRITICAL // 0' < "risk-${{ matrix.scope }}.json")

          if [ "$CRITICAL" -gt 0 ]; then
            gh issue create \
              --title "⚠️ Critical risks in ${{ matrix.scope }}" \
              --body-file "risk-${{ matrix.scope }}.md" \
              --label "security,qa-review"
          fi
```

## GitLab CI/CD

### Example 1: Merge Request Review

```yaml
# .gitlab-ci.yml
gremlin-review:
  image: python:3.11-slim
  stage: test
  only:
    - merge_requests

  before_script:
    - pip install gremlin-critic

  script:
    - |
      git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD | \
      gremlin review "MR !$CI_MERGE_REQUEST_IID changes" \
        --context - \
        --output md > gremlin-report.md

    - |
      # Post comment to MR
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        --header "Content-Type: application/json" \
        --data "{\"body\": \"$(cat gremlin-report.md)\"}" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"

  artifacts:
    paths:
      - gremlin-report.md
    expire_in: 30 days

  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

### Example 2: Quality Gate

```yaml
# .gitlab-ci.yml
gremlin-gate:
  image: python:3.11-slim
  stage: test
  only:
    - merge_requests

  before_script:
    - pip install gremlin-critic jq

  script:
    - |
      git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD | \
      gremlin review "MR changes" --context - --output json > report.json

    - CRITICAL=$(jq '.summary.by_severity.CRITICAL // 0' report.json)
    - |
      if [ "$CRITICAL" -gt 0 ]; then
        echo "❌ Found $CRITICAL critical risks - blocking merge"
        exit 1
      fi
    - echo "✅ Quality gate passed"

  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

## CircleCI

### Example: PR Review

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  gremlin-review:
    docker:
      - image: cimg/python:3.11

    steps:
      - checkout

      - run:
          name: Install Gremlin
          command: pip install gremlin-critic

      - run:
          name: Run Review
          command: |
            git diff origin/main...HEAD | \
            gremlin review "PR changes" \
              --context - \
              --output md > gremlin-report.md
          environment:
            ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

      - store_artifacts:
          path: gremlin-report.md

      - run:
          name: Check Critical Risks
          command: |
            RESULT=$(git diff origin/main...HEAD | \
              gremlin review "PR changes" --context - --output json)

            CRITICAL=$(echo "$RESULT" | jq '.summary.by_severity.CRITICAL // 0')

            if [ "$CRITICAL" -gt 0 ]; then
              echo "Found $CRITICAL critical risks"
              exit 1
            fi

workflows:
  version: 2
  pr-review:
    jobs:
      - gremlin-review:
          filters:
            branches:
              ignore: main
```

## Jenkins

### Example: Pipeline Review

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install gremlin-critic'
            }
        }

        stage('Gremlin Review') {
            when {
                changeRequest()
            }
            steps {
                script {
                    def diff = sh(
                        script: "git diff origin/${env.CHANGE_TARGET}...HEAD",
                        returnStdout: true
                    ).trim()

                    sh """
                        echo '${diff}' | \
                        gremlin review 'PR-${env.CHANGE_ID} changes' \
                          --context - \
                          --output md > gremlin-report.md
                    """

                    // Archive report
                    archiveArtifacts artifacts: 'gremlin-report.md'

                    // Check for critical risks
                    def result = sh(
                        script: """
                            echo '${diff}' | \
                            gremlin review 'PR changes' --context - --output json
                        """,
                        returnStdout: true
                    ).trim()

                    def critical = sh(
                        script: "echo '${result}' | jq '.summary.by_severity.CRITICAL // 0'",
                        returnStdout: true
                    ).trim().toInteger()

                    if (critical > 0) {
                        error("Found ${critical} critical risks - blocking merge")
                    }
                }
            }
        }
    }
}
```

## Pre-commit Hook

Catch risks before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Only run if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Skipping Gremlin review (ANTHROPIC_API_KEY not set)"
    exit 0
fi

echo "🔍 Running Gremlin review on staged changes..."

# Get staged diff
DIFF=$(git diff --staged)

if [ -z "$DIFF" ]; then
    exit 0
fi

# Run Gremlin
RESULT=$(echo "$DIFF" | gremlin review "staged changes" --context - --output json)

# Check for critical risks
CRITICAL=$(echo "$RESULT" | jq '.summary.by_severity.CRITICAL // 0')

if [ "$CRITICAL" -gt 0 ]; then
    echo ""
    echo "❌ Found $CRITICAL CRITICAL risks in staged changes:"
    echo "$RESULT" | jq -r '.risks[] | select(.severity == "CRITICAL") | "  - \(.title)"'
    echo ""
    echo "Review these risks before committing."
    echo "To commit anyway: git commit --no-verify"
    exit 1
fi

echo "✅ No critical risks detected"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Docker Integration

### Dockerfile for CI

```dockerfile
FROM python:3.11-slim

# Install Gremlin
RUN pip install gremlin-critic

# Set working directory
WORKDIR /workspace

# Entry point
ENTRYPOINT ["gremlin"]
CMD ["--help"]
```

### Usage in CI

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  gremlin-critic review "feature scope" --output json
```

## Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Gremlin Review
          image: python:3.11
          script:
            - pip install gremlin-critic
            - |
              git diff origin/$BITBUCKET_PR_DESTINATION_BRANCH...HEAD | \
              gremlin review "PR #$BITBUCKET_PR_ID changes" \
                --context - \
                --output md > gremlin-report.md
            - |
              # Check for critical risks
              RESULT=$(git diff origin/$BITBUCKET_PR_DESTINATION_BRANCH...HEAD | \
                gremlin review "PR changes" --context - --output json)

              CRITICAL=$(echo "$RESULT" | jq '.summary.by_severity.CRITICAL // 0')

              if [ "$CRITICAL" -gt 0 ]; then
                echo "Found $CRITICAL critical risks"
                exit 1
              fi
          artifacts:
            - gremlin-report.md
```

## Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Set up Python'

  - script: |
      pip install gremlin-critic
    displayName: 'Install Gremlin'

  - script: |
      git diff origin/$(System.PullRequest.TargetBranch)...HEAD | \
      gremlin review "PR changes" \
        --context - \
        --output md > gremlin-report.md
    displayName: 'Run Gremlin Review'
    env:
      ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'gremlin-report.md'
      artifactName: 'gremlin-report'
    displayName: 'Publish Report'

  - script: |
      RESULT=$(git diff origin/$(System.PullRequest.TargetBranch)...HEAD | \
        gremlin review "PR changes" --context - --output json)

      CRITICAL=$(echo "$RESULT" | jq '.summary.by_severity.CRITICAL // 0')

      if [ "$CRITICAL" -gt 0 ]; then
        echo "##vso[task.logissue type=error]Found $CRITICAL critical risks"
        exit 1
      fi
    displayName: 'Quality Gate'
    env:
      ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)
```

## Best Practices

### 1. Cache Dependencies

**GitHub Actions:**
```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-gremlin
```

### 2. Fail Fast on Critical Risks

Always check for critical risks and fail the pipeline:
```bash
CRITICAL=$(gremlin review "..." --output json | jq '.summary.by_severity.CRITICAL // 0')
[ "$CRITICAL" -eq 0 ] || exit 1
```

### 3. Store Reports as Artifacts

Keep historical reports:
```yaml
- uses: actions/upload-artifact@v3
  with:
    name: gremlin-report-${{ github.sha }}
    path: gremlin-report.*
    retention-days: 90
```

### 4. Use Appropriate Thresholds

- **PR reviews:** `--threshold 85` (high confidence only)
- **Weekly audits:** `--threshold 70` (broader exploration)
- **Pre-commit:** `--threshold 90` (very high confidence)

### 5. Scope Appropriately

```bash
# Good: Review actual changes
git diff | gremlin review "PR changes" --context -

# Less useful: Review entire codebase
gremlin review "entire application"
```

### 6. Rate Limit Considerations

For large PRs or frequent runs, consider:
- Caching reviews for unchanged commits
- Rate limiting review frequency
- Using lower `--depth quick` for frequent checks

## Troubleshooting

### Issue: API Rate Limits

**Solution:** Add delays between reviews:
```bash
for scope in "${SCOPES[@]}"; do
  gremlin review "$scope" --output json > "risk-$scope.json"
  sleep 5  # Wait 5 seconds between reviews
done
```

### Issue: Large Diffs Timeout

**Solution:** Review specific files instead:
```bash
# Review only changed files in critical paths
git diff --name-only | grep "src/auth/" | while read file; do
  gremlin review "changes in $file" --context @"$file" --output md
done
```

### Issue: Missing ANTHROPIC_API_KEY

**Solution:** Add to CI secrets and verify:
```bash
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Error: ANTHROPIC_API_KEY not set"
  exit 1
fi
```

## Next Steps

- **View sample outputs:** Check [sample-outputs/](sample-outputs/) directory
- **Format options:** See [output-formats.md](output-formats.md)
- **Context usage:** See [with-context.md](with-context.md)
- **Basic usage:** Back to [basic-usage.md](basic-usage.md)
