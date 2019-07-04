import unittest
from dxtrack import DXTrack
import time


def one_second_function(*args):
    time.sleep(1)


MAXIMUM_ASYNC_EXECUTION_TIME = 0.05


class TestAsyncBehaviour(unittest.TestCase):
    """

    A test class that runs DXTrack in both synchronous and asynchronous mode.
    We override the function that would be used to send metrics with a
    function that takes 1 second to execute. (Although this should probably
    be a mocked version of the object).

    To verify that the functionality is working as expected we send a metric
    via DXTrack that executes our sleep function. If everything is as
    expected, when running in async mode there should be almost no delay to
    get to the next line in the text.

    """
    def test_async_is_non_blocking(self):
        dx = DXTrack()
        dx.configure(
            context="test_context_001",
            stage="dev",
            run_id="test_non_async_call_takes_no_time_to_return",
            default_metadata={},
            use_async_requests=True
        )
        #
        #   Override our default write out function with our one that sleeps
        #   synchronously.
        dx._write_out = one_second_function
        #
        #   Take a look at the time now, run our function, and check how
        #   long it took.
        then = time.time()
        dx.metric("a", 0)
        now = time.time()
        #
        #   Check that the difference in time is no longer than our allotted
        #   maximum execution time for async functions.
        assert now - then < MAXIMUM_ASYNC_EXECUTION_TIME

    def test_sync_is_blocking(self):
        dx = DXTrack()
        dx.configure(
            context="test_context_001",
            stage="dev",
            run_id="test_sync_call_takes_a_while_to_return",
            default_metadata={},
            use_async_requests=False
        )
        #
        #   Override our default write out function with our one that sleeps
        #   synchronously.
        dx._write_out = one_second_function
        #
        #   Take a look at the time now, run our function, and check how long
        #   it took.
        then = time.time()
        dx.metric("a", 0)
        now = time.time()
        #
        #   Check that the difference in time is longer than our allotted
        #   maximum execution time for async functions.
        assert now - then > MAXIMUM_ASYNC_EXECUTION_TIME
