
====================
Implementation notes
====================

This is a non exhaustive list of things about how things were
implemented like they were in uv.py

Wakeup
======

While a socketpair + a Poll handle could have been used, pyuv
comes with a dedicated handle for this task, Async.

Ordering
========

Tulip enforces certain order of execution by design, which doesn't
really match the order in which pyuv would execute the given callbacks.
The solution is to use a single Check handle (which gets executed every
loop iteration, after polling for io) which processes the ready callbacks
queue. Other handles just append to this queue, and there is a single
place where the queue is processed: the check handle. Thus order is preserved.

Stop
====

Loop stop is always executed at the begining of the next event loop
iteration. Calling stop will also prevent the loop from blocking for io
on that iteration.

Close
=====

After calling close the loop is destroyed and all resources are freed so
the loop cannot be used anymore.

Signals
=======

Signals are not handled using Python's `signal` module but using pyuv's
Signal handles. These handles allow signals to be processed on any thread
and on multiple event loops at the same time (all callbacks will be called).
Callbacks are always called on the event loop thread.

Currently Signal handles are ref'd, this means that if an event loop has a single
signal handler and loop.run() is called, it will not return unless the signal handler
is removed or loop.stop() is explicitly called. This may change in the future.

KeyboardInterrupt
=================

If the loop is blocked polling, pressing Ctrl+C won't interrupt it and raise
KeyboardInterrupt. This is due to how libuv handles signals. More info and a
possible solution here: https://github.com/saghul/pyuv/commit/3b43285bc66883c4466cb4413de80842dce98621
and here: https://github.com/saghul/pyuv/commit/6e71bf7da350c6ced6bdc4375ed6ba8cd2a9d2f2

