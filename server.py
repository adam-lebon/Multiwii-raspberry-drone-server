#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
import os
import logging
import threading
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.websocket
import json

from tornado.options import define, options


camera = False

class server:
	def __init__(self, port):
		
		#self.board = board
		self.port = port
		#global camera
		#camera = cam
		tornado.options.parse_command_line()
		self.app = MainHandler()

	def start(self, async):
		
		self.app.listen(self.port)
		if async:
			try:
				self.thread = threading.Thread(target=tornado.ioloop.IOLoop.current().start)
				self.thread.start()
				print "async"
				return False
			except Exception, errtxt:
				logging.error("The server failed to start", exc_info=True)
		else:
			try:
				tornado.ioloop.IOLoop.instance().start()				
			except Exception, errtxt:
				logging.error("The server failed to start", exc_info=True)

	def stop(self):
		tornado.ioloop.IOLoop.current().stop()

	def changeSpeed(self, channel, speed):
		self.throtle.changeSpeed(speed)
		


class MainHandler(tornado.web.Application):
	def __init__(self):
		logging.info("Server is started");
		handlers = [
			(r"/", MainHandler),
			(r"/chatsocket", SocketHandler),
		]
		settings = dict(
			cookie_secret="jskifhjndouihnsdfouij454sqdqs5gf7s2z9s",
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			xsrf_cookies=True,
		)
		tornado.web.Application.__init__(self, handlers, **settings)

class WebHandler(tornado.web.RequestHandler):
 	def get(self):
		self.write(open("www/index.html", "r").read())

class SocketHandler(tornado.websocket.WebSocketHandler):
	waiters = set()
	cache = []
	cache_size = 200
	continueReading = True
	checkCardRunning = False
	global camera

	print('test')
	print(camera)

	def __init__(self):
		print('tttest')
		print(server.camera)

	def check_origin(self, origin):
		return True

	def get_compression_options(self):
		# Non-None enables compression with default options.
		return {}
	
	def open(self):
		SocketHandler.waiters.add(self)
		print('connect')

	def on_close(self):
		SocketHandler.waiters.remove(self)

	def on_message(self, message):
		print('message')
		message = json.loads(message)
		if(message.action == "videoStart"):
			print('videoStart')
		print(message)
"""
import time
import commands
import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import threading
import json

from tornado.options import define, options

camera = False
board  = False
information = {
	'record': False,
	'main_controller': False,
	'usb': []
}

class server:
	def __init__(self, port, b, cam):
		define("port", default=80, help="run on the given port", type=int)
		self.port = 80
		global camera
		camera = cam
		global board
		board = b
		tornado.options.parse_command_line()
		self.app = Application()
		#self.board = board
		#self.port = port
		#global camera
		#camera = cam
		#tornado.options.parse_command_line()
		#self.app = Application()

	def start(self, async):
		self.started = True
		self.app.listen(self.port)
		if async:
			try:
				self.tornadoThread = threading.Thread(target=tornado.ioloop.IOLoop.current().start)
				self.tornadoThread.start()

				self.securityCheckThread = threading.Thread(target=self.securityCheck())
				self.securityCheckThread.start()
				print "async"
				return False
			except Exception, errtxt:
				logging.error("The server failed to start", exc_info=True)
		else:
			try:
				tornado.ioloop.IOLoop.instance().start()				
			except Exception, errtxt:
				logging.error("The server failed to start", exc_info=True)

	def stop(self):
		self.started = False
		tornado.ioloop.IOLoop.current().stop()

	def securityCheck(self):
		while self.started:
			if(len(ChatSocketHandler.waiters) == 0):
				board.rcData = [1500, 1500, 1500, 1000]

			mount = commands.getoutput('mount -v')
			lines = mount.split('\n')
			points = map(lambda line: line.split()[2], lines)
			information["usb"] = []
			for point in points:
				if point[:10] == "/media/usb":
					if point in information["usb"]:
						pass
					else:
						information["usb"].append(point)

			print information
			time.sleep(1)


class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", MainHandler),
			(r"/chatsocket", ChatSocketHandler),
		]
		settings = dict(
			cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			xsrf_cookies=True,
		)
		tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html", messages=ChatSocketHandler.cache)

class ChatSocketHandler(tornado.websocket.WebSocketHandler):
	waiters = dict()
	id_counter = 1

	def get_compression_options(self):
		# Non-None enables compression with default options.
		return {}

	def check_origin(self, origin):
		return True

	def open(self, *args):
		self.id = ChatSocketHandler.id_counter
		ChatSocketHandler.id_counter = ChatSocketHandler.id_counter + 1
		ChatSocketHandler.waiters[self.id] = { "id": self.id, "obj": self}
		#self.write_message('{ "action": "set_id", "data": "'+ str(self.id) +'"}')

	def on_close(self):
		global information
		ChatSocketHandler.waiters.pop(self.id, None)
		information["main_controller"] = False
		self.send_updates()

	@classmethod
	def update_cache(cls, chat):
		cls.cache.append(chat)
		if len(cls.cache) > cls.cache_size:
			cls.cache = cls.cache[-cls.cache_size:]

	def send_updates(cls):
		print "send update"
		global information
		print information
		for key in cls.waiters:
			try:
				information_temp = information
				information_temp["id"] = cls.waiters[key]["id"]
				cls.waiters[key]["obj"].write_message('{ "action": "get_info", "data": ' + json.dumps(information_temp) + ' }')
			except:
				logging.error("Error sending message", exc_info=True)

	def on_message(self, message):
		global information
		message = json.loads(message)
		if message["action"] == "rcData":

			if information["main_controller"] == self.id:
				global board
				board.rcData = [
					((message["data"]["right"]["deltaY"]/100)*500+1500),
					((message["data"]["right"]["deltaX"]/100)*500+1500),
					((message["data"]["left"]["deltaX"]/100)*500+1500),
					(message["data"]["left"]["deltaY"]/100)*500+1500,
				]
				print(board.rcData)
		
		if message["action"] == "record":
			print "record"
			global camera
			if information["record"] == False:
				if len(information["usb"]) == 1:
					if os.path.isdir(information["usb"][0]+'/Video drone') == False:
						os.mkdir(information["usb"][0]+'/Video drone')
					camera.start_recording(information["usb"][0]+"/Video drone/"+time.strftime("%y-%m-%d %H.%M")+".h264")
					information["record"] = True
			else:
				camera.stop_recording()
				information["record"] = False

			self.send_updates()

		if message["action"] == "get_info":
			print "get_info"
			self.send_updates()

		if message["action"] == "mainControllerRequest":
			print "mainControllerRequest"
			if information["main_controller"] == False:
				information["main_controller"] = self.id
			self.send_updates()

		if message["action"] == "mainControllerRelease":
			if self.id == information["main_controller"]:
				information["main_controller"] = False
				self.send_updates()


def main():
	tornado.options.parse_command_line()
	app = Application()
	app.listen(options.port)
	tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
	main()