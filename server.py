#!/usr/bin/env python
# Python middleman server for bystander effect
# Ludum Dare 40
# Copyright Benjamin Welsh and Saul Amster

import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import os.path
import json
from urlparse import parse_qs
import random

PORT=33002
class Player:
    def __init__(self,uid,name):
        self.uid=uid
        self.shade_up=False
        self.has_called=False
        self.name=name

    def get_json(self):
        return {"uid":self.uid,
        "shade_up":self.shade_up,
        "has_called":self.has_called,
        "name":self.name}

    def __str__(self):
        return json.dumps(self.get_json())
class Room:
    _uid=1
    def __init__(self,secret):
        self.players = {}
        self.secret = secret
        self.is_live=False

    def addPlayer(self, name):
        self.players[name]=Player(self._uid,name)
        self._uid+=1
        return self._uid-1

    def get_json(self):
        return{
            "players":[self.players[i].get_json() for i in self.players]
        }
    def __str__(self):
        d=self.get_json()
        d["secret"]=self.secret
        return json.dumps(d)

class Server(BaseHTTPRequestHandler):
    rooms={"asdf":Room("Did you ever hear the tragedy of Darth Plagueis The Wise?")}

    #def __init__(self):
    #    
    #    self.rooms["asdf"]=Room()

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

    def do_Error(self,i,s="no message"):
        self.send_response(i)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', 'http://saulamster.com')
        self.wfile.write("<html><body><h1>Error %d: </h1>%s</body></html>"%(i,s))
        
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
            print "===ERROR=== no type in data"
            self.do_Error(400)
            return
        type=data["type"][0]
        output_json={}
        # {'type': ['join'], 'name': ['Bob']}
        try:
            if type=="join":
                output_json=self.req_join(data)
            elif type=="update_request":
                output_json=self.req_update(data)
            elif type=="action":
                atype=data["action"][0]
                if atype=="shades":
                    self.action_blinds(data)
                elif atype=="call":
                    self.action_call(data)
                output_json=self.req_update(data)
            elif type=="new_room":
                output_json=self.req_newroom(data)
            elif type=="supdate_request":
                output_json=self.req_supdate(data)
            elif type=="saction":
                atype=data["action"][0]
                if atype=="makelive":
                    output_json=self.saction_setlive(True)
        except KeyError as e:
            print "===ERROR===",e
            self.do_Error(400,str(e))
            return
#        print self.posted
#        print self.data
        self._set_headers_json()
        print "SENDING:",json.dumps(output_json)
        self.wfile.write(json.dumps(output_json))

    def random_code(self):
        return chr(random.randint(97,122))+chr(random.randint(97,122))+chr(random.randint(97,122))+chr(random.randint(97,122))
    
    def req_newroom(self, data):
        secret=data["secret"][0]
        room_id=self.random_code()
        while room_id in self.rooms:
            room_id=self.random_code()
        self.rooms[room_id]=Room(secret)
        return {"room_id":room_id}

    def req_supdate(self, data):
        secret=data["secret"][0]
        room_id=data["room_id"][0]
        if room_id not in self.rooms:
            return {"success":False,"players":[],"message":"Room does not exist."}
        if secret != self.rooms[room_id].secret:
            return {"success":False,"players":[],"message":"Bad secret."}
        # if name not in self.rooms[room_id].players:
        #     return {"success":"false","message":"Name '%s' does not exist in room."%name}
        ret=self.rooms[room_id].get_json()
        ret["success"]=True
        ret["message"]="hi"
        return ret

    def req_join(self, data):
        name=data["name"][0]
        room_id=data["room_id"][0]

        if room_id not in self.rooms:
            return {"success":"false","message":"Room does not exist."}
        if name in self.rooms[room_id].players:
            return {"success":"false","message":"Name is already in use."}
        uid=self.rooms[room_id].addPlayer(name)
        return {"name":name, "success":"true", "uid":uid}

    def req_update(self, data):
        name=data["name"][0]
        room_id=data["room_id"][0]
        if room_id not in self.rooms:
            return {"success":"false","message":"Room does not exist."}
        if name not in self.rooms[room_id].players:
            return {"success":"false","message":"Name '%s' does not exist in room."%name}
        ret=self.rooms[room_id].players[name].get_json()
        ret["success"]=True
        ret["is_live"]=self.rooms[room_id].is_live
        return ret

    def action_blinds(self,data):
        name=data["name"][0]
        room_id=data["room_id"][0]
        if room_id not in self.rooms:
            return {"success":"false","message":"Room does not exist."}
        if not self.rooms[room_id].is_live:
            return {"success":"false","message":"Room is not live"}
        if name not in self.rooms[room_id].players:
            return {"success":"false","message":"Name '%s' does not exist in room."%name}
        self.rooms[room_id].players[name].shade_up = not self.rooms[room_id].players[name].shade_up

    def action_call(self,data):
        name=data["name"][0]
        room_id=data["room_id"][0]
        if room_id not in self.rooms:
            return {"success":"false","message":"Room does not exist."}
        if not self.rooms[room_id].is_live:
            return {"success":"false","message":"Room is not live"}
        if name not in self.rooms[room_id].players:
            return {"success":"false","message":"Name '%s' does not exist in room."%name}
        self.rooms[room_id].players[name].has_called = True
    
def dump(self):
    print "\n\n", "-"*80
    for rid in self.rooms.keys():
        print rid,"::",str(self.rooms[rid])
    print "-"*80
        

httpd = SocketServer.TCPServer(("", PORT), Server)

print "serving at port", PORT
try:
    httpd.serve_forever()
except KeyboardInterrupt as e:
#    for rid in httpd.rooms.keys():
#        print rid,"::",str(httpd.rooms[rid])
#    print "-"*80
#    Server().dump()
    print dump(Server)
    httpd.server_close()
