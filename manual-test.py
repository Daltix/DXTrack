import time
import argparse
from dxtrack import dxtrack

parser = argparse.ArgumentParser()

parser.add_argument(
    '-s', '--stage', help='Which stage', type=str,
    required=True,
)

args = parser.parse_args()


dxtrack.configure(
    stage=args.stage,
    context='test-{}'.format(args.stage),
    run_id=str(time.time()),
    default_metadata={'default': 'metadata'}
)

try:
    raise ValueError('Test value error')
except ValueError:
    dxtrack.error(metadata={'extra': 'error metadata'})


dxtrack.metric('test_metric', 1000000, metadata={'extra': 'metric metadata'})
