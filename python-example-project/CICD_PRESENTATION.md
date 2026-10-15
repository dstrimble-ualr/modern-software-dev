---
marp: true
paginate: true
---

# CI/CD with GitHub Actions

### Running every test on every merge, for `python-example-project`

30–45 minutes. One workflow file, three jobs, two ways to make it go red.

<!--
Timing budget is in each slide title. The slides sum to 43 minutes. For a 30-minute version, skip the
slides marked (optional) and show the LIVE demos from runs you started before class instead of pushing live.

Before class:
  1. In the repo root, make sure main is green on the Actions tab.
  2. Push the two demo branches (LIVE slides below) and open them as draft PRs, so their runs have
     finished by the time you get there. You can still push a fresh commit live if time allows.
  3. Open three tabs: the repo's Actions tab, the open PR list, and .github/workflows/python.yml.
Renders with Marp (VS Code extension or `npx @marp-team/marp-cli`); reads fine as plain Markdown too.
Follows TESTING_PRESENTATION.md: students should already know the three test layers.
-->

---

## Agenda `⏱ 1 min`

| Minutes | Topic |
|---|---|
| 0–8 | Why CI/CD, the three terms, and what we built |
| 8–25 | Reading the workflow, one block at a time |
| 25–35 | LIVE: a green run, a red PR, and a bug only the pipeline sees |
| 35–43 | Protecting `main`, debugging CI, what deployment adds, wrap-up |

By the end you should be able to open `.github/workflows/python.yml`, say what runs when,
and explain why a PR got a red X.

---

## The problem CI solves `⏱ 2 min`

Last session we wrote 15 tests. They help only if someone runs them.

- "It passed on my machine": a dependency in your venv that isn't in `requirements.txt`
- "I forgot to run the E2E tests": they take longer, so they get skipped
- "Who broke `main`?": three PRs merged this morning, and none of them ran anything

**Continuous integration** fixes this with one rule: every change gets tested
**automatically, on a clean machine, before and after it reaches `main`.**

<!--
Ask: who has pulled main and found it broken? What did it cost to find which commit did it?
CI makes "which commit broke it" a question you never have to ask: every commit has a check mark or an X.
-->

---

## Three terms people mix up `⏱ 3 min`

| Term | What happens automatically | Who decides to release |
|---|---|---|
| **Continuous Integration** | Every push and PR is built and tested | n/a, nothing is released |
| **Continuous Delivery** | ...and every green `main` produces a **ready-to-ship artifact** | A human clicks "deploy" |
| **Continuous Deployment** | ...and every green `main` **goes to production** | Nobody: the pipeline does it |

Each row includes the one above it. **CD** means either of the bottom two, depending on who's talking.

**This project today:** CI, plus the first half of delivery. The pipeline builds the Docker image,
proves it starts, and saves it. Nothing is deployed anywhere.

<!--
The difference between delivery and deployment is a human decision, not a technical one.
Plenty of good teams stop at delivery on purpose: a person picks when to release.
We'll add the deploy step in a later unit. Today is about the gate, not the destination.
-->

---

## The pipeline at a glance `⏱ 2 min`

```
 PR opened / commit pushed / merged to main
                │
                ▼
┌───────────────────────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐
│ fast-tests        (×3 Pythons)│    │ e2e-tests           │    │ docker-image             │
│  pip install                  │    │  install Chromium   │    │  docker build            │
│  pytest tests/unit            │──► │  pytest tests/e2e   │──► │  docker run              │
│  pytest tests/integration     │    │  screenshots on     │    │  smoke_test.py           │
│  coverage → summary + report  │    │  failure            │    │  save image (main only)  │
└───────────────────────────────┘    └─────────────────────┘    └──────────────────────────┘
        ~40 s, in parallel                  ~1 min                       ~40 s
```

Fast and cheap first, slow and expensive last. Each arrow means **"only if everything to the left passed."**

It's the test pyramid from last time, now drawn as a pipeline.

