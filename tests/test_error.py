import os
import json
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
        except ValueError as e:
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


if __name__ == '__main__':
    unittest.main()
