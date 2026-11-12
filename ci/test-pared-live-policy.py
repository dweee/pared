#!/usr/bin/env python3
"""Prevent loss of the full Pared matrix or its required macOS 27 route."""
import hashlib,json,re,unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
class LivePolicy(unittest.TestCase):
 def test_complete_native_inventory_and_cleanup(self):
  policy=json.loads((ROOT/'.fork-ci.json').read_text());inventory=json.loads((ROOT/'nix/platforms.json').read_text());rows={r['system']:r for r in policy['matrix']}
  self.assertEqual(set(rows),set(inventory));self.assertEqual(sum(len(v) for v in inventory.values()),13)
  for system,names in inventory.items():
   self.assertEqual(set(rows[system]['packages']),set(names));self.assertEqual(rows[system]['checks'],['cleanup'])
  self.assertEqual(rows['aarch64-darwin']['runner'],'xcode-27');self.assertEqual((policy['upstream'],policy['branch']),('4evy/pared','master'))
 def test_trusted_sync_and_channel_runner(self):
  sync=yaml.safe_load((ROOT/'.github/workflows/upstream-sync.yml').read_text());job=sync['jobs']['upstream'];revision=job['with']['tool-revision']
  self.assertEqual(revision,'b8caba7f1506fdf2d770e36fb95852ac7446bcd2');self.assertIn('on',yaml.load((ROOT/'.github/workflows/upstream-sync.yml').read_text(),Loader=yaml.BaseLoader));self.assertTrue(job['uses'].endswith('@'+revision));self.assertIs(job['with']['auto-merge'],False);self.assertIn("GUARDED_UPSTREAM_SYNC_ENABLED == 'true'",job['if'])
  channel=yaml.safe_load((ROOT/'.github/workflows/release-channels.yml').read_text());self.assertEqual(channel['jobs']['build_aarch64_darwin']['runs-on'],'xcode-27');self.assertIn('promote',channel['jobs'])
 def test_installed_helpers_match_hash_manifest(self):
  for name,expected in json.loads((ROOT/'ci/channel-tool-hashes.json').read_text()).items():self.assertEqual(hashlib.sha256((ROOT/'ci'/name).read_bytes()).hexdigest(),expected,name)
 def test_all_helper_tests_remain_in_pr_checks(self):
  workflow=yaml.safe_load((ROOT/'.github/workflows/pr-checks.yml').read_text())
  scripts='\n'.join(step.get('run','') for step in workflow['jobs']['test']['steps'])
  self.assertIn('PyYAML==6.0.3',scripts)
  self.assertIn('for test in ci/test-*.py; do python3 "$test"; done',scripts)
if __name__=='__main__':unittest.main()