<!--
Point out that the third box is new: the first two jobs test the code, the third tests the thing we'd ship.
Times are rough; show the real ones on the Actions tab.
-->

---

## GitHub Actions vocabulary `⏱ 2 min`

| Word | Meaning | In our file |
|---|---|---|
| **Workflow** | One YAML file in `.github/workflows/` | `python.yml` |
| **Event** | What starts it | `push`, `pull_request`, `workflow_dispatch` |
| **Job** | A group of steps on **one fresh machine** | `fast-tests`, `e2e-tests`, `docker-image` |
| **Runner** | That machine: a clean Ubuntu VM, thrown away after the job | `runs-on: ubuntu-latest` |
| **Step** | One shell command (`run:`) or one reusable action (`uses:`) | `run: pytest tests/unit` |
| **Action** | A packaged, reusable step someone published | `actions/checkout@v4` |
| **Artifact** | A file a job saves for you to download | coverage HTML, the Docker image |

**Jobs share nothing.** That's why every job starts with checkout and install again.

<!--
The "fresh machine" point causes most beginner confusion. Your laptop has years of installed packages;
the runner has nothing but Ubuntu, Python, and Docker. That's a feature: it's the honest test.
-->

---

## Where the file lives `⏱ 1 min`

```
modern-software-dev/                 ← the GitHub repo
├── .github/workflows/
│   ├── node.yml                     ← the Node project's pipeline
│   └── python.yml                   ← ours
├── dstrimble-example-project/
└── python-example-project/
```

GitHub only reads workflows from `.github/workflows/` **at the repo root**. A `.github/` folder
inside `python-example-project/` would be ignored. So every command needs to run in the subfolder:

```yaml
defaults:
  run:
    working-directory: python-example-project
```

<!--
This is the monorepo pattern: one repo, several projects, one workflow per project.
In your own team repo the project is probably at the root and you don't need `defaults`.
-->

---

## Triggers: when does it run? `⏱ 2 min`

```yaml
on:
  push:
    branches: [ main ]     # every merge (or direct push) to main
  pull_request:
    branches: [ main ]     # every PR aimed at main, re-run on each new commit
  workflow_dispatch:       # adds a "Run workflow" button on the Actions tab
```

| You do | It runs? |
|---|---|
| Push commits to `feature/login` with no PR | No |
| Open a PR from `feature/login` → `main` | **Yes**, and again on every push to that branch |
| Merge the PR | **Yes**, on `main`: tests the merged result |
| Click "Run workflow" | **Yes** |

Why test again after merging? The PR tested *your branch*. `main` might have moved since then.
The merge commit combines both, and nobody has tested it yet.

<!--
There's no `paths:` filter (the Node workflow has one). With a filter, a PR that only touches the Node
project skips this workflow. If this workflow is a required check, that PR then waits forever for a status
that never arrives. Running an extra two minutes is cheaper than explaining that bug.
-->

---

## Concurrency and permissions (optional) `⏱ 2 min`

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

permissions:
  contents: read
```

**Concurrency:** push three commits to a PR in a minute, and only the newest one matters.
The older runs get cancelled. Runs on `main` are never cancelled, so every merge gets its own result.

**Permissions:** each run gets a `GITHUB_TOKEN`. We ask for the least it needs: read the code.
A test job has no reason to be able to push commits or edit issues.

`${{ ... }}` is an **expression**: GitHub fills it in before the job starts.

<!--
Least privilege matters more than it looks. Workflows run code from PRs, and dependencies run code
at install time. If something malicious runs, a read-only token limits what it can do.
-->

---

## Job 1: fast tests, three Pythons at once `⏱ 2 min`

```yaml
  fast-tests:
    name: Unit and integration tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: [ '3.12', '3.13', '3.14' ]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -r requirements.txt
      - name: Unit tests
        run: pytest tests/unit
      - name: Integration tests
        run: pytest tests/integration
