#!/usr/bin/env python3
"""Validate all advertised package aliases and route native packages and checks."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = {'aarch64-darwin': 'xcode-27', 'aarch64-linux': 'ubuntu-24.04-arm', 'x86_64-linux': 'ubuntu-24.04'}


def jobs(inventory, declared, family, selected='all'):
    packages = declared['packages']
    checks = declared['checks']
    if set(packages) != set(inventory) or (set(packages) | set(checks)) - RUNNERS.keys():
        raise ValueError('Unclassified advertised native system')
    for system, names in packages.items():
        # Darwin default is the same CLI derivation as pared; keep one build.
        expected = set(inventory[system]) | ({'default'} if system == 'aarch64-darwin' else set())
        if set(names) != expected or len(inventory[system]) != len(set(inventory[system])):
            raise ValueError('Native inventory differs from advertised package attributes')
    result = []
    known_names = set()
    for output_set, systems in [('packages', inventory), ('checks', checks)]:
        for system, names in systems.items():
            for name in names:
                if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', name):
                    raise ValueError('Invalid native target name')
                known_names.add(name)
                if system.endswith('-darwin') == (family == 'darwin') and selected in ['all', name]:
                    result.append({'system': system, 'runner': RUNNERS[system], 'package': name, 'set': output_set})
    if selected != 'all' and selected not in known_names:
        raise ValueError('Unknown package or check')
    return {'include': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family', choices=['darwin', 'others'])
    parser.add_argument('--package', default='all')
    args = parser.parse_args()
    inventory = json.loads((ROOT/'nix/platforms.json').read_text())
    expression = 'let f=builtins.getFlake '+json.dumps('git+file://'+str(ROOT))+'; in { packages=builtins.mapAttrs (_: builtins.attrNames) f.packages; checks=builtins.mapAttrs (_: builtins.attrNames) (f.checks or {}); }'
    raw = subprocess.check_output(['nix', 'eval', '--impure', '--json', '--option', 'accept-flake-config', 'false',
        '--option', 'allow-import-from-derivation', 'false', '--option', 'max-jobs', '0', '--option', 'builders', '',
        '--no-update-lock-file', '--no-write-lock-file', '--expr', expression], text=True, timeout=180)
    matrix = jobs(inventory, json.loads(raw), args.family, args.package)
    print(json.dumps(matrix, separators=(',', ':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('has_jobs='+str(bool(matrix['include'])).lower()+'\n')


if __name__ == '__main__':
    main()
