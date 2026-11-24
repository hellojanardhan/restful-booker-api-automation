# GitHub Actions Day 1--Day 7: 10/10 Master Commands & Practice Cheat Sheet

**Project:** Restful Booker API Automation Framework\
**Coverage:** Day 1--Day 7\
**Purpose:** One practical reference for terminal commands, Git, Pytest,
workflow YAML, expressions, reports, dependencies, reusable workflows,
composite actions, matrix, cron, PR validation, debugging and revision.

> **Important:** This document contains four kinds of reference
> material: terminal commands, Pytest commands, GitHub Actions YAML
> syntax, and GitHub Actions expressions. YAML keys such as `runs-on`,
> `needs`, and `strategy` are not terminal commands.

------------------------------------------------------------------------

# 1. Terminal commands

Run commands from the repository root unless otherwise mentioned.

  -------------------------------------------------------------------------------------------------------------------
  Goal                    Windows PowerShell                            Ubuntu / Git Bash
  ----------------------- --------------------------------------------- ---------------------------------------------
  Current directory       `Get-Location`                                `pwd`

  List files              `Get-ChildItem`                               `ls -la`

  Change directory        `cd folder_name`                              `cd folder_name`

  Create directory        `New-Item -ItemType Directory reports`        `mkdir -p reports`

  Print a message         `Write-Output "Hello"`                        `echo "Hello"`

  Python version          `python --version`                            `python --version`

  Pip version             `python -m pip --version`                     `python -m pip --version`

  Upgrade pip             `python -m pip install --upgrade pip`         `python -m pip install --upgrade pip`

  Install dependencies    `python -m pip install -r requirements.txt`   `python -m pip install -r requirements.txt`

  List installed packages `python -m pip list`                          `python -m pip list`
  -------------------------------------------------------------------------------------------------------------------

Useful Ubuntu shell commands in GitHub-hosted runners:

``` bash
pwd
ls -la
mkdir -p reports
test -f reports/report.html && echo "Report exists" || echo "Report missing"
```

------------------------------------------------------------------------

# 2. Git commands

``` bash
git status
git branch
git branch --show-current
git switch main
git switch -c feature/github-actions-practice
git add .
git commit -m "Add GitHub Actions workflow"
git push -u origin feature/github-actions-practice
git pull
git diff
git log --oneline -5
```

Typical practice sequence:

``` bash
git switch -c feature/pr-validation
# Make your workflow changes
git status
git add .github/workflows/
git commit -m "Add PR validation workflow"
git push -u origin feature/pr-validation
```

Then open a pull request from `feature/pr-validation` into `main`.

------------------------------------------------------------------------

# 3. Pytest commands

Run from the repository root. Use marker names registered in your own
`pytest.ini`.

  ------------------------------------------------------------------------------------------------------------
  Goal                                Command
  ----------------------------------- ------------------------------------------------------------------------
  Run all tests                       `python -m pytest`

  Verbose output                      `python -m pytest -v`

  Show print output                   `python -m pytest -s`

  Verbose + print output              `python -m pytest -v -s`

  Collect tests only                  `python -m pytest --collect-only`

  Run one file                        `python -m pytest tests/test_auth.py`

  Run one test                        `python -m pytest tests/test_auth.py::test_create_token`

  Select by test name                 `python -m pytest -k "booking"`

  Run smoke tests                     `python -m pytest -m smoke -v`

  Run regression tests                `python -m pytest -m regression -v`

  Stop after first failure            `python -m pytest -x`

  Short traceback                     `python -m pytest --tb=short`

  Generate HTML report                `python -m pytest -v --html=reports/report.html --self-contained-html`

  Generate Allure results             `python -m pytest --alluredir=reports/allure-results`
  ------------------------------------------------------------------------------------------------------------

Example `pytest.ini`:

``` ini
[pytest]
markers =
    smoke: Critical API tests
    regression: Full regression tests
    authentication: Authentication tests
```

Example test markers:

``` python
import pytest

@pytest.mark.smoke
def test_health_check():
    ...

@pytest.mark.regression
def test_create_booking():
    ...
```

Install report dependencies if the project uses them:

``` bash
python -m pip install pytest-html
python -m pip install allure-pytest
```

------------------------------------------------------------------------

# 4. Workflow files and core YAML syntax

Workflow files belong in:

``` text
.github/workflows/
```

Example structure:

``` text
.github/
└── workflows/
    ├── api-tests.yml
    ├── pr-validation.yml
    ├── nightly-regression.yml
    ├── matrix-tests.yml
    └── reusable-api-tests.yml
```

  -----------------------------------------------------------------------
  YAML key / event                    Purpose
  ----------------------------------- -----------------------------------
  `name`                              Workflow display name

  `on`                                Events that trigger the workflow

  `push`                              Trigger on push

  `pull_request`                      Trigger on PR activity

  `workflow_dispatch`                 Manual trigger

  `schedule`                          Scheduled trigger

  `branches`                          Branch filter

  `paths`                             Changed-file filter

  `jobs`                              Define jobs

  `runs-on`                           Select runner

  `steps`                             Ordered job steps

  `uses`                              Call an action

  `run`                               Execute shell commands

  `with`                              Configure action inputs

  `env`                               Environment variables

  `needs`                             Job dependencies

  `if`                                Conditional execution

  `strategy` / `matrix`               Matrix configurations

  `fail-fast`                         Cancel matrix jobs after a failure

  `max-parallel`                      Limit concurrent matrix jobs

  `include` / `exclude`               Add/remove matrix combinations

  `timeout-minutes`                   Set timeout

  `continue-on-error`                 Allow a step/job failure without
                                      failing the workflow

  `outputs`                           Expose step/job outputs

  `concurrency`                       Control overlapping workflow runs

  `permissions`                       Set workflow token permissions

  `defaults`                          Set default shell or working
                                      directory
  -----------------------------------------------------------------------

## 4.1 Push trigger

``` yaml
on:
  push:
    branches:
      - main
```

Equivalent compact syntax:

``` yaml
on:
  push:
    branches: [main]
```

## 4.2 Pull request trigger

``` yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
```

For `pull_request`, `branches: [main]` filters the PR's target/base
branch.

## 4.3 Manual trigger

``` yaml
on:
  workflow_dispatch:
```

## 4.4 Multiple triggers

``` yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

## 4.5 Path filters

``` yaml
on:
  push:
    branches: [main]
    paths:
      - "tests/**"
      - "config/**"
      - "requirements.txt"
      - ".github/workflows/**"
```

A path filter restricts the workflow to matching changed files. Include
all files whose changes should run the workflow. Be aware that path
filters can cause a required PR check not to run for some changes;
design required checks carefully.

------------------------------------------------------------------------

# 5. Standard Python + Pytest workflow

``` yaml
name: API Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  api_tests:
    name: API Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest -v
```

`actions/checkout` checks out the repository. `actions/setup-python`
selects the Python version. `run` executes shell commands on the runner.

------------------------------------------------------------------------

# 6. Environment variables, secrets and GitHub Environments

## 6.1 YAML configuration

``` yaml
jobs:
  api_tests:
    runs-on: ubuntu-latest
    environment: QA
    env:
      BASE_URL: ${{ vars.BASE_URL }}
      BOOKER_USERNAME: ${{ secrets.BOOKER_USERNAME }}
      BOOKER_PASSWORD: ${{ secrets.BOOKER_PASSWORD }}
```

-   `vars.NAME` reads a GitHub Actions variable.
-   `secrets.NAME` reads a GitHub Actions secret.
-   `environment: QA` attaches the job to the GitHub Environment named
    `QA`. Its configured variables and secrets become available subject
    to environment rules and approvals.

## 6.2 Read values in Python

``` python
import os

base_url = os.getenv("BASE_URL")
username = os.getenv("BOOKER_USERNAME")
password = os.getenv("BOOKER_PASSWORD")
```

## 6.3 Safe presence check

``` yaml
- name: Check configuration
  run: |
    python -c "import os; print('BASE_URL configured:', bool(os.getenv('BASE_URL')))"
    python -c "import os; print('Username configured:', bool(os.getenv('BOOKER_USERNAME')))"
    python -c "import os; print('Password configured:', bool(os.getenv('BOOKER_PASSWORD')))"