```

A **matrix** turns one job into three, one per version, running in parallel. The README promises
"Python 3.12 or newer", and this is where we check that promise.

`fail-fast: false` lets the other versions finish when one fails, so you can see which versions broke.

<!--
Ask: why are unit and integration separate steps when `pytest` would run both? So the red X names the layer.
"Unit tests failed" is a better first clue than "pytest failed".
`cache: pip` keeps downloaded packages between runs, keyed on requirements.txt. Change that file and the cache resets.
-->

---

## Conditional steps, summaries, artifacts `⏱ 2 min`

```yaml
      - name: Coverage (unit + integration)
        if: matrix.python-version == '3.12'
        run: pytest --cov --cov-report=term-missing --cov-report=html --cov-report=json

      - name: Add coverage table to the job summary
        if: matrix.python-version == '3.12'
        run: python scripts/coverage_summary.py >> "$GITHUB_STEP_SUMMARY"

      - name: Upload HTML coverage report
        if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@v4
        with:
          name: python-coverage-report
          path: python-example-project/htmlcov/
```

- **`if:`** skips a step unless the condition is true. Coverage is the same on every version, so we measure it once.
- **`$GITHUB_STEP_SUMMARY`**: anything you write to this file shows up as Markdown on the run's page.
- **Artifacts**: files the runner saves before it is thrown away. Download them from the run page.

<!--
Artifact paths are relative to the repo root, not the working-directory default. That's why the
path starts with python-example-project/. It's an easy mistake to make in a monorepo.
-->

---

## Job 2: end-to-end, only if the fast tests pass `⏱ 2 min`

```yaml
  e2e-tests:
    needs: fast-tests   # only spend the slow minutes if the fast tests pass
    steps:
      ...
      - run: playwright install --with-deps chromium
      - run: pytest tests/e2e --screenshot only-on-failure
      - name: Upload failure screenshots
        if: failure()
        uses: actions/upload-artifact@v4
```

- **`needs:`** creates the arrow in the picture. If `fast-tests` fails, this job shows as **skipped**.
- With a matrix, `needs: fast-tests` waits for **all three** versions to pass.
- **`if: failure()`** runs a step only when an earlier step failed. A screenshot of the broken page
  tells you more than a timeout message.

The order is about cost: a unit test failure shows up in 40 seconds, so nobody waits for a browser download to learn about it.

---

## Job 3: test the thing you ship `⏱ 3 min`

```yaml
  docker-image:
    needs: e2e-tests
    env:
      IMAGE: python-example-project:${{ github.sha }}
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t "$IMAGE" .
      - run: docker run -d --name app -p 8000:8000 "$IMAGE"
      - run: python3 scripts/smoke_test.py http://localhost:8000
      - name: Show container logs
        if: always()
        run: docker logs app
```

Jobs 1 and 2 test **the code in a checkout**. Users never run a checkout. They'd run the **image**.
The image has its own Dockerfile, its own installed packages, and its own start command.

A **smoke test** is a short check that the built thing turns on: it serves the page, login works,
widgets come back. `scripts/smoke_test.py` checks four things using only the standard library.

Tagging with `github.sha` (the commit ID) means every image traces back to exactly one commit.

<!--
Ask: look at the Dockerfile. It runs `pip install flask`, not `pip install -r requirements.txt`.
The tests installed requirements.txt. If someone adds a runtime dependency to requirements.txt and imports it,
which job catches it? Only this one: the container crashes on import, and the smoke test fails.
(That's exercise 3.) `if: always()` means logs print even when the smoke test fails, which is when you need them.
-->

---

## Delivery, not deployment `⏱ 1 min`

```yaml
      - name: Save the image as a release candidate
        if: github.ref == 'refs/heads/main'
        run: docker save "$IMAGE" | gzip > image.tar.gz
      - name: Upload the release candidate
        if: github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v4
        with:
          name: python-example-project-image
          retention-days: 7
