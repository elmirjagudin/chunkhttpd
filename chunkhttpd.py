#!/usr/bin/env python

"""
Simple HTTP daemon, that serves the content in chunks. Have simple
support for 'Range' header, to allow resuming downloads.

Allows to emulate issues with downloading large files over HTTP, where
connection is lost before the complete file is transmitted.
"""


from os import path
from http import server
import argparse
import socketserver
import re


class ChunkHandler(server.SimpleHTTPRequestHandler):
    """
    Extends the SimpleHTTPRequestHandler to only serve
    at most the specified chunk size.

    Also handle 'Range' header, to allow resuming uploads.
    """
    def _parse_range(self):
        """
        Parse 'Range' request header.

        :return: (False, 0) if no 'Range' header is specified
                 (True, start) if 'Range' header is specified,
                               start is the first byte of the content requested
        """
        no_header = (False, 0)
        range_header = self.headers.get("Range")
        if range_header is None:
            return no_header

        match = re.match(r"bytes=(\d*)-", range_header)
        if match is None:
            return no_header

        return True, int(match.group(1))

    def do_GET(self):
        file_path = self.translate_path(self.path)
        if not path.isfile(file_path):
            # let the super class to deal with directory listing,
            # file not found errors, etc
            return server.SimpleHTTPRequestHandler.do_GET(self)

        range_specified, range_start = self._parse_range()
        file_size = path.getsize(file_path)

        if range_specified:
            self.send_response(206)
            self.send_header(
                "Content-Range",
                "bytes {start}-{end}/{size}".format(start=range_start,
                                                    end=file_size-1,
                                                    size=file_size))
        else:
            self.send_response(200)

        requested_file = open(file_path, mode="rb")
        requested_file.seek(range_start)

        self.send_header("Content-type", "text/plain")
        self.send_header("Content-Length", file_size)
        self.end_headers()

        self.wfile.write(requested_file.read(self.server.chunk_size))


class ChunkServer(socketserver.ThreadingTCPServer):
    """
    Override ThreadingTCPServer so that we can pass on the chunk size
    setting to our request handler.
    """
    def __init__(self, server_address, RequestHandlerClass, chunk_size):
        socketserver.ThreadingTCPServer.__init__(self,
                                                 server_address,
                                                 RequestHandlerClass)
        self.chunk_size = chunk_size


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Chunked up HTTP responses")
    parser.add_argument("-p", "--port", dest="port", type=int, default=8000,
                        help="The port to listen on.")

    parser.add_argument("-c", "--chunk", dest="chunk_size", type=int,
                        default=1024*1024*2,
                        help="The port to listen on.")

    return parser.parse_args()


def main():
    """
    parse argument, handle requested we get interrupt signal
    """
    args = parse_args()
    httpd = ChunkServer(("", args.port), ChunkHandler, args.chunk_size)

    try:
        print("serving at port {0}, chunk size: {1} bytes.".format(
            args.port, args.chunk_size))

        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()

main()
