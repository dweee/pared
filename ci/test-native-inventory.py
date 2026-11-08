#!/usr/bin/env python3
"""Inventory drift and native check routing cannot silently omit advertised roots."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('native_matrix', ROOT/'ci/matrix.py')
matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matrix)


class CompleteNativeInventory(unittest.TestCase):
    def setUp(self):
        self.inventory = json.loads((ROOT/'nix/platforms.json').read_text())
        self.declared = {'packages': {system: names+(['default'] if system=='aarch64-darwin' else [])
                            for system,names in self.inventory.items()},
                         'checks': {system:['cleanup'] for system in self.inventory}}

    def test_all_platforms_route_all_exports_and_their_native_checks(self):
        jobs = matrix.jobs(self.inventory,self.declared,'darwin')['include']+matrix.jobs(self.inventory,self.declared,'others')['include']
        identities = {(j['set'],j['system'],j['package']) for j in jobs}
        expected = {('packages',system,name) for system,names in self.inventory.items() for name in names}
        expected |= {('checks',system,'cleanup') for system in self.inventory}
        self.assertEqual(identities,expected)
        self.assertEqual(len(jobs),len(identities))
        self.assertTrue(all(j['runner']==matrix.RUNNERS[j['system']] for j in jobs))

    def test_new_package_or_platform_requires_explicit_classification(self):
        for update in ['package','system','missing']:
            declared = copy.deepcopy(self.declared)
            if update=='package':declared['packages']['x86_64-linux'].append('new-export')
            elif update=='system':declared['checks']['x86_64-darwin']=['new-check']
            else:declared['packages'].pop('aarch64-linux')
            with self.subTest(update=update),self.assertRaises(ValueError):
                matrix.jobs(self.inventory,declared,'others')

    def test_native_check_selection_is_supported_and_unknown_selection_fails(self):
        jobs = matrix.jobs(self.inventory,self.declared,'others','cleanup')['include']
        self.assertEqual({(j['set'],j['system']) for j in jobs},{('checks','x86_64-linux'),('checks','aarch64-linux')})
        with self.assertRaises(ValueError):matrix.jobs(self.inventory,self.declared,'others','unknown')

    def test_every_workflow_builds_all_outputs_and_isolates_artifact_names(self):
        for family in ['darwin','others']:
            workflow = yaml.safe_load((ROOT/f'.github/workflows/{family}-actions.yml').read_text())
            steps = workflow['jobs']['build']['steps']
            build = next(s for s in steps if s.get('name','').startswith('Evaluate and build every output'))
            self.assertIn('target=".#$TARGET_SET.$TARGET_SYSTEM.$TARGET_PACKAGE"',build['run'])
            self.assertIn('-- nix build "$target^*"',build['run'])
            exports = [s['with']['name'] for job in ['build','publish'] for s in workflow['jobs'][job]['steps']
                       if s.get('uses','').startswith(('actions/upload-artifact@','actions/download-artifact@'))]
            self.assertEqual(len(exports),2)
            self.assertEqual(exports[0],exports[1])
            self.assertIn('${{ matrix.set }}',exports[0])
            self.assertIn("github.event_name != 'pull_request'",workflow['jobs']['publish']['if'])


if __name__=='__main__':unittest.main()