```

On `main` only, the tested image is kept. It's a **release candidate**: the exact bytes that passed every check.

**Build once, ship that build.** A deploy step later should pick up this file, not rebuild from source
and hope it comes out the same.

```bash
gh run download <run-id> --name python-example-project-image
docker load -i image.tar.gz
docker run --rm -p 8000:8000 python-example-project:<sha>
```

---

## LIVE: a green run `⏱ 2 min`

On the **Actions** tab, open the latest run on `main`. Walk through it:

1. **The graph:** three Python boxes, then E2E, then the image job. Click a box to see its steps.
2. **A step's log:** expand "Unit tests" to see the same pytest output you get locally.
3. **The summary:** scroll down to the coverage table and the image tag and size.
4. **Artifacts:** the coverage report and the image, at the bottom of the summary.

Then open any merged PR: the checks list at the bottom is the same run, seen from the PR.

<!--
If there's no recent run on main, click "Run workflow" now; it takes about 3 minutes.
Ask: how many machines did this run use? Five: three for the matrix, one for E2E, one for the image.
-->

---

## LIVE: a red PR `⏱ 4 min`

Break the login rule in `app/auth_utils.py`, then open a PR:

```python
    return len(creds["username"]) > 0 or len(creds["password"]) > 0   # was: and
```

```bash
git switch -c demo/red-unit
git commit -am "Demo: login only needs one field"
git push -u origin demo/red-unit
gh pr create --draft --fill
gh pr checks --watch
```

Expected on the PR:
- All three **Unit and integration tests** jobs fail at the **Unit tests** step:
  `FAILED tests/unit/test_auth_utils.py::TestHasLoginFields::test_true_only_when_both_fields_are_non_empty`
- **End-to-end tests** and **Build and smoke-test** show as **skipped**
- The merge box says **"Some checks were not successful"**

<!--
Reading a failure, in order: which job is red, which step is red, then the last 20 lines of that step's log.
`gh run view --log-failed` prints only the failing step's log in the terminal.
Optional aside: the integration tests (6 passed locally) would NOT have caught this. No integration test sends
a body without a password. The unit test is the only layer guarding it. That's the coverage gap from last session.
Fix: push the revert to the same branch, watch the checks go green, then close the PR without merging.
-->

---

## LIVE: a bug only the pipeline sees `⏱ 4 min`

In `app/__main__.py`, change the address the server listens on:

```python
create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))   # was "0.0.0.0"
```

```bash
make test && make test-e2e          # locally: 12 passed, 3 passed. All green.
```

Push it as a second PR (`demo/bad-bind`). Expected:
- Fast tests: green. E2E: green. They run the server on the same machine, so `127.0.0.1` is fine.
- **Build and smoke-test: red** at the smoke test step, after 30 seconds: `FAIL  server did not start on http://localhost:8000`
- "Show container logs" still runs and prints the clue: `Running on http://127.0.0.1:8000`

Inside a container, `127.0.0.1` means **the container itself**. Requests forwarded from outside never reach it.

<!--
This is the "works on my machine" bug in its purest form. Every test passes, and the shipped artifact is unusable.
It's also why the logs step is `if: always()`.
To reproduce without GitHub: `make docker-build`, `docker run --rm -p 8000:8000 python-example-project`, `make smoke`.
Fix: revert, push, green. Close the PR.
-->

---

## Make the checks matter: protect `main` `⏱ 2 min`

A red X that people can merge anyway is just a suggestion. Make it a rule:

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**
- Enforcement status: **Active** (a new ruleset is not enforced until you set this)
- Target branches: **Include default branch** (`main`)
- ✅ **Require a pull request before merging**
- ✅ **Require status checks to pass**, then add:
  - `Unit and integration tests (Python 3.12)`, `(Python 3.13)`, `(Python 3.14)`
  - `End-to-end tests (Playwright)`
  - `Build and smoke-test the Docker image`
- Optionally: **Require branches to be up to date before merging**

Now the merge button stays grey until every check is green.