```

Never print secret values or commit credentials into YAML or source
code.

------------------------------------------------------------------------

# 7. HTML reports and artifacts

## 7.1 Generate a Pytest HTML report

``` bash
mkdir -p reports
python -m pytest -v --html=reports/report.html --self-contained-html
```

## 7.2 Upload the report

``` yaml
- name: Upload HTML report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: pytest-html-report
    path: reports/report.html
    retention-days: 7
    if-no-files-found: warn
```

Remember:

-   `if: always()` attempts the upload even if earlier steps failed.
-   It does not create a report that does not exist.
-   The report path must match the upload path.
-   The action name is `actions/upload-artifact` (singular).

## 7.3 Allure results and report

Install the Python integration:

``` bash
python -m pip install allure-pytest
```

Generate results:

``` bash
python -m pytest --alluredir=reports/allure-results
```

Generate the browsable HTML report using the separate Allure CLI:

``` bash
allure generate reports/allure-results -o reports/allure-report --clean
```

Allure CLI also needs a compatible Java runtime. On an Ubuntu runner,
install/configure Java and Allure CLI before using `allure generate`.
The `allure-pytest` Python package alone does not install the Allure
CLI.

For a Windows local machine, use the installed Allure executable
available on PATH. Do not invoke Windows-only `cmd.exe` or `allure.bat`
on an Ubuntu runner.

------------------------------------------------------------------------

# 8. Job dependencies, conditions and outputs (Day 6)

## 8.1 `needs`: smoke before regression

``` yaml
jobs:
  smoke_tests:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Run smoke tests here"

  regression_tests:
    needs: smoke_tests
    runs-on: ubuntu-latest
    steps:
      - run: echo "Run regression tests here"
```

A dependent job is skipped by default when a required job fails or is
skipped. Hosted jobs normally use separate runners, so checkout and
dependency installation should be repeated in each job.

## 8.2 Multiple dependencies

``` yaml
needs: [smoke_tests, api_validation]
```

## 8.3 Status functions

``` yaml
if: success()
if: failure()
if: always()
if: cancelled()
```

Examples:

``` yaml
- name: Upload report
  if: always()
  uses: actions/upload-artifact@v4
```

``` yaml
notify:
  needs: [smoke_tests, regression_tests]
  if: failure()
  runs-on: ubuntu-latest
  steps:
    - run: echo "A test job failed"
```

## 8.4 Step output and job output

``` yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      target_env: ${{ steps.set_env.outputs.env_name }}
    steps:
      - name: Set output
        id: set_env
        run: echo "env_name=QA" >> "$GITHUB_OUTPUT"

  use_output:
    needs: prepare
    runs-on: ubuntu-latest
    steps:
      - name: Read output
        run: echo "Environment: ${{ needs.prepare.outputs.target_env }}"
```

Use outputs for small, non-secret values. Use artifacts to transfer
files. Never pass secrets through job outputs.

------------------------------------------------------------------------

# 9. Contexts and expressions

``` yaml
${{ github.event_name }}
${{ github.ref }}
${{ github.base_ref }}
${{ github.sha }}
${{ matrix.python-version }}
${{ matrix.os }}
${{ needs.prepare.outputs.target_env }}
${{ steps.step_id.outputs.name }}
${{ vars.BASE_URL }}
${{ secrets.BOOKER_PASSWORD }}
${{ success() }}
${{ failure() }}
${{ always() }}
${{ cancelled() }}
```

For a PR, `github.base_ref` is the target branch name. `github.ref`
commonly refers to a PR merge ref rather than `refs/heads/main`.

------------------------------------------------------------------------

# 10. Matrix strategy (Day 7)

## 10.1 Python versions

``` yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

Use the selected version:

``` yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
```

## 10.2 OS × Python matrix

``` yaml
jobs:
  api_tests:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      max-parallel: 2
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
```

This produces four combinations (2 operating systems × 2 Python
versions).

## 10.3 Exclude a combination

``` yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python-version: ["3.10", "3.11", "3.12"]
    exclude:
      - os: windows-latest
        python-version: "3.10"
```

## 10.4 Include extra matrix data

``` yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    include:
      - python-version: "3.12"
        test-type: "full-regression"
```

Access the value using `${{ matrix.test-type }}` where it is defined.

-   `fail-fast: true` is the default; a matrix failure cancels queued
    and in-progress matrix jobs.
-   `fail-fast: false` lets other matrix jobs continue.
-   `max-parallel: 2` allows at most two matrix jobs at once.
-   `exclude` removes matching combinations.
-   `include` adds values to combinations or adds combinations.

------------------------------------------------------------------------

# 11. Cron schedule (Day 7)

Cron fields:

``` text
minute hour day-of-month month day-of-week
```

Examples in UTC:

  Schedule                   Cron
  -------------------------- ----------------
  Every day at 2 AM UTC      `0 2 * * *`
  Every day at 8:30 PM UTC   `30 20 * * *`
  Every 6 hours              `0 */6 * * *`
  Every 30 minutes           `*/30 * * * *`
  Monday at 9 AM UTC         `0 9 * * 1`
  Weekdays at 10 AM UTC      `0 10 * * 1-5`

2:00 AM IST = 8:30 PM UTC on the previous calendar day:

``` yaml
on:
  schedule:
    - cron: "30 20 * * *"
  workflow_dispatch:
```

Scheduled workflows run from the default branch. Start times can be
delayed during high GitHub Actions load; cron is not an exact-time
guarantee.

------------------------------------------------------------------------

# 12. PR validation and required status checks

## 12.1 PR trigger

``` yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
```

## 12.2 Run smoke tests

``` yaml
- name: Run smoke tests
  run: python -m pytest -m smoke -v
```

## 12.3 Required status checks (GitHub UI, not terminal commands)

1.  Open repository Settings.
2.  Go to Branches or Rulesets.
3.  Create a rule for `main`.
4.  Enable requiring a pull request before merging, if desired.
5.  Enable requiring status checks to pass before merging.
6.  Select the exact check name after the PR workflow has run.
7.  Save the rule.

The workflow produces the check; branch protection/rulesets enforce the
merge requirement. Ensure required checks are actually reported for
every PR path that must be protected.

------------------------------------------------------------------------

# 13. Reusable workflows (additional Day 6 practice)

A reusable workflow lets one workflow call another workflow. It is
useful when several repositories or workflows need the same job/pipeline
logic.

## 13.1 Create a reusable workflow

File: `.github/workflows/reusable-api-tests.yml`

``` yaml
name: Reusable API Tests

on:
  workflow_call:
    inputs:
      python-version:
        description: Python version to use
        required: false
        type: string
        default: "3.12"

jobs:
  api_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest -v
```

## 13.2 Call the reusable workflow

In another workflow:

``` yaml
name: Call Reusable API Tests

on:
  workflow_dispatch:

jobs:
  call_api_tests:
    uses: ./.github/workflows/reusable-api-tests.yml
    with:
      python-version: "3.12"
```

Key points:

-   Reusable workflows are stored in `.github/workflows/`.
-   They declare `on: workflow_call`.
-   They are called at the job level using `jobs.<job_id>.uses`.
-   Inputs are declared under `workflow_call.inputs` and passed using
    `with`.
-   A reusable workflow can contain multiple jobs.

------------------------------------------------------------------------

# 14. Composite actions (additional Day 6 practice)

A composite action packages multiple steps into one reusable action. It
is useful for repeating setup logic inside workflows.

## 14.1 Create a composite action

File: `.github/actions/setup-python/action.yml`

``` yaml
name: Setup Python Project
description: Set up Python and install project dependencies

runs:
  using: composite
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"

    - name: Install dependencies
      shell: bash
      run: |
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
```

## 14.2 Call the composite action

``` yaml
steps:
  - name: Checkout repository
    uses: actions/checkout@v5

  - name: Set up project
    uses: ./.github/actions/setup-python
```

Key points:

-   Composite action metadata is in `action.yml`.
-   A local composite action can live under
    `.github/actions/<action-name>/`.
