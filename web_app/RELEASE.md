# Python CLI release process

The website currently offers source-preview setup. No public tag, GitHub Release,
PyPI distribution, signed package, or platform binary has been verified. Package
version 0.1.0 is not evidence of a stable distribution.

Current main includes `.github/workflows/cli-release-artifacts.yml`. It runs on
GitHub Release publication, checks for `vVERSION`, builds wheel/source artifacts,
creates checksums and GitHub provenance attestations, and uploads them. No
published release was present in the 2026-10-30 recheck. The workflow does not run
the candidate test suite and rebuilds artifacts; a local candidate check alone
does not verify the bytes that this workflow publishes.

## Verify a candidate

Use Python >=3.12, Git, and uv. From the repository root:

```sh
python3 web_app/scripts/verify-cli-package.py --ref HEAD --output /tmp/omnix-candidate
```

The output path must be new. The script archives only tracked Python CLI source
from the selected commit into a temporary directory, installs frozen development
dependencies on Python 3.12, runs its tests, and builds one wheel and one source
distribution. It installs each artifact in its own fresh environment and checks
the installed package version, CLI help, and local project initialization. It then retains those same artifacts,
`SHA256SUMS`, and `verification.json` in the output directory. It does not alter
the working CLI, tag, push, publish, sign, or call a model provider.

This command is a local candidate pipeline, independent of the website build.
An invalid ref, tag/version mismatch, failing test, build, or install stops it.
Checksums establish file identity; they are not signatures or proof of author.

## Prepare a tagged release

1. Review the Python package version, requirements, license, changes, and known
   limitations on an appropriate branch. Merge through a PR.
2. Choose a reviewed commit and a tag named `vVERSION`, where VERSION exactly
   matches `ai-cli/pyproject.toml`. Never rewrite an existing published tag.
3. Have the maintainer create an annotated tag at that commit, then run the
   candidate verifier with `--ref vVERSION`. The website agent does not create
   or push this tag automatically.
4. Prepare release notes naming the version, commit, Python requirement, source
   preview limitations, setup instructions, and platform/testing scope. Include
   the distinction between stored artifacts/model reports and runtime tests.
5. Prepare a draft release for that tag and review the notes. Publish as a
   prerelease while distributing a preview. Publication triggers the artifact
   workflow; require it to succeed before treating the release as usable. A
   registry publish requires its own verified process and credentials.
6. Retrieve the workflow's wheel, source archive, and `SHA256SUMS`; check their
   hashes and verify each attestation with
   `gh attestation verify <artifact> --repo Bibek200619/Omnix-CLI --signer-workflow Bibek200619/Omnix-CLI/.github/workflows/cli-release-artifacts.yml`.
   Install each downloaded package in an isolated environment and recheck version,
   help, and local initialization. Record the actual published digests and
   verification results. Do not assume rebuilt bytes match local candidates, or
   silently replace artifacts after verification.
7. Only then add a manually verified installation method tied to that release in
   website product data and test its page state. Publication by itself enables
   a release-page link, never an inferred registry or direct-download action.

## Recovery

If verification fails, fix the smallest cause on a branch and rerun into a new
output directory. If a published candidate is faulty, mark the release clearly
and ship a new version/tag; do not silently replace its artifacts. The website
can continue to offer source preview while the distribution issue is resolved.
