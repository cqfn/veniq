import threading
import signal
import os
import time


class TerminateExecution(Exception):
    """
    Exception to indicate that execution has exceeded the preset running time.
    """


def quit_function(pid):
    # Killing all subprocesses
    os.setpgrp()
    os.killpg(0, signal.SIGTERM)

    # Killing the main thread
    os.kill(pid, signal.SIGTERM)


def handle_term(signum, frame):
    raise TerminateExecution()


def invoke_with_timeout(timeout, fn, *args, **kwargs):
    # Setting a sigterm handler and initiating a timer
    old_handler = signal.signal(signal.SIGTERM, handle_term)
    timer = threading.Timer(timeout, quit_function, args=[os.getpid()])
    terminate = False

    # Executing the function
    timer.start()
    try:
        result = fn(*args, **kwargs)
    except TerminateExecution:
        terminate = True
    finally:
        # Restoring original handler and cancel timer
        signal.signal(signal.SIGTERM, old_handler)
        timer.cancel()

    if terminate:
        raise BaseException("xxx")

    return result
