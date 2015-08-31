import os
import hashlib


class Mapper:
	def __init__(self):
		pass

	def onMapPre(self):
		pass

	def onMapPost(self):
		pass

	def onCleanup(self):
		pass

	def getComandLinePre(self):
		return ""

	def getComandLineMain(self):
		return ""

	def getComandLinePost(self):
		return ""

	def getName(self):
		return "Unknown"

	def getTitle(self):
		return self.title

# Generic Mapper Wrapper
# Enables the creation of YAML-based wrappers for mappers, through a generic
# interface which allows using templates in YAML for setting the structure of the mappers command line calls
#
# Template Syntax:
#   (b) ... Mapper binary path
#     (b1) - (bn) ... nth binary path if multiple mapper binaries are used (i.e. separate binary for building indices)
# 	(r) ... Reference input
# 	(q) ... Query read file(s)
# 	  (q1) ... Query read file 1 (only use in command_multi_read_files)
# 	  (q2) ... Query read file 2 (only use in command_multi_read_files)
# 	(o) ... Mapping output
# 	(p) ... If input is paired end, at this position the value of param_paired will be inserted
#   (x) ... Additional parameters
#   (t) ... Number of threads
class MapperGeneric(Mapper):
	hashes = {}

	def __init__(self, name, config):
		self.name = name
		self.title = name
		if "title" in config:
			self.title = config["title"]

		self.binary_path = config["bin"]
		self.params = {}
		self.is_paired = False
		self.read_files = []

		self.command = config["command"]
		self.command_multiread = config["command_multi_read_files"]
		self.command_index = config["command_index"]
		self.command_cleanup = config["command_cleanup"]
		self.param_paired = config["param_paired"]
		self.thread_count = 1

		self.param_string = ""
		if "param_string" in config:
			self.param_string = config["param_string"]

		self.index_files = config["index_files"]
		self.temporary_files = []
		if "temporary_files" in config:
			self.temporary_files = config["temporary_files"]
		self.config_hash = hashlib.md5(str(config)).hexdigest()

	def onMapPre(self):
		pass

	def onMapPost(self):
		pass

	def onCleanup(self):
		for file in self.temporary_files:
			try:
				os.remove(self.fillPlaceholders(file))
			except:
				pass

	def getBinaryHash(self):
		if isinstance(self.binary_path, basestring):
			return self.getPathHash(self.binary_path)
		else:
			return hashlib.md5("".join([self.getPathHash(path) for path in self.binary_path])).hexdigest()

	def getPathHash(self, path):
		if not path in MapperGeneric.hashes:
			text = open(path, "r").read()
			MapperGeneric.hashes[path] = hashlib.md5(text).hexdigest()

		return hashlib.md5(self.name + MapperGeneric.hashes[path]).hexdigest()

	def getConfigHash(self):
		return self.config_hash

	def getBinaryPath(self):
		return self.binary_path

	def getName(self):
		return self.name

	def getId(self):
		return self.getName()

	def setInReferenceFile(self, ref):
		self.params["ref"] = ref

	def setInReadFiles(self, reads):
		self.read_files = reads

	def setInPaired(self, is_paired):
		self.is_paired = is_paired

	def setOutMappingFile(self, outfile):
		self.params["output"] = outfile

	def setThreadCount(self, threadc):
		self.thread_count = threadc

	def addParams(self, params):
		pass

	def resetParams(self):
		self.params = {}

	def fillPlaceholders(self, text):
		if len(self.read_files) <= 1:
			text = text.replace("(q)", self.read_files[0])

		else:
			i = 1
			for curr in self.read_files:
				text = text.replace("(q" + str(i) + ")", curr)
				i = i + 1

		if self.is_paired:
			text = text.replace("(p)", self.param_paired)
		else:
			text = text.replace("(p)", "")

		text = text.replace("(r)", self.params["ref"])
		text = text.replace("(o)", self.params["output"])
		text = text.replace("(x)", self.param_string)

		if isinstance(self.binary_path, basestring):
			text = text.replace("(b)", self.binary_path)
		else:
			i = 1
			for path in self.binary_path:
				text = text.replace("(b%d)" % i, path)
				i += 1

		text = text.replace("(t)", str(self.thread_count))

		return text

	def prepareCommand(self, cmd_single, cmd_multiread):
		if len(self.read_files) <= 1:
			cmd = cmd_single
		else:
			cmd = cmd_multiread

		return self.fillPlaceholders(cmd)

	def indexExists(self):
		for index_file in self.index_files:
			if not os.path.isfile(self.fillPlaceholders(index_file)):
				print("Index missing: " + self.fillPlaceholders(index_file))
				return False
		return True

	def getCommandLinePre(self):
		if self.indexExists():
			return ""
		else:
			return self.prepareCommand(self.command_index, self.command_index)

	def getCommandLineMain(self):
		return self.prepareCommand(self.command, self.command_multiread)

	def getCommandLinePost(self):
		return self.prepareCommand(self.command_cleanup, self.command_cleanup)


