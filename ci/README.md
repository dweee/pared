Native package builds use the explicit platform inventory and pinned flake inputs.
Successful default-branch builds export approved runtime closures to a separate publisher job.
Pull requests never publish. Configure ATTIC_TOKEN and enable DAVE_FORK_CI_ENABLED and
ATTIC_PUSH_ENABLED using repository settings; never commit credentials.
