"""Common init function for tests."""
import sys
import json
import logging

from util import init_logging

import graph
import stepmanager


def fail_with(*arg):
    """Print an error message and exit."""
    print("ERROR:", *arg, file=sys.stderr)
    sys.exit(1)


def fail_if(condition, *arg, dry=False):
    """Exit with error message, if condition is met.

    Keyword argument:
    dry -- Don't check and fail, only print message
    """
    if condition or dry:
        print("ERROR:", *arg, file=sys.stderr)
        if condition and not dry:
            sys.exit(1)


def init_test(steps=None, extra_config=None):
    """Common interface for test. Reads a JSON file and some ll-file from the
    command line and make them available.

    CLI usage when using init_test:
    your_program <os_name> <json_file> <ll_files>

    Return a graph reference, the JSON struct and the stepmanager instance.

    Arguments:
    steps:        List of steps, see the `esteps` argument of
                  Stepmanager.execute.
    extra_config: Dict with extra configuration, see the `extra_config`
                  argument of Stepmanager.execute.
    """
    init_logging(level=logging.DEBUG)
    if not extra_config:
        extra_config = {}
    g = graph.Graph()
    assert len(sys.argv) == 3
    json_file = sys.argv[1]
    i_file = sys.argv[2]
    print(f"Testing with JSON: '{json_file}'"
          f", and file: {i_file}")
    if steps:
        print(f"Executing steps: {steps}")
    elif extra_config:
        print(f"Executing with config: {extra_config}")
    else:
        assert False
    with open(json_file) as f:
        data = json.load(f)

    s_manager = stepmanager.StepManager(g)

    config = {'log_level': 'debug',
              'dump_prefix': '/dev/null',
              'dump': False,
              'input_file': i_file}
    s_manager.execute(config, extra_config, steps)

    return g, data, s_manager
