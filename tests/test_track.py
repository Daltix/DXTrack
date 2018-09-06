import shutil
import os
import json
import unittest
from dxtrack import dxtrack

output_file = './.dxtrack_output/metrics.jsonl'
context = 'test_metric_track'
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
        shutil.rmtree(output_file)

    def test_error_raw_output(self):
        self.assertTrue(os.path.exists(output_file))
        try:
            raise ValueError('hello')
        except ValueError as _:
            dxtrack.error()
        with open(output_file) as fh:
            err = json.load(fh)
        self.assertEqual(
            {
                'context': context,
                'exception': {

                },
                'stage': stage,
                'metadata': default_metadata,
                'timestamp': 5,
                'run_id': run_id,
                'error_id': hash(1),
                'error_group': hash(1),
            },
            err
        )