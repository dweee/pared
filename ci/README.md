Native package builds use the explicit platform inventory and pinned flake inputs.
Successful default-branch builds export approved runtime closures to a separate publisher job.
Pull requests never publish. Configure ATTIC_TOKEN and enable DAVE_FORK_CI_ENABLED and
ATTIC_PUSH_ENABLED using repository settings; never commit credentials.

The native job uses the arm64 `xcode-27` image because Package.swift declares macOS 27. It runs the upstream CLI checks instead of disabling them on an older runtime. GitHub documents the image at https://github.blog/changelog/2026-09-10-xcode-27-runner-image-now-runs-on-macos-27/.
