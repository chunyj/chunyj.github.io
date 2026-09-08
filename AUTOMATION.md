# Automated site updates

Two GitHub Actions workflows keep this site's content fresh without manual editing.
Both open a **pull request** for review — nothing is ever merged automatically.

## 1. Publications sync (`sync-publications.yml`)

- **What it does**: runs [scripts/sync_publications.py](scripts/sync_publications.py), which
  queries the Semantic Scholar API for this author's paper list and appends any papers not
  already in [_bibliography/papers.bib](_bibliography/papers.bib) (matched by arXiv ID, DOI, or
  normalized title). New entries get `needs_review = {true}` so they're easy to spot.
- **Schedule**: every Monday, 13:00 UTC. Can also be run manually.
- **Setup required**: none — no secrets, no external account needed.
- **After it opens a PR**: check the new entry's `abbr`, add a `preview` image under
  `assets/img/publication_preview/`, set `selected`, then remove `needs_review` before merging.
- **Run manually**: `gh workflow run sync-publications.yml`

## 2. Resume PDF sync (`sync-resume.yml`)

- **What it does**: clones the Overleaf resume project via Overleaf's Git integration,
  recompiles `resume.tex` with `resume.cls` using `latexmk`/`pdflatex`, and copies the result
  into `assets/pdf/resume.pdf`.
- **Schedule**: every January 1 and July 1 (~every 6 months). Can also be run manually.
- **Setup required** (one-time):
  1. In Overleaf: **Account Settings → Git Integration → "Get a Git authentication token"**.
     This is a personal token, separate from your Overleaf login password.
  2. In this GitHub repo: **Settings → Secrets and variables → Actions → New repository
     secret**, name `OVERLEAF_GIT_TOKEN`, value = the token from step 1.
  3. The Overleaf project ID is hardcoded in the workflow (from the project URL
     `overleaf.com/project/<id>`). If the resume ever moves to a different Overleaf project,
     update the ID in `.github/workflows/sync-resume.yml`.
- **Important limitation**: this only syncs the **PDF file**. It does NOT touch
  `_data/cv.yml` (the on-page `/cv` content) or `_bibliography/papers.bib`. If the resume's
  actual content changed — new job, new award, new publication, retitled paper — those need to
  be updated by hand (or by asking Claude to diff the new resume against `_data/cv.yml`).
- **Run manually**: `gh workflow run sync-resume.yml`

## One-time repo setting both workflows depend on

Both workflows use `peter-evans/create-pull-request` to open PRs, which requires:
**Settings → Actions → General → Workflow permissions → "Allow GitHub Actions to create and
approve pull requests"** checked. This was enabled on 2026-09-08. If a future workflow run
fails with `GitHub Actions is not permitted to create or approve pull requests`, that setting
was toggled off again — re-enable it.

## What's still manual

- **CV content** (`_data/cv.yml`): job history, awards, skills, mentoring — no API for this,
  ask Claude to sync it whenever the resume changes.
- **Profile picture** (`assets/img/prof_pic.jpg`): swap the file whenever you have a new photo.
- **Coauthor links** (`_data/coauthors.yml`) and **venue badges** (`_data/venues.yml`): add
  entries here when a new frequent coauthor or publication venue shows up, so the
  `/publications` page links/styles them correctly.
