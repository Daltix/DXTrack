import os
import json
import copy
import unittest
import shutil
from dxtrack import dxtrack

output_file = './.dxtrack_output/error.jsonl'

context = 'test_error_track'
stage = 'test'
run_id = 'test_run_id'
default_metadata = {'default': 'metadata'}


class TestErrorTrack(unittest.TestCase):

    def setUp(self):
        shutil.rmtree(output_file, ignore_errors=True)

        dxtrack.configure(
            context=context,
            stage=stage,
            run_id=run_id,
            default_metadata=default_metadata
        )

    def tearDown(self):
        shutil.rmtree(os.path.dirname(output_file))

    def test_error_raw_output(self):
        try:
            raise ValueError('hello')
        except ValueError as _:
            dxtrack.error()
        self.assertTrue(os.path.exists(output_file))
        with open(output_file) as fh:
            err = json.loads(fh.read())
        self.assertEqual(
            {
                'metadata',
                'id',
                'timestamp',
                'run_id',
                'stage',
                'exception',
                'context'
            },
            set(err.keys())
        )
        self.assertEqual(
            {'type', 'value', 'traceback'},
            set(err['exception'].keys())
        )
        self.assertEqual(err['metadata'], default_metadata)

    def test_metadata_merge(self):
        metadata = {'new': 'key'}
        try:
            raise ValueError('hello')
        except ValueError as _:
            dxtrack.error(metadata=metadata)
        with open(output_file) as fh:
            err = json.loads(fh.read())
        expected_metadata = copy.deepcopy(metadata)
        expected_metadata.update(default_metadata)
        self.assertEqual(err['metadata'], expected_metadata)

    def _test_errors(self, n_errors, metadata=None):
        errors = []
        for i in range(0, n_errors):
            try:
                raise ValueError(str(i))
            except ValueError as e:
                errors.append(e)
        dxtrack.errors(errors, metadata=metadata)
        tracked_errors = []
        with open(output_file) as fh:
            for line in fh.readlines():
                tracked_errors.append(json.loads(line))
        return errors, tracked_errors

    def test_errors(self):
        n_errors = 5
        errors, tracked_errors = self._test_errors(n_errors)

        self.assertEqual(len(tracked_errors), n_errors)
        for i, entry in enumerate(tracked_errors):
            self.assertEqual(entry['exception']['value'], str(i))
            self.assertEqual(entry['exception']['traceback'], None)

    def test_errors_incl_metadata(self):
        n_errors = 5
        metadata = {'test': 'value'}
        errors, tracked_errors = self._test_errors(n_errors, metadata=metadata)

        for i, entry in enumerate(tracked_errors):
            self.assertEqual(entry['exception']['value'], str(i))
            self.assertEqual(entry['metadata']['test'], metadata['test'])


if __name__ == '__main__':
    unittest.main()
