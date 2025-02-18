import functools
import logging
import sys
import tracemalloc
from time import perf_counter
from typing import Any, Callable


def benchmark(logger: logging.Logger | None = None) -> Callable[..., Any]:
    """
    Benchmark the wrapped function by printing its execution time
    :param logger: The logger class to log the benchmark value
    :return: The benchmark decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracemalloc.start()
            start_time = perf_counter()
            value = func(*args, **kwargs)
            end_time = perf_counter()
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            run_time = end_time - start_time

            if sys.platform == "linux" or sys.platform == "linux2":
                import resource

                mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            else:
                mem_usage = None

            printed_text = f"Execution of {func.__name__} took {run_time:.3f} seconds.\n"
            printed_text += (
                f"Current Memory Usage: {current_mem / 1024 :.3f} KB or {current_mem / 1024 / 1024 :.3f} MB.\n"
            )
            printed_text += f"Peak Memory Usage: {peak_mem / 1024 / 1024:.3f} MB"

            if mem_usage is not None:
                print(f"\nMax RSS Memory Usage: {mem_usage:.2f} MB")

            print(printed_text)

            if logger:
                logger.info(printed_text)

            return value

        return wrapper

    return decorator


def log_this(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Perform logging for the wrapped function
    :param func: The wrapped function to benchmark
    :return: The logging wrapper function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logging.info(f"Calling {func.__name__}")
        value = func(*args, **kwargs)
        logging.info(f"Finished {func.__name__}")
        return value

    return wrapper
