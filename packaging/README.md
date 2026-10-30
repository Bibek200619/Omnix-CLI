# Omnix CLI packaging

The release workflow builds a Rust `omnix` frontend and a Python engine wheel into
one archive for each supported target. No public release exists yet; the install
script should only be shared after the release workflow has produced and verified
the assets for a tagged version.

## Supported release targets

| Target | Frontend | Engine runtime |
| --- | --- | --- |
| macOS arm64 | Rust release binary | Python 3.12+ in an isolated venv |
| Linux x86_64 (Ubuntu 22.04 baseline) | Rust release binary | Python 3.12+ in an isolated venv |

Intel macOS, Linux arm64, and Windows are not release targets yet. Add a target only
after its clean-machine CI and terminal-interaction checks pass.

## Install and upgrade

The installer selects the matching release archive, verifies its SHA-256 checksum,
creates an isolated Python virtual environment, installs the engine wheel with the
dependency versions and hashes exported from `ai-cli/uv.lock`, and puts a small
`omnix` launcher in `~/.local/bin`. Python 3.12 or newer, `curl`, and a SHA-256 utility
must be available. Add `~/.local/bin` to `PATH` if the installer reports it is missing.

After a verified release is published, install or upgrade with:

```sh
curl -fsSL https://github.com/Bibek200619/Omnix-CLI/releases/latest/download/install.sh | sh
```

Running the same command again upgrades the application runtime in place. The CLI
keeps project state in each workspace's `.project/` directory and credentials in the
operating system keyring; installation does not modify either.

## Uninstall

After installation, remove the CLI runtime and launcher with:

```sh
sh "${XDG_DATA_HOME:-$HOME/.local/share}/omnix/uninstall.sh"
```

Uninstall removes the app runtime only. It leaves project folders, `.project/` data,
and account credentials unchanged.

## Release verification

The release workflow runs only for a published release whose tag matches the Python
package version. It compiles the Rust binary on native runners, packages the wheel,
generates checksums, and attests the uploaded artifacts. The pull request package
workflow separately verifies clean engine installation, command forwarding, project
initialization, and a non-interactive TUI startup on both release targets.
