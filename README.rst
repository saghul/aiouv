
========================================
rose: a PEP-3156 experimental event loop
========================================


Overview
========

`PEP-3156 <http://www.python.org/dev/peps/pep-3156/>_` is a proposal for asynchronous I/O in Python,
starting with Python 3.3. The reference implementation is codenamed "tulip" and can be found
`here <https://code.google.com/p/tulip/>`_.

Rose is just a fork of tulip which replaces the use of select, epoll and kqueue selectors
with `pyuv <https://github.com/saghul/pyuv>`_.

The intention of this project is to experiment with pyuv as a specific event loop implementation.
Once tulip makes it to the standard library all duplicated code will be removed from this project
just leaving the event loop itself.

.. note::
    I try to keep up with the tulip develpment, but sometimes it may take me a while to port
    changes over to rose. Please bear with me :-)

.. note::
    Rose currently depends on pyuv master branch, you can install it by doing:

    pip install git+https://github.com/saghul/pyuv.git


Running the test suite
======================

From the toplevel directory, run:

::

    nosetests -v -w tests/

