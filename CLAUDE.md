# nilan_connect

Home Assistant custom integration for Nilan Gateway and Genvex Connect ventilation
units. All device communication lives in the [nilan_proxy](https://github.com/HairingX/nilan_proxy)
library; this repository is the Home Assistant layer on top of it.

Protocol work, register addresses and per model behaviour belong in `nilan_proxy`,
not here. That library is meant to be usable outside Home Assistant.

## Layout

| Path | Purpose |
|---|---|
| `custom_components/nilan_connect/__init__.py` | Config entry setup, creates the proxy |
| `custom_components/nilan_connect/config_flow.py` | Discovery, manual setup, reconfigure |
| `custom_components/nilan_connect/entity.py` | Base entity all platforms inherit |
| `custom_components/nilan_connect/{sensor,binary_sensor,climate,switch,number,button,select}.py` | Platforms |
| `custom_components/nilan_connect/manifest.json` | Version and the `nilan_proxy` pin |
| `custom_components/nilan_connect/translations/` | `en.json`, `da.json`, mirrored by `strings.json` |

**Files here use CRLF line endings.** Preserve them. Rewriting a file with LF turns
a three line change into a whole file diff.

## Releasing

**The version is never edited by hand, and the draft release is never published by
hand.** Both are done for you, and doing either yourself breaks the release. See the
pitfalls below.

1. **Merge a pull request into `main`.** `.github/workflows/release-drafter.yml`
   creates or updates a **draft release**, computing the next version and writing the
   changelog from merged pull request titles.
2. **Check the draft** at
   [releases](https://github.com/HairingX/nilan_connect/releases). It is named
   `vX.Y.Z`.
3. **Run the `Release` workflow from the Actions tab.** That is the release step.
   Do not press Publish on the draft.

`Release` takes an optional version. Leave it empty and it reads the version from the
newest draft; fill it in to jump a minor or major without relabelling merged pull
requests. Either way it hands the version to the composite action in
`.github/actions/release-publish`, which does the whole thing in one direction:

```
validate version -> check the tag is free -> bump manifest.json -> commit -> push
-> tag -> zip custom_components/nilan_connect
-> capture the draft body, delete the draft -> gh release create
```

The zip attached to the release is what HACS installs, because `hacs.json` sets
`zip_release` and `filename`.

`.github/workflows/release-dev.yml` zips and uploads only, with no version bump. It
is `workflow_dispatch` and is for trying a build without cutting a release.

### How the next version number is chosen

`.github/release-drafter.yml` resolves it from the labels on the merged pull
requests:

| Label on the PR | Result |
|---|---|
| `major` | major bump |
| `minor` | minor bump |
| `patch` | patch bump |
| no label | **patch bump**, this is the default |

The same file groups the changelog by label (`breaking-change`, `enhancement` /
`feature request`, `bug` / `fix` / `bugfix`, `chore`, `dependencies`) and drops
anything labelled `skip-changelog`. An autolabeler adds `bug` for branches named
`fix/...` and `feature request` for `feature/...`.

So: **to release anything other than a patch, label the pull request before merging
it**, or type the version into `Release`.

### Pitfall: never publish the draft by hand

Publishing the draft creates the tag immediately, at whatever `main` points to. The
version bump would then land *after* the tag, so the tag would carry the previous
version. That is exactly what the old event driven workflow did, and every tag it
produced is wrong:

```
tag v1.0.2 -> manifest.json says 1.0.1
tag v1.0.3 -> manifest.json says 1.0.1
tag v1.0.4 -> manifest.json says 1.0.3
tag v1.0.5 -> manifest.json says 1.0.4
```

`Release` bumps, commits and only then tags, so the tag and the manifest agree.
Publishing by hand also builds and attaches nothing at all now, because nothing
listens for `release: published` any more, which would leave HACS with a release
carrying no zip.

### Only `version` is release managed

`requirements`, and everything else in `manifest.json`, is a normal code change and
belongs in the pull request. Only `version` is written by the release.

### Releasing alongside nilan_proxy

`manifest.json` pins the library under `requirements`, and Home Assistant pip
installs it from PyPI at setup. **Bumping the pin here without releasing
`nilan_proxy` first leaves the integration unable to install its dependency.**
Order: release `nilan_proxy` to PyPI, confirm the version is there, then release
`nilan_connect`.

## Conventions

- **Every platform inherits `NilanConnectEntityBase`.** Availability, update
  subscriptions, unique id and device info live there. Add cross cutting entity
  behaviour to the base rather than per platform.
- **Entities are push based.** `should_poll` is `False`. The proxy calls the
  registered handlers from its receive thread, and the base entity turns that into
  `schedule_update_ha_state()`, which hands the write back to the event loop and is
  safe to call from a thread.
- **`available` is a property, not `_attr_available`.** It reports
  `proxy.is_available()`. Home Assistant only reads it when state is written, so
  the proxy also pushes a notification when it flips; without that push the entity
  would keep its last state forever.
- **A missing value is unknown, a missing device is unavailable.**
  `proxy.get_value()` returning `None` gives unknown, which is correct. Do not
  substitute zero or a last known value for either.
- **Adding an entity**: guard it with `proxy.provides_value(key)` so it only
  appears on models that have the point, and add the translation key to
  `strings.json` and every file in `translations/`.
- **Do not raise from `async_setup_entry` for a transient problem.** Raise
  `ConfigEntryNotReady` and let Home Assistant retry; it backs off
  5s, 10s, 20s and so on up to 10 minutes, indefinitely. Never build a retry loop
  on top of that.

## Validation

`.github/workflows/hacs-validate.yml` runs Hassfest and HACS validation on pushes to
`main`, on pull requests, and on demand from the Actions tab. There are no unit tests
in this repository; the logic that can be tested without Home Assistant lives in
`nilan_proxy`, which has a suite.

**It deliberately carries no `schedule`.** GitHub disables workflows that have one
after 60 days of repository inactivity, and that is how this workflow silently
stopped running, taking Hassfest and HACS validation with it. If a nightly run is
ever wanted, expect to re-enable the workflow by hand from time to time.
