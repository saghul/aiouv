
====================
Implementation notes
====================

This is a non exhaustive list of things about how things were
implemented like they are in uv_events.py

Wakeup
======

While a socketpair + a Poll handle could have been used, pyuv
comes with a dedicated handle for this task, Async.

Ordering
========

Tulip enforces certain order of execution by design, which doesn't
really match the order in which pyuv would execute the given callbacks.
The solution is to use a single Idle handle (which gets executed every
loop iteration, when there are pending callbacks) which processes the
ready callbacks queue. Other handles just append to this queue, and there
is a single place where the queue is processed: the idle handle. Thus order
is preserved.

Stop
====

Loop stop is always executed at the begining of the next event loop
iteration. Calling stop will also prevent the loop from blocking for io
on that iteration. If any callback raises an exception, the loop is stopped.

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

NOTE: Tulip doesn't allow multiple signal handlers per signal. Rose could easily
implement it because pyuv supports it, though.

KeyboardInterrupt
=================

If the loop is blocked polling, pressing Ctrl+C won't interrupt it and raise
KeyboardInterrupt. This is due to how libuv handles signals. More info and a
possible solution here: https://github.com/saghul/pyuv/commit/3b43285bc66883c4466cb4413de80842dce98621
and here: https://github.com/saghul/pyuv/commit/6e71bf7da350c6ced6bdc4375ed6ba8cd2a9d2f2

Callback execution
==================

Currently rose runs all callbacks in an Idle handle, which runs before i/o has been performed and
prevents the loop from blocking for i/o in case it's still active.
All operations will queue the handles in the _ready queue and the aforementioned Idle handle will
execute them in order.

If any of the handlers raises BaseException sys.exc_info()
will be saved in _last_exc and the processing will not continue, then, if _last_exc is not None it
will be raised. Also, loop will be stopped.

