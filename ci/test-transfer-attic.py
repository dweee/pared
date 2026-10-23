import importlib.util
import io
import gzip
import subprocess
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location('transfer', Path(__file__).with_name('transfer-attic.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TransferSafetyTests(unittest.TestCase):
    def test_cli_allows_bounded_large_closure_and_rejects_excess_before_transfer(self):
        for mib, expected in [('8192', 0), ('8193', 1), ('0', 1)]:
            with self.subTest(mib=mib), patch.dict(os.environ, {'ATTIC_MAX_CLOSURE_MIB': mib}, clear=True), \
                    patch.object(module.sys, 'argv', ['transfer-attic.py', 'export', '--directory', 'artifact']), \
                    patch.object(module, 'transfer') as transfer, redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(), expected)
                if expected:
                    transfer.assert_not_called()
                else:
                    transfer.assert_called_once_with('export', Path('artifact'), 8192 * 1024 * 1024)

    def test_closure_size_uses_registered_sizes_and_rejects_incomplete_metadata(self):
        paths = ['/nix/store/' + 'a' * 32 + '-one', '/nix/store/' + 'b' * 32 + '-two']
        with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '17\n25\n', '')):
            self.assertEqual(module.closure_size(paths), 42)
        for data in ['17\n', '17\n-1\n', '17\nprivate-path\n']:
            with self.subTest(data=data), patch.object(module.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 0, data, '')):
                with self.assertRaises(ValueError): module.closure_size(paths)

    def test_oversize_registered_closure_is_rejected_before_archive_export(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {}, clear=True), \
                patch.object(module, 'roots', return_value=['/nix/store/' + 'a' * 32 + '-public']), \
                patch.object(module.policy, 'runtime', return_value=['/nix/store/' + 'a' * 32 + '-public']), \
                patch.object(module, 'closure_size', return_value=1025), \
                patch.object(module.subprocess, 'Popen') as process:
            directory = Path(temporary) / 'artifact'
            with self.assertRaises(module.TransferLimitExceeded): module.transfer('export', directory, 1024)
            process.assert_not_called()
            self.assertFalse((directory / 'closure.nar.gz').exists())

    def test_failure_categories_never_include_sensitive_exception_details(self):
        secret = 'private-path-and-credential-fixture'
        cases = [(module.TransferLimitExceeded(secret), 'closure-limit-exceeded'),
                 (OSError(28, secret), 'io-error-28'),
                 (subprocess.CalledProcessError(1, secret, stderr=secret), 'subprocess-failed'),
                 (ValueError(secret), 'invalid-transfer-or-policy-rejected')]
        for error, expected in cases:
            self.assertEqual(module.failure_category(error), expected)
            self.assertNotIn(secret, module.failure_category(error))

    def test_oversize_stream_is_rejected_before_excess_is_written(self):
        target = io.BytesIO()
        with self.assertRaises(ValueError): module.copy_bounded(io.BytesIO(b'x' * 1025), target, 1024)
        self.assertEqual(target.getvalue(), b'')

    def test_bounded_stream_round_trips(self):
        target = io.BytesIO()
        self.assertEqual(module.copy_bounded(io.BytesIO(b'public fixture'), target, 100), 14)
        self.assertEqual(target.getvalue(), b'public fixture')

    def test_manifest_excludes_non_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / 'outputs.txt'
            for value in ['', '/tmp/credential', '/nix/store/' + 'a' * 32 + '-file.drv', '/nix/store/' + 'a' * 32 + '-file/child']:
                manifest.write_text(value)
                with self.subTest(value=value), self.assertRaises(ValueError): module.roots(manifest)

    def test_manifest_preserves_only_unique_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / 'outputs.txt';value='/nix/store/'+'a'*32+'-public'
            manifest.write_text(value+'\n'+value+'\n')
            self.assertEqual(module.roots(manifest), [value])

    def test_import_restores_official_signatures_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = '/nix/store/' + 'a' * 32 + '-custom-package'
            (directory / 'outputs.txt').write_text(root + '\n')
            with gzip.open(directory / 'closure.nar.gz', 'wb') as stream:
                stream.write(b'public data fixture')
            process = MagicMock()
            process.stdin = io.BytesIO()
            process.wait.return_value = 0
            process.poll.return_value = 0
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(module.subprocess, 'Popen', return_value=process), \
                    patch.object(module.subprocess, 'run') as call, patch.object(module.policy, 'runtime', return_value=[root]):
                module.transfer('import', directory, 1024)
            self.assertEqual(call.call_args_list[0].args[0], ['nix-store', '--check-validity', root])
            self.assertEqual(call.call_args_list[1].args[0],
                             ['nix', 'store', 'copy-sigs', '--substituter',
                              'https://cache.nixos.org', '--recursive', root])
            self.assertTrue(call.call_args_list[1].kwargs['check'])
            self.assertEqual(call.call_args_list[1].kwargs['timeout'], 120)

    def test_forbidden_runtime_never_starts_export_or_creates_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'artifact'
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(module, 'roots', return_value=['/nix/store/'+'a'*32+'-root']), \
                    patch.object(module.policy, 'runtime', side_effect=ValueError('blocked')), \
                    patch.object(module.subprocess, 'Popen') as process:
                with self.assertRaises(ValueError): module.transfer('export', directory, 1024)
                process.assert_not_called()
                self.assertFalse((directory / 'closure.nar.gz').exists())

    def test_transfer_refuses_upload_credentials(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {'ATTIC_TOKEN':'synthetic-fixture'}):
            with self.assertRaises(ValueError): module.transfer('export', Path(temporary), 1024)

    def test_workflow_token_is_confined_to_the_isolated_publisher(self):
        for path in Path(__file__).resolve().parents[1].joinpath('.github/workflows').glob('*actions.yml'):
            with self.subTest(workflow=path.name):
                build, separator, publisher = path.read_text().partition('\n  publish:\n')
                self.assertTrue(separator)
                self.assertIn('Configure authenticated private cache reads for trusted builds', build)
                self.assertEqual(publisher.count('secrets.ATTIC_TOKEN'),1)
                self.assertIn('needs: [plan, build]', publisher)
                self.assertIn('--max-jobs 0 --builders', publisher)
                self.assertIn('github.event.repository.default_branch', publisher)
                self.assertLess(publisher.index('Install the trusted pinned Attic client'), publisher.index('ci/transfer-attic.py import'))
                self.assertLess(publisher.index('ci/transfer-attic.py import'), publisher.index('secrets.ATTIC_TOKEN'))
                self.assertNotIn('Evaluate and build the selected native package', publisher)


if __name__ == '__main__': unittest.main()
