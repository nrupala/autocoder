# Changelog

All notable changes to AutoCoder are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions per
`pyproject.toml`. Tags: `v<version>` after merge.

## [Unreleased]

### Added
- **Portfolio certification rollout:** `CHANGELOG.md` (this file, Keep a
  Changelog), `ATTRIBUTION.md`, and a `LICENSE` file carrying the MIT text
  the repo already declared in `pyproject.toml` and `README.md` (no
  `LICENSE` file existed before).
- `CONTRIBUTING.md`: PR-flow discipline section (draft PR → CI green →
  owner merges; no direct pushes to `master`; `CHANGELOG` entry under
  Unreleased per PR; semver bump; merge commits reference PR numbers;
  releases tagged `vX.Y.Z`); clone URL corrected to
  `github.com/nrupala/autocoder`.
- MIT license headers on all Python source files.

### Changed
- Version bump `0.1.0` → `0.1.1` (chore) in `pyproject.toml`.

### Notes
- No deploy target found: workflows are CI-only (`tests.yml`, `lint.yml`,
  `typecheck.yml`); `ci_cd_build.py` and `check_repos.py` are developer
  helper scripts, not deploy scripts. Skipped track 2; if a deploy/publish
  step is added later it must delegate to the signed-deploy wrapper before
  first use.
