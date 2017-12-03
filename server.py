#!/usr/bin/env python
# Python middleman server for bystander effect
# Ludum Dare 40
# Copyright Benjamin Welsh and Saul Amster

import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import os.path
from urlparse import parse_qs

PORT=33002
class Player:
    def __init__(self,uid,name):
        self.uid=uid
        self.shade_up=False
        self.has_called=False
        self.name=name

class Game:
    def __init__(self):
        self.players = {}
        

class Server(BaseHTTPRequestHandler):
    games={}
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', 'http://saulamster.com')
        self.end_headers()

    def _set_headers_json(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', 'http://saulamster.com')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        localpath="serve"+self.path
        if localpath == "serve/":
            localpath="serve/root.html"
        print localpath
        if os.path.isfile(localpath):
            print "file exists"
            with open(localpath) as f:
                self.wfile.write(f.read())
        else:
            self.wfile.write("<html><body><h1>404</h1></body></html>")

    def do_Error(self,i):
        self.send_response(i)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', 'http://saulamster.com')
        self.wfile.write("<html><body><h1>Error %d</h1></body></html>"%i)
        
    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        length=0
        try:        
            length=int(self.headers['content-length'])
        except ValueError:
            print "NEEDED LENGTH"
            self.do_Error(411)
            #do 4--
        post_data=self.rfile.read(length)
        print "DATA:",post_data
        data=parse_qs(post_data)
        print "Parsed:",data
        if "type" not in data:
            self.do_Error(400)
            return
#        print self.posted
#        print self.data
        self._set_headers_json()
        self.wfile.write('{"name":"bob"}')


httpd = SocketServer.TCPServer(("", PORT), Server)

print "serving at port", PORT
try:
    httpd.serve_forever()
except KeyboardInterrupt as e:
    httpd.server_close()
