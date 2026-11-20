# Distribution

## Requirements

| ID | Requirement | Status |
|---|---|---|
| DST-001 | Every GitHub release contains a zip with the contents of `custom_components/<domain>/`. GitHub counts downloads of release assets automatically. | implemented (workflow, untested) |
| DST-002 | HACS installs from this zip (`zip_release: true` in `hacs.json`), so HACS installations are counted too. | implemented (config, untested) |
| DST-003 | The version in the zip (`manifest.json`) matches the release tag. The workflow sets it during the build. | implemented (workflow, untested) |
| DST-004 | The zip can be built locally with `scripts/build_zip.sh`. | implemented |
| DST-005 | User docs explain both paths: HACS and manual installation from the zip. | planned |
| DST-006 | HACS offers releases only, never the default branch (`hide_default_branch`), because a branch has no zip and the install would fail. Alpha and beta versions are GitHub pre-releases and need "Show beta versions" in HACS. | implemented |

## Notes

- Download counts per release via `gh api repos/<owner>/<repo>/releases` (field
  `download_count` per asset).
- Repository: https://github.com/mschmiedel/thermogeist. Releases only when the user asks.
