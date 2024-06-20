import functools
import logging
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
            start_time = perf_counter()
            value = func(*args, **kwargs)
            end_time = perf_counter()
            run_time = end_time - start_time
            printed_text = f"Execution of {func.__name__} took {run_time:.2f} seconds."
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
