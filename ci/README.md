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
its custom native workflow; no tested/stable promotion or scheduled-update
workflow is installed by this change.

The native job keeps the arm64 xcode-27 runner because Package.swift requires
macOS 27, and keeps all upstream CLI checks. See the maintained GitHub runner
reference in .github/workflows/darwin-actions.yml.

The documentation workflow also reads Niks3 on the trusted default branch,
retains the selected docs build graph on failure, and sends bounded store data
to an isolated Linux publisher. It follows this fork's native-cache branch and
manual dispatches. Pages deployment still requires the default branch; cache
publication has its own trust and enable guards. The tag release uses Swift
directly rather than Nix, so it produces no Nix store outputs to publish.
