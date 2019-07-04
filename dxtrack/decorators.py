import asyncio


def fire_and_forget(f):
    """

    A function that can be used as a decorator to execute the function asynchronously.
    https://stackoverflow.com/questions/37278647/fire-and-forget-python-async-await/37345564

    :param f: The function f run as async.

        :return: Whatever was returned from the function that was run.

    """
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped
