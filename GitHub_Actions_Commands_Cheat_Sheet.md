# GitHub Actions and Pytest Cheat Sheet

Quick reference for running this API automation project locally and in GitHub Actions.

## Contents

- [Terminal commands](#terminal-commands)
- [Pytest commands](#pytest-commands)
- [Workflow example](#workflow-example)
- [Environment variables and secrets](#environment-variables-and-secrets)
- [Workflow syntax](#workflow-syntax)
- [Troubleshooting CI](#troubleshooting-ci)

## Terminal commands

The GitHub-hosted workflow uses Ubuntu, so its shell commands run in Bash.

| Goal | Command |
| --- | --- |
| Print a message | `echo "Hello GitHub Actions"` |
| Show the current directory | `pwd` |
| List files | `ls -la` |
| Create a directory | `mkdir folder_name` |
| Change directory | `cd folder_name` |
| Check the Python version | `python --version` |
| Upgrade pip | `python -m pip install --upgrade pip` |
| Install project dependencies | `python -m pip install -r requirements.txt` |

## Pytest commands

Run these from the repository root. The project's `pytest.ini` already sets test discovery, verbosity, and report options.

| Goal | Command |
| --- | --- |
| Run all tests | `python -m pytest` |
| Run with verbose output | `python -m pytest -v` |
| Collect tests without running them | `python -m pytest --collect-only` |
| Run one test file | `python -m pytest tests/test_auth.py` |
| Run tests with a marker | `python -m pytest -m authentication` |
| Generate a standalone HTML report | `python -m pytest --html=report.html --self-contained-html` |

Use a marker that is declared in `pytest.ini` or applied to a test. For example, `authentication`, `security`, and `regression` are project markers.

## Workflow example

This example shows a test workflow with push, pull-request, and manual triggers. Store credentials in repository secrets rather than in the workflow file.

```yaml
name: API tests

on:
  push:
    branches: [main]
    paths:
      - "tests/**"
      - "config/**"
      - "requirements.txt"
      - "pytest.ini"
      - ".github/workflows/**"
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  api-tests:
    runs-on: ubuntu-latest
    env:
      BASE_URL: https://restful-booker.herokuapp.com
      BOOKER_USERNAME: ${{ secrets.BOOKER_USERNAME }}
      BOOKER_PASSWORD: ${{ secrets.BOOKER_PASSWORD }}

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest -v --html="${GITHUB_WORKSPACE}/report.html" --self-contained-html

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-html-report
          path: ${{ github.workspace }}/report.html
          retention-days: 7
          if-no-files-found: warn
```

## Environment variables and secrets

Add credentials under **Repository Settings > Secrets and variables > Actions**:

| Name | Use |
| --- | --- |
| `BOOKER_USERNAME` | Username used by the authentication tests |
| `BOOKER_PASSWORD` | Password used by the authentication tests |

`BASE_URL` is the public API root and can be configured as a workflow environment variable. Use the root URL, not an endpoint such as `/auth`.

Read environment variables in Python:

```python
import os

base_url = os.getenv("BASE_URL")
username = os.getenv("BOOKER_USERNAME")
password = os.getenv("BOOKER_PASSWORD")
```

Do not commit real credentials or print them in CI logs. Updating a repository secret does not automatically start a workflow; rerun it from the **Actions** tab.

## Workflow syntax

| Key | Purpose |
| --- | --- |
| `name` | Workflow name |
| `on` | Events that start a workflow |
| `push` | Run after a push |
| `pull_request` | Run for pull-request events |
| `workflow_dispatch` | Allow a manual run |
| `schedule` | Run on a schedule |
| `branches` | Restrict a trigger to branch names |
| `paths` | Restrict a trigger to changed file paths |
| `jobs` | Define work to run |
| `runs-on` | Choose the runner environment |
| `steps` | Define ordered actions or commands |
| `uses` | Use a reusable action |
| `run` | Execute shell commands |
| `with` | Configure an action's inputs |
| `env` | Set environment variables |
| `timeout-minutes` | Set a job or step timeout |

Common conditional expressions:

```yaml
if: always()   # Run even if an earlier step failed
if: success()  # Run only if earlier steps succeeded
if: failure()  # Run only if an earlier step failed
```

## Troubleshooting CI

- Confirm the workflow run is using the intended branch and commit.
- Check that `BOOKER_USERNAME` and `BOOKER_PASSWORD` match the credentials that work locally.
- If authentication responds with `{"reason":"Bad credentials"}`, verify the secret values; the API may return HTTP 200 for invalid credentials.
- Check the workflow logs for dependency installation, test results, and report upload status.
- If a secret was just changed, manually rerun the workflow.
