import time
import argparse
import random
from dxtrack import dxtrack

parser = argparse.ArgumentParser()
parser.add_argument(
    '-ne', '--n_errors', help='Number of errs to send', type=int, default=0
)
parser.add_argument(
    '-nm', '--n_metric_messages', help='Number of metric entries to send',
    type=int, default=0
)
parser.add_argument(
    '-name', '--metric_name', help='Metric name',
    type=str, default='test_metric'
)
parser.add_argument(
    '-c', '--context', help='Context to use',
    type=str, default='test_context'
)
parser.add_argument(
    '-p', '--profile_name', help='AWS profile to use',
    type=str, default=None
)
args = parser.parse_args()


dxtrack.configure(
    stage='dev',
    context=args.context,
    default_metadata={'default': 'metadata'},
    run_id=str(round(time.time())),
    profile_name=args.profile_name
)

for i in range(args.n_errors):
    try:
        raise ValueError('some kind of error {}'.format(i))
    except ValueError as _:
        dxtrack.error(metadata={'count': i})

for i in range(args.n_metric_messages):
    dxtrack.metric(args.metric_name, random.gauss(10, 5))