#Dedicated Mapper Wrapper Example: NGM
#For frequently tested mappers, instead of repetitively defining them using the generic wrapper,
#it is advisable to create a dedicated wrapper class instead
class MapperNGM(Mapper):
	hashes = {}

	def __init__(self, name, config):
		self.name = name
		self.title = name
		if "title" in config:
			self.title = config["title"]

		self.binary_path = config["bin"]
		self.params = {}
		self.params_append = []
		self.is_paired = False
		self.read_files = []
		self.hash = None
		self.config_hash = hashlib.md5(str(config)).hexdigest()
		self.thread_count = 1

		self.param_string = ""
		if "param_string" in config:
			self.param_string = config["param_string"]

	def onMapPre(self):
		self.onCleanup()

	def onMapPost(self):
		self.onCleanup()

	def onCleanup(self):
		return

		try:
			os.remove(self.params["ref"] + "-enc.ngm")
		except OSError:
			pass

		try:
			os.remove(self.params["ref"] + "-ht-13-2.ngm")
		except OSError:
			pass

		try:
			os.remove(self.params["ref"] + "-enc.2.ngm")
		except OSError:
			pass

		try:
			os.remove(self.params["ref"] + "-ht-13-2.2.ngm")
		except OSError:
			pass

	def getBinaryHash(self):
		if not self.binary_path in MapperNGM.hashes:
			text = open(self.binary_path, "r").read()  # ngm
			text = text + open(self.binary_path + "-core", "r").read()  # ngm-core
			MapperNGM.hashes[self.binary_path] = hashlib.md5(text).hexdigest()

		return MapperNGM.hashes[self.binary_path]

	def getConfigHash(self):
		return self.config_hash

	def getBinaryPath(self):
		return self.binary_path

	def getName(self):
		return self.name

	def getId(self):
		return self.getName()

	def setInReferenceFile(self, ref):
		self.params["ref"] = ref

	def setInReadFiles(self, reads):
		self.read_files = reads

	def setInPaired(self, is_paired):
		self.is_paired = is_paired

	def setOutMappingFile(self, outfile):
		self.params["output"] = outfile

	def setThreadCount(self, threadc):
		self.thread_count = threadc

	def addParams(self, params):
		if self.name in params:
			params_kv = params[self.name]
			for k in params_kv:
				self.params[k] = params_kv[k]

		params_kv = params["ngm"]
		for k in params_kv:
			self.params[k] = params_kv[k]

	def resetParams(self):
		self.params = {}
		self.params_append = []

	def indexExists(self):
		exists = True
		for index_file in [self.params["ref"] + "-enc.ngm", self.params["ref"] + "-ht-13-2.ngm"]:
			if not os.path.isfile(index_file):
				exists = False
				break

		if exists:
			return True

		for index_file in [self.params["ref"] + "-enc.2.ngm", self.params["ref"] + "-ht-13-2.2.ngm"]:
			if not os.path.isfile(index_file):
				return False
		return True

	def getCommandLinePre(self):
		if self.indexExists():
			return ""
		else:
			return self.binary_path + " --ref " + self.params["ref"] + " "

	def getCommandLineMain(self):
		if self.is_paired:
			if len(self.read_files) == 1:
				self.params["qry"] = self.read_files[0]
				self.params["p"] = ""
			else:
				self.params["qry1"] = self.read_files[0]
				self.params["qry2"] = self.read_files[1]
		else:
			self.params["qry"] = " ".join(self.read_files)

		self.params["t"] = self.thread_count

		param_string = ""
		for key in self.params:
			prefix = ""
			if len(key) > 1:
				prefix = "--"
			else:
				prefix = "-"

			param_string += prefix + key + " "

			if self.params[key] != None:
				param_string += str(self.params[key]) + " "

		param_string += " ".join(self.params_append)
		param_string += self.param_string

		cmd = self.binary_path + " " + param_string + " --no-progress"

		return cmd

	def getCommandLinePost(self):
		return ""
