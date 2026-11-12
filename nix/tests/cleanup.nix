{ pkgs }:
let
  inherit (pkgs) lib;
  # Nixpkgs' Swift compiler cannot link on ARM Linux at this frozen revision.
  # The shell behavior remains tested there by the same portable assertions.
  swiftSupported = !(pkgs.stdenv.hostPlatform.isLinux && pkgs.stdenv.hostPlatform.isAarch64);
  package = pkgs.writeShellScriptBin "pared" ''
    printf '%s\n' "$*" >> calls
    exit "''${PARED_TEST_EXIT:-0}"
  '';
  cleanup = pkgs.writeShellScript "pared-cleanup-test" (
    import ../cleanup.nix {
      inherit lib pkgs package;
      policyFile = "policy.json";
      stateDirectory = "state with spaces";
      profilePath = "profile.mobileconfig";
    }
  );
in
pkgs.runCommand "pared-cleanup-regression"
  {
    nativeBuildInputs = [ pkgs.python3 ] ++ lib.optional swiftSupported pkgs.swift;
  }
  ''
    python3 ${../../Tests/activation/activation.py} ${cleanup}
    ${lib.optionalString swiftSupported ''
      swift ${../../Tests/activation/activation.swift} ${cleanup}
    ''}
    touch "$out"
  ''
