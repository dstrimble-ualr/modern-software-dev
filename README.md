# modern-software-dev

Teaching examples for the Modern Software Development course. Two versions of the same
small app, each with unit, integration, and end-to-end tests, coverage tooling, CI, a
class playbook of break/fix demos, and a 45-minute presentation deck.

| Project | Stack | Start here |
|---|---|---|
| [dstrimble-example-project/](dstrimble-example-project/) | Node.js, Express, Jest, supertest, Playwright | [README](dstrimble-example-project/README.md), [Playbook](dstrimble-example-project/TESTING_PLAYBOOK.md), [Deck](dstrimble-example-project/TESTING_PRESENTATION.md) |
| [python-example-project/](python-example-project/) | Python, Flask, pytest, pytest-cov, Playwright | [README](python-example-project/README.md), [Playbook](python-example-project/TESTING_PLAYBOOK.md), [Deck](python-example-project/TESTING_PRESENTATION.md) |

Each project is self-contained: `cd` into it and follow its README. CI runs each project's
tests from `.github/workflows/` whenever files under that project change.
