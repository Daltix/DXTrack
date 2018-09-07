import time
import argparse
import random
from dxtrack import dxtrack

dxtrack.configure(
    stage='dev',
    context='test',
    default_metadata={'default': 'metadata'},
    run_id=str(round(time.time()))
)

parser = argparse.ArgumentParser()
parser.add_argument(
    '-ne', '--n_errors', help='Number of errs to send', type=int, default=100
)
parser.add_argument(
    '-nm', '--n_metric_messages', help='Number of metric entries to send',
    type=int, default=100
)
args = parser.parse_args()

for i in range(args.n_errors):
    try:
        raise ValueError('some kind of error')
    except ValueError as _:
        dxtrack.error(metadata={'count': i})

for i in range(args.n_metric_messages):
    dxtrack.metric('metric_name_{}'.format(i % 10), random.gauss(10, 5))
