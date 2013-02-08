"""Run all unittests.

Usage:
  python3 runtests.py [-v] [-q] [pattern] ...

Where:
  -v: verbose
  -q: quiet
  pattern: optional regex patterns to match test ids (default all tests)

Note that the test id is the fully qualified name of the test,
including package, module, class and method,
e.g. 'tulip.events_test.PolicyTests.testPolicy'.
"""

# Originally written by Beech Horn (for NDB).

import logging
import os
import re
import sys
import unittest

assert sys.version >= '3.3', 'Please use Python 3.3 or higher.'


TULIP_DIR = __import__('tulip').__path__[0]
ROSE_DIR = os.path.join(os.path.dirname(__file__), 'rose')


def load_test_modules(loader, suite, includes, excludes, base_module, test_modules):
    for mod in [getattr(base_module, name) for name in test_modules]:
        for name in set(dir(mod)):
            if name.endswith('Tests'):
                test_module = getattr(mod, name)
                tests = loader.loadTestsFromTestCase(test_module)
                if includes:
                    tests = [test
                            for test in tests
                            if any(re.search(pat, test.id()) for pat in includes)]
                if excludes:
                    tests = [test
                            for test in tests
                            if not any(re.search(pat, test.id()) for pat in excludes)]
                suite.addTests(tests)


def load_tests(includes=(), excludes=()):
    tulip_test_mods = [f[:-3] for f in os.listdir(TULIP_DIR) if f.endswith('_test.py')]
    rose_test_mods = [f[:-3] for f in os.listdir(ROSE_DIR) if f.endswith('_test.py')]

    if sys.platform == 'win32':
        try:
            tulip_test_mods.remove('subprocess_test')
        except ValueError:
            pass
    tulip = __import__('tulip', fromlist=tulip_test_mods)
    rose = __import__('rose', fromlist=rose_test_mods)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    load_test_modules(loader, suite, includes, excludes, tulip, tulip_test_mods)
    load_test_modules(loader, suite, includes, excludes, rose, rose_test_mods)

    return suite


def main():
  excludes = []
  includes = []
  patterns = includes  # A reference.
  v = 1
  for arg in sys.argv[1:]:
    if arg.startswith('-v'):
      v += arg.count('v')
    elif arg == '-q':
      v = 0
    elif arg == '-x':
        if patterns is includes:
            patterns = excludes
        else:
            patterns = includes
    elif arg and not arg.startswith('-'):
      patterns.append(arg)
  tests = load_tests(includes, excludes)
  logger = logging.getLogger()
  if v == 0:
    logger.setLevel(logging.CRITICAL)
  elif v == 1:
    logger.setLevel(logging.ERROR)
  elif v == 2:
    logger.setLevel(logging.WARNING)
  elif v == 3:
    logger.setLevel(logging.INFO)
  elif v >= 4:
    logger.setLevel(logging.DEBUG)

  result = unittest.TextTestRunner(verbosity=v).run(tests)
  sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
  main()
