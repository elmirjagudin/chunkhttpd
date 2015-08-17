# Chunkhttpd

Simple HTTP daemon, that serves the content in chunks. Have simple
support for 'Range' header, to allow resuming downloads.

Allows to emulate issues with downloading large files over HTTP, where
connection is lost before the complete file is transmitted.

## Using

run with:

> python chunkhttpd.py

to get a list of supported command line arguments, run:

> python chunkhttpd.py -h

This is python 3 code, the `python` above must resolve to python 3 interperator, replace with `python3` as needed.

## Hacking

To perform static analysis of the code with `flake8` and `pylint` tools, run:

> make

This requires that `make`, `flake8` and `pylint` tools are available on your system.

