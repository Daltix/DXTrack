import unittest
from dxtrack import dxtrack


class TestFramework(unittest.TestCase):

    def test_configure(self):
        """
        Test the simple base case
        """
        default_metadata = {'default': 'metadata'}
        dxtrack.configure(
            context='test_error_track',
            stage='test',
            run_id='test_run_id',
            default_metadata=default_metadata
        )
        self.assertEqual(dxtrack.context, 'test_error_track')
        self.assertEqual(dxtrack.stage, 'test')
        self.assertEqual(dxtrack.run_id, 'test_run_id')
        self.assertEqual(dxtrack.default_metadata, default_metadata)

    def test_configure_error(self):
        """
        Test for missing arguments
        """
        with self.assertRaises(ValueError) as e:
            dxtrack.configure(
                context=None,
                stage='test',
                run_id='test_run_id'
            )
            self.assertIn('context', str(e))

        with self.assertRaises(ValueError) as e:
            dxtrack.configure(
                context='test_error_track',
                stage=None,
                run_id='test_run_id'
            )
            self.assertIn('stage', str(e))

        with self.assertRaises(ValueError) as e:
            dxtrack.configure(
                context='test_error_track',
                stage='test',
                run_id=None
            )
            self.assertIn('run_id', str(e))

if __name__ == '__main__':
    unittest.main()
