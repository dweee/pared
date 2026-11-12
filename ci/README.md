Native package builds use the explicit platform inventory and pinned flake inputs.
Trusted default-branch jobs read Niks3 through refreshing read-only GitHub OIDC.
Completed selected build dependencies are retained even if a later build fails,
then exported as bounded public data to a separate Niks3 publisher job. The
trusted publisher client is installed before imported data; its own completed
build dependencies are published separately. PR events receive no private reader
and never publish. Keep DAVE_FORK_CI_ENABLED and NIKS3_PUSH_ENABLED enabled for
this fork; the existing ATTIC_PUSH_ENABLED setting remains a compatibility gate.
No active reader or publisher uses Attic credentials.

ci/channels.json records ownership and the existing explicit native application
inventory for shared helper metadata and policy validation. This fork retains
its custom native workflow; tested/stable promotion and scheduled-update workflows are installed by the
reviewed adoption change described below.

The native job keeps the arm64 xcode-27 runner because Package.swift requires
macOS 27, and keeps all upstream CLI checks. See the maintained GitHub runner
reference in .github/workflows/darwin-actions.yml.

The documentation workflow also reads Niks3 on the trusted default branch,
retains the selected docs build graph on failure, and sends bounded store data
to an isolated Linux publisher. It follows this fork's native-cache branch and
manual dispatches. Pages deployment still requires the default branch; cache
publication has its own trust and enable guards. The tag release uses Swift
directly rather than Nix, so it produces no Nix store outputs to publish.

The native platform inventory covers every exported package on all three declared
platforms, with Darwin's `default` recorded as an alias of `pared`. The matrix
compares that inventory with the actual locked flake exports and also schedules
all declared native checks. A new package or unsupported system fails planning
instead of disappearing from coverage. Each selected derivation builds `^*`;
package and check artifacts have separate names. Linux exports use native x86
and ARM workers, while Swift CLI work retains the required xcode-27 Mac worker.
These are cache builds and checks; they do not activate Apple settings or deploy
Pages, and tested/stable promotion follows the separate guarded workflow.


Guarded upstream maintenance and channels
----------------------------------------

The owner installs the maintained guarded upstream-sync caller, scheduled
input/monitor updates and tested/stable channel workflow for `native-cache`.
`.fork-ci.json` tracks `4evy/pared:master`, preserves fork controls and Nix files,
and covers all thirteen declared packages plus cleanup checks on all systems.
Upstream merges stay review-gated (`auto-merge: false`); input PRs reuse the
maintained routine branch. Swift package builds retain native CLI tests.

Both sync and channel Darwin builds require `xcode-27` (macOS 27). After
regenerating channel automation, retain that explicit owner runner override;
`ci/test-pared-live-policy.py` rejects a downgrade to the default Mac runner.
The sync caller pins controller `b8caba7f1506fdf2d770e36fb95852ac7446bcd2`
in both revision fields. Controller PR57 permits `xcode-27` only for
`aarch64-darwin`; other native runner defaults remain unchanged. Installed
channel helpers retain their reviewed controller55 bytes and hash manifest.
Owner review, native checks and explicit enablement of
`GUARDED_UPSTREAM_SYNC_ENABLED` remain required before a live sync.
Prepared adoption does not establish a successful live run.
No job activates Apple settings, deletes model data or deploys Pages.

The cleanup check runs the complete portable activation-shell regression suite on
all three platforms. Darwin and x86 Linux also retain the original Swift suite.
The frozen nixpkgs Swift compiler is marked broken on ARM Linux because its gold
linker fails; ARM cleanup does not require Swift or allow a broken package.