-   It declares `runs: using: composite`.
-   Each `run` step in a composite action must specify a shell.
-   A composite action bundles steps; it does not define multiple jobs.

## 14.3 Reusable workflow vs composite action

  Feature           Reusable workflow          Composite action
  ----------------- -------------------------- ---------------------------
  Purpose           Reuse workflow/job logic   Reuse multiple steps
  Location          `.github/workflows/`       `.github/actions/`
  Invocation        Job-level `uses`           Step-level `uses`
  Multiple jobs     Yes                        No
  Typical example   Shared CI pipeline         Shared Python setup steps

------------------------------------------------------------------------

# 15. Complete smoke → regression → notification example

This demonstrates job dependencies and failure notification logic.
Replace the example test commands with the actual project commands.

``` yaml
name: Smoke Regression Pipeline

on:
  workflow_dispatch:

jobs:
  smoke_tests:
    name: Smoke Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
      - name: Run smoke tests
        run: python -m pytest -m smoke -v

  regression_tests:
    name: Regression Tests
    needs: smoke_tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
      - name: Run regression tests
        run: python -m pytest -m regression -v

  notify:
    name: Failure Notification Placeholder
    needs: [smoke_tests, regression_tests]
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Report failure in log
        run: echo "Smoke or regression job failed"
```

Expected scenarios:

  Smoke   Regression   Notification
  ------- ------------ --------------
  Pass    Pass         Skipped
  Fail    Skipped      Runs
  Pass    Fail         Runs

The notification example writes to the job log; it does not send an
email or chat notification.

------------------------------------------------------------------------

# 16. Workflow debugging and validation

Useful commands:

``` bash
python --version
python -m pip --version
python -m pip list
python -m pytest --collect-only
python -m pytest -v
git status
git diff
```

Check report existence on Ubuntu:

``` bash
ls -la reports
test -f reports/report.html && echo "Report exists" || echo "Report missing"
```

Check environment variable presence without exposing values:

``` bash
python -c "import os; print('BASE_URL configured:', bool(os.getenv('BASE_URL')))"
```

Common problems:

  -----------------------------------------------------------------------
  Error / symptom                     What to check
  ----------------------------------- -----------------------------------
  `ModuleNotFoundError`               Dependencies, working directory and
                                      Python import paths

  `Invalid URL`                       `BASE_URL` includes `https://` and
                                      is the API root

  Bad credentials                     Secret values and environment
                                      scope; do not print secrets

  Missing HTML report                 `pytest-html` installed and report
                                      flags supplied

  Artifact not found                  Report generation path matches
                                      artifact upload path

  `cmd.exe` not found on Ubuntu       Replace Windows-only commands with
                                      Linux-compatible commands

  Multiple workflows run on one push  Inspect the `on.push` trigger in
                                      every workflow file

  Regression skipped                  Check `needs` dependency results
                                      and job conditions

  Matrix combinations cancelled       Check `fail-fast`

  Scheduled run not visible           Workflow exists on default branch
                                      and cron is valid
  -----------------------------------------------------------------------

### Debug logging

GitHub Actions supports repository-level Actions variables:

-   `ACTIONS_STEP_DEBUG` = `true`
-   `ACTIONS_RUNNER_DEBUG` = `true`

Enable these only when needed, review logs carefully, and never print
secrets.

### Workflow run review

In GitHub: 1. Open the repository's Actions tab. 2. Select the workflow
run. 3. Open the job. 4. Expand each step to inspect logs. 5. Check the
summary and artifacts. 6. Re-run failed jobs or the workflow after
correcting the issue.

------------------------------------------------------------------------

# 17. Additional useful workflow syntax

## 17.1 Timeout

``` yaml
jobs:
  api_tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
```

## 17.2 Concurrency

Avoid overlapping runs for the same branch/ref:

``` yaml
concurrency:
  group: api-tests-${{ github.ref }}
  cancel-in-progress: true
```

Use this carefully: a newer run can cancel an older run in the same
concurrency group.

## 17.3 Permissions

Apply least privilege:

``` yaml
permissions:
  contents: read
```

Add only the permissions your workflow needs.

## 17.4 Default shell

``` yaml
defaults:
  run:
    shell: bash
```
