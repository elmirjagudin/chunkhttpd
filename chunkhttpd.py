#!/usr/bin/env python

from os import path
from http import server
import argparse
import socketserver
import re


class ChunkHandler(server.SimpleHTTPRequestHandler):
    def _parse_range(self):
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
    def __init__(self, server_address, RequestHandlerClass, chunk_size):
        socketserver.ThreadingTCPServer.__init__(self,
                                                 server_address,
                                                 RequestHandlerClass)
        self.chunk_size = chunk_size


def parse_args():
    parser = argparse.ArgumentParser(description="Chunked up HTTP responses")
    parser.add_argument("-p", "--port", dest="port", type=int, default=8000,
                        help="The port to listen on.")

    parser.add_argument("-c", "--chunk", dest="chunk_size", type=int,
                        default=1024*1024*2,
                        help="The port to listen on.")

    return parser.parse_args()

args = parse_args()

httpd = ChunkServer(("", args.port), ChunkHandler, args.chunk_size)

try:
    print("serving at port {0}, chunk size: {1} bytes.".format(
        args.port, args.chunk_size))

    httpd.serve_forever()
except KeyboardInterrupt:
    httpd.shutdown()
