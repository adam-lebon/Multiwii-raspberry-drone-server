#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import logging
import os.path
import uuid
import signal
import sys
import threading
import json
import encodings
import time
import serial
import RPi.GPIO as GPIO
import picamera

import multiwii
import server


class Main():
	def start(self, board, camera):
		self.hello = "hello"
		test = "test"
		self.board = board
		self.camera = camera
		self.webServer = server.server(80, self.board, self.camera)
		self.webServer.start(True)

	def stop(self):
		self.webServer.stop()
		self.board.stop()

	
if __name__ == "__main__":
	global board
	board = multiwii.drone('/dev/ttyUSB0')
	camera = picamera.PiCamera()
	camera.vflip = True
	camera.hflip = True
	
	start = Main()
	MainThread = threading.Thread(target=start.start, args=(board, camera))
	MainThread.start()
	"""MainThread.join()"""
	
	def signal_handler(signal, frame):
		print('You pressed Ctrl+C!')
		GPIO.cleanup()
		start.stop()
		sys.exit(0)
	
	signal.signal(signal.SIGINT, signal_handler)
	signal.pause()
