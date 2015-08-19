# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

DIR_PLAYLIST = "./music"
DIR_COLORS = "./colors"
DIR_COLORS_RANDOM = "./colors/random"

ON_PI = False
LED_COMMON_ANODE = True
RGB_PINS = [4, 17, 22]	# USES BCM NUMBERING
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
import sys
sys.path.insert(0, './lib')

import time, os, glob, thread, signal, logging, math
from mutagen.mp3 import MP3
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from random import random
import vlc

if (ON_PI):
	blaster_file = open("/dev/pi-blaster", "a")

# -----------------------------------------------------------------------------

def percentage_in_range(a, b, c):
	return ((a-b)/float(c-b))

# -----------------------------------------------------------------------------
# MUSIC
# -----------------------------------------------------------------------------

class Music:
	file = ""
	player = vlc.MediaPlayer()
	volume = 1
	mute = False

	def load(self, file):
		self.stop()
		self.file = file

	def play(self):
		if (self.player.get_state() == vlc.State.NothingSpecial) or (self.player.get_state() == vlc.State.Stopped) or (self.player.get_state() == vlc.State.Ended):
			self.player.set_mrl(self.file)
		self.player.play()

	def set_volume(self, volume):
		self.volume = volume
		self.mute = False
		self.player.audio_set_volume(int(round(self.volume * 100)))

	def get_volume(self): return (self.player.audio_get_volume() / 100.0)

	def mute_toggle(self):
		self.player.audio_set_volume(int(round(self.volume * 100)) * int(self.mute))
		self.mute = not self.mute

	def stop(self):
		self.player.stop()

	def seek(self, time):
		self.play()
		self.set_time(time)

	def play_pause(self):
		if (self.player.get_state() == vlc.State.Playing):
			self.player.pause()
		else:
			self.play()

	def get_time(self): return max(self.player.get_time() / 1000.0, 0)
	def set_time(self, time): self.player.set_time(int(round(time * 1000)))
	def get_playing(self): return (self.player.get_state() == vlc.State.Playing)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# PLAYLIST
# -----------------------------------------------------------------------------

class Playlist:
	index = 0
	mode = 3 # 0 = Play all once, 1 = Repeat All, 2 = Repeat One, 3 = Shuffle

	def __init__(self):
		self.scan()
		self.set_index(self.index)

		thread.start_new_thread(Playlist.thread_main, (self,))

	def scan(self):
		self.array_files = []
		self.array_length = []
		self.array_titles = []
		
		for file in glob.glob(os.path.join(DIR_PLAYLIST, "*.mp3")):
			self.array_files.append(file)
			self.array_length.append(MP3(file).info.length)
			self.array_titles.append(os.path.splitext(os.path.basename(file))[0])
		print str(len(self.array_files)) + " music track(s) found."
		
		self.array_cycles_name = []
		self.array_cycles = [] # Randoms, then specifics
		self.num_colors_random = 0
		
		for file in glob.glob(os.path.join(DIR_COLORS_RANDOM, "*.txt")):
			self.num_colors_random += 1
			file_load = open(file, "r")
			self.array_cycles.append(file_load.read())
			self.array_cycles_name.append("")
		print str(self.num_colors_random) + " random color cycle(s) found."
			
		for file in glob.glob(os.path.join(DIR_COLORS, "*.txt")):
			file_load = open(file, "r")
			self.array_cycles.append(file_load.read())
			self.array_cycles_name.append(os.path.splitext(os.path.basename(file))[0])
			
		print str(len(self.array_cycles) - self.num_colors_random) + " color cycle(s) found."
		
		self.array_cycles_index = [None for x in range(len(self.array_titles))]
		
		for i in range(len(self.array_titles)):
			for i_2 in range(len(self.array_cycles_name)):
				if (self.array_cycles_name[i_2] == self.array_titles[i]):
					self.array_cycles_index[i] = i_2
			if (self.array_cycles_index[i] == None):
				self.array_cycles_index[i] = int(round(random() * (self.num_colors_random - 1)))
	
	def set_index(self, index):
		self.index = index
		obj_Music.load(self.array_files[self.index])
		obj_Led.change_cycle(
			self.array_cycles[self.array_cycles_index[self.index]],
			self.array_length[self.index]
		)
				
	def play_index(self, index):
		self.set_index(index)
		obj_Music.play()

	def next(self):
		index = self.index + 1
		if (index >= len(self.array_files)):
			index = 0
		self.play_index(index)

	def prev(self):
		index = self.index - 1
		if (index < 0):
			index = len(self.array_files) - 1
		self.play_index(index)

	def repeat(self):
		obj_Music.play()

	def button_next(self):
		if ((self.mode == 0) or (self.mode == 2)):
			self.next()
		else:
			self.advance()

	def change_mode(self):
		self.mode += 1
		if (self.mode >= 4):
			self.mode = 0

	def advance(self):
		if (self.mode == 0):
			if (self.index >= len(self.array_files) - 1):
				self.set_index(0)
			else:
				self.next()
		elif (self.mode == 1):
			self.next()
		elif (self.mode == 2):
			self.repeat()
		elif (self.mode == 3):
			self.play_index(int(math.floor(random()* len(self.array_files))))

	def thread_main(self):
		global running
		while running:
			if (obj_Music.player.get_state() == vlc.State.Ended):
				self.advance()					
			time.sleep(1.0/20.0)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# WEBSOCKET