<!--
Check names only show up in the picker after they have run at least once, so do this after the first green run.
Each matrix entry is its own check, so list all three.
"Up to date" makes people merge main into their branch first, so the PR run tests what the merge will produce.
That's slower but stricter. The push-to-main run is the safety net if you leave it off.
This repo is public, so rulesets are available on a free account; private repos need a paid plan.
-->

---

## "It passes locally but fails in CI" (optional) `⏱ 2 min`

| Symptom in the log | Usual cause |
|---|---|
| `ModuleNotFoundError` | Installed in your venv, missing from `requirements.txt` |
| `FileNotFoundError`, or a missing import | The file was never committed: check `git status` |
| Same, but the file *is* committed | Case: macOS ignores `App.py` vs `app.py`; Linux doesn't |
| Fails only on 3.12 | You used something newer than the oldest version you support |
| Passes on re-run, fails sometimes | A flaky test: timing, ordering, or shared state |
| Times out waiting for a server | It never started, or it's listening somewhere else (Demo 2) |

To reproduce CI locally: fresh venv, `pip install -r requirements.txt`, then the same commands.
Every step in the YAML matches a `make` target. CI just runs your Makefile on a fresh machine.

<!--
"Re-run failed jobs" is useful but dangerous: a test that passes on re-run is still flaky. Fix it or it will
train everyone to ignore red.
-->

---

## What deployment would add (optional) `⏱ 2 min`

Not in our file yet. This is the shape of the job we'd add:

```yaml
  deploy:
    needs: docker-image
    if: github.ref == 'refs/heads/main'
    environment: production          # can require a named person to click Approve
    permissions:
      packages: write                # to push to GitHub's container registry
    steps:
      - uses: actions/download-artifact@v4
        with: { name: python-example-project-image, path: python-example-project }
      - run: docker load -i image.tar.gz
      - run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin
      - run: docker tag ... ghcr.io/<owner>/python-example-project:${{ github.sha }} && docker push ...
      - run: ...                     # roll out: kubectl, a hosting platform's CLI, etc.
```

New ideas this would bring in: **secrets** (credentials the log never prints), **environments**
(protection rules and approvals), and a **registry** (where servers pull images from).

Before any of that is safe, this app needs real password hashing and a real session token (see the README).

<!--
Delivery vs deployment again: with `environment: production` requiring a reviewer, this is still continuous
delivery, because a human approves. Remove the reviewer and it becomes continuous deployment.
-->

---

## What to take away `⏱ 2 min`

1. **CI is a rule, not a tool:** every change is tested automatically, on a clean machine,
   before and after it reaches `main`.
2. **Order the pipeline by cost.** Fast tests first, slow tests next, packaging last. `needs:` draws the arrows.
3. **Test the artifact, not just the code.** The image job caught a bug that 15 green tests missed.
4. **Delivery ≠ deployment.** We produce a release candidate on every merge. Shipping it is a separate decision.
5. **A check only matters if it blocks the merge.** Protect `main`.

For your team project: by the final presentation, every PR should have a green check on it.
Be ready to show the workflow and name what it does *not* check.

---

## Exercises

1. Add a **lint** job (`pip install ruff`, `ruff check .`) that runs alongside `fast-tests`, not before it.
   Should `e2e-tests` need it?
2. The README says "Python 3.12 or newer". Is that true, or just untested below 3.12?
   Add `'3.11'` to the matrix and find out. Then decide: widen the promise or keep the matrix honest.
3. Add `requests` to `requirements.txt` and `import requests` in `app/__init__.py`. Which jobs pass?
   Which one fails, and why? Fix the Dockerfile so the image installs what the app needs and nothing else.
4. Add a smoke check to `scripts/smoke_test.py` that logout clears the cookie.
5. Set up the ruleset from the "protect `main`" slide on your team's repo, then try to merge a red PR.
6. Write the `deploy` job's first half for real: push the image to `ghcr.io` on merges to `main`.
   What permission did you have to add?
