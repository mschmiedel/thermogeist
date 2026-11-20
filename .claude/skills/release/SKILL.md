---
name: release
description: Prepare and publish a release of the integration as a downloadable zip (GitHub release asset, used by HACS). Use when the user asks to release, tag or ship a version.
---

# Release

Only release when the user explicitly asks.

1. **Checks:** `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`
   all green.
2. **Spec and docs:** statuses correct, user docs in both languages up to date.
3. **Version:** semantic versioning. Agree the version with the user. The tag is `vX.Y.Z`.
4. **Local dry run:** `scripts/build_zip.sh X.Y.Z` – inspect the zip: it must contain the
   integration files at the zip root (`manifest.json` at top level) with the right version.
5. **Release notes:** user-facing, in English, grouped by "New", "Improved", "Fixed",
   "Breaking". Mention anything users must do after updating.
6. **Publish:** create the GitHub release for the tag (after user confirmation). The workflow
   `.github/workflows/release.yml` builds and attaches `<domain>.zip`.
7. **Verify:** the asset exists on the release; HACS shows the new version.

Download counts: `gh api repos/<owner>/<repo>/releases --jq '.[] | {tag: .tag_name, downloads: [.assets[].download_count] | add}'`