# -----------------------------------------------------------------------------
class Server_GUI:
	class WebSocket_GUI(WebSocket):
		def handleMessage(self):
			mode = self.data[:1]
			message = self.data[1:]			
			if (mode == '0'):			# PLAY
				obj_Music.play_pause()
			elif (mode == '1'):			# STOP
				obj_Music.stop()
			elif (mode == '2'):			# PREVIOUS
				obj_Playlist.prev()
			elif (mode == '3'):			# NEXT
				obj_Playlist.button_next()
			elif (mode == '4'):			# VOLUME
				obj_Music.set_volume(float(message))
			elif (mode == '5'):			# PLAY INDEX
				obj_Playlist.play_index(int(message))
			elif (mode == '6'):			# SEEK
				obj_Music.seek(float(message))
			elif (mode == '7'):			# MUTE
				obj_Music.mute_toggle()	
			elif (mode == '8'):			# PLAYLIST CYCLE MODE
				obj_Playlist.change_mode()

		def handleConnected(self):
			print self.address, 'connected'
			Server_GUI.update_all(self);

		def handleClose(self): print self.address, 'closed'

	def __init__(self):
		self.server = SimpleWebSocketServer('0.0.0.0', 8000, self.WebSocket_GUI)

		signal.signal(signal.SIGINT, self.close_sig_handler)
		logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

		thread.start_new_thread(self.thread_main,())
		thread.start_new_thread(self.thread_change,())

		print "Server open!"

	@staticmethod
	def string_playing(): return '"playing":' + str(obj_Music.get_playing()).lower() + ','

	@staticmethod
	def string_index(): return '"index":' + str(obj_Playlist.index).lower() + ','

	@staticmethod
	def string_files():
		string = '"files":['
		for title in obj_Playlist.array_titles:
			string += '"' + title + '",'
		return string[:-1] + '],'

	@staticmethod
	def string_length():
		string = '"lengths":['
		for length in obj_Playlist.array_length:
			string += str(length) + ','
		return string[:-1] + '],'
	
	@staticmethod
	def string_position(): return '"time":' + str(obj_Music.get_time()) + ','

	@staticmethod
	def string_volume(): return '"volume":' + str(obj_Music.get_volume()) + ','

	@staticmethod
	def string_mute(): return '"mute":' + str(obj_Music.mute).lower() + ','

	@staticmethod
	def string_mode(): return '"mode":' + str(obj_Playlist.mode) + ','
	
	@staticmethod
	def string_cycles():
		string = '"cycles":["'
		for x in obj_Playlist.array_cycles:
			string += x + '","'
		return (string[:-2] + '],').replace("\r", "\n").replace("\n\n", "\n").replace("\n", "\\n")
		
	@staticmethod
	def string_cycles_index():
		string = '"cycles_index":['
		for x in obj_Playlist.array_cycles_index:
			string += str(x) + ','
		return string[:-1] + '],'

	def send_to_all(self, string):
		for conn in self.server.connections.itervalues():
			conn.sendMessage(string)

	def thread_main(self):
		self.server.serveforever()

	@staticmethod
	def update_all(client):
		client.sendMessage("0{" + Server_GUI.string_cycles_index() + Server_GUI.string_cycles() + Server_GUI.string_mode() + Server_GUI.string_mute() + Server_GUI.string_volume() + Server_GUI.string_position() + Server_GUI.string_length() + Server_GUI.string_index() + Server_GUI.string_files() + Server_GUI.string_playing()[:-1] + "}")

	def thread_change(self):
		global running
		array_prev = [None for x in range(6)]
		array_current = [
			obj_Music.get_playing,
			(lambda: obj_Playlist.index),
			obj_Music.get_time,
			obj_Music.get_volume,
			(lambda: obj_Music.mute),
			(lambda: obj_Playlist.mode)
		]
		array_id = [
			'2',
			'3',
			'5',
			'6',
			'7',
			'8'
		]
		array_function = [
			self.string_playing,
			self.string_index,
			self.string_position,
			self.string_volume,
			self.string_mute,
			self.string_mode
		]
		while running:
			for i in range(len(array_current)):
				if (array_prev[i] != array_current[i]()):
					self.send_to_all(array_id[i] + "{" + array_function[i]()[:-1] + "}")
					array_prev[i] = array_current[i]()
			time.sleep(1.0/15.0)

	def close_sig_handler(self, signal, frame):
		self.server.close()
