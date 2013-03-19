
====================================================
rose: a PEP-3156 compatible event loop based on pyuv
====================================================


Overview
========

`PEP-3156 <http://www.python.org/dev/peps/pep-3156/>`_ is a proposal for asynchronous I/O in Python,
starting with Python 3.3. The reference implementation is codenamed "tulip" and can be found
`here <https://code.google.com/p/tulip/>`_.

Rose is an event loop implementation for Tulip based on `pyuv <https://github.com/saghul/pyuv>`_.

Rose depends on pyuv >= 0.10.0, you can install it by doing:

::

    pip install -U pyuv


Running the test suite
======================

From the toplevel directory, run:

::

    hg clone https://code.google.com/p/tulip/
    export PYTHONPATH=tulip/
    python runtests.py -v