# -----------------------------------------------------------------------------

class Color_Cycle:

	class Color:
		def __init__(self, array, time):
			self.array = array
			self.time = time
	
	color_current = [0.0 , 0.0, 0.0]
	
	fade_out = 2
	fade_out_offset = 1

	time = 0.0
	queue = []
	time_total = None
	
	def __init__(self, refresh_rate = 1.0/60.0):
		self.refresh_rate = refresh_rate
		thread.start_new_thread(Color_Cycle.thread_main, (self,))
		
	def change_cycle(self, string, time_total):
		self.queue = []
		array_file = string.splitlines()
		for line in array_file:
			array_line = line.split(",")
			self.queue.append(Color_Cycle.Color(
				map(int, array_line[0:3]),
				float(array_line[3])
			))
		self.time_total = time_total
		
			
	def thread_main(self):
		while running:
			try:
				if (len(self.queue) != 0) and (self.time_total != None):
					self.time = obj_Music.get_time()
				
					i = 0
					time_reach = 0
					while (self.time >= time_reach):
						i %= len(self.queue)
						time_reach += self.queue[i].time
						i += 1
					i -= 1
					
					percentage = percentage_in_range(
						self.time,
						time_reach - self.queue[i].time,
						time_reach			
					)
					
					self.color_current = []
					for c in range(3):
						if (i <= 0):
							if (self.time >= self.queue[0].time):
								color_init = self.queue[len(self.queue) - 1].array[c]
							else:
								color_init = 0
						else:
							color_init = self.queue[i - 1].array[c]
						color_dest = self.queue[i].array[c]
						
						color_result = (percentage * (color_dest - color_init)) + color_init
						
						fade_end = self.time_total - self.fade_out_offset
						fade_start = fade_end - self.fade_out
						if (self.time >= fade_start):
							color_result *= 1 - min(max(percentage_in_range(
								self.time,
								fade_start,
								fade_end
							),0),1)
						self.color_current.append(color_result)
				else:
					self.color_current = [0.0, 0.0, 0.0]
				time.sleep(self.refresh_rate)
			except Exception:
				pass

class Led:
	refresh_rate = 1.0/60.0
	color_init = [0,0,0]
	pins = RGB_PINS
	
	def __init__(self):
		self.cycle = Color_Cycle()
		self.color_dest = self.cycle.color_current
		
		thread.start_new_thread(Led.thread_main, (self,))
		
	def change_cycle(self, string, time_total):
		self.cycle.change_cycle(
			string,
			time_total
		)
		
	def set_color(self, array):
		array_result = []
		for c in array:
			c = (c / 255.0)
			if (LED_COMMON_ANODE):
				c = 1 - c
			array_result.append(c)
		
		for i in range(len(array)):
			blaster_file.write(str(self.pins[i]) +  "=" + str(array_result[i]) + "\n")
		
	def thread_main(self):
		while running:
			self.set_color(self.cycle.color_current)				
			time.sleep(self.refresh_rate)
			
class Led_Null:
	def change_cycle(self, string, time_total):
		pass

	def set_color(self, array):
		pass

# -----------------------------------------------------------------------------
# EXECUTE
# -----------------------------------------------------------------------------

running = True
obj_Music = Music()
if (ON_PI):
	obj_Led = Led()
else:
	obj_Led = Led_Null()
obj_Playlist = Playlist()
obj_Server_GUI = Server_GUI()

while running:
	time.sleep(10)
# -----------------------------------------------------------------------------
