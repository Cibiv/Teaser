import copy
import subprocess
import os
import time
import hashlib
import traceback
import sys
import resource

import yaml


from lib import util

merge = util.merge

#
# Teaser
# A read mapper benchmark framework
#
# =================================================================
# Test class
# Represents a single test; Implements loading, inheritance, pipelines,
# serialization
# =================================================================
class Test:
	yaml_cache = {}

	def __init__(self, id, name, directory, mate, mapper):
		self.pipeline_types = ["init", "main", "cleanup", "versioned_evaluate", "report_overview", "report_detail"]

		self.id = id
		self.name = name

		self.config = {}
		self.config_main = mate.getConfig()
		self.directory = directory
		self.mapper = mapper
		self.was_run = False
		self.finished_run = False
		self.run_time = 0

		self.warnings = []
		self.errors = []

		self.run_results = None
		self.run_results_human = None
		self.sub_results = []

		# Non-serialized fields
		self.mate = mate
		self.script_locals = {"self": self}
		self.old_working_directory = os.getcwd()
		self.in_working_directory = False
		self.comparison_test = None

		self.max_errors = 10
		self.max_warnings = 10

	# Config getter shortcut
	def _(self, field, default=None):
		value = self.getConfig()
		for part in field.split(":"):
			if part in value:
				value = value[part]
			else:
				return default
		if value==None:
			return default
		else:
			return value

	def setc(self, field, new_value):
		value = self.getConfig()
		parts = field.split(":")
		last_part = parts[-1]
		parts_tree = [parts[p] for p in range(len(parts) - 1)]
		for part in parts_tree:
			if part in value:
				value = value[part]
			else:
				value[part] = {}
				value = value[part]

		value[last_part] = new_value

	def getReportDirectory(self):
		return self.mate.getReportDirectory()

	def log(self, text, level=2, newline="\n"):
		self.mate.log(text, level, newline)

	def dbg(self, text, prefix="INFO"):
		self.log(text)

	def warn(self, text, affected_file=None, affected_pos=None):
		if len(self.warnings) == self.max_warnings:
			self.dbg("Maximum number of warnings exceeded for test", "WARNING")
			self.warnings.append(("Maximum number of warnings exceeded for test", None, None))
			return
		elif len(self.warnings) > self.max_warnings:
			return

		self.dbg(text + " at " + str(affected_file) + ":" + str(affected_pos), "WARNING")
		self.warnings.append((text, affected_file, affected_pos))

	def error(self, text, affected_file=None, affected_pos=None):
		if len(self.errors) == self.max_errors:
			self.dbg("Maximum number of errors exceeded for test", "WARNING")
			self.errors.append(("Maximum number of errors exceeded for test", None, None))
			return
		elif len(self.errors) > self.max_errors:
			return

		self.dbg(text + " at " + str(affected_file) + ":" + str(affected_pos), "ERROR")
		self.errors.append((text, affected_file, affected_pos))
		self.mate.traceback()

	def fatal_error(self, text, affected_file=None, affected_pos=None):
		self.error(text, affected_file, affected_pos)
		self.mate.traceback()
		raise SystemExit

	def getWarnings(self):
		return self.warnings

	def getErrors(self):
		return self.errors

	def getSuccess(self):
		return self.getErrorCount() == 0

	def getErrorCount(self):
		return len(self.errors)

	def getWarningCount(self):
		return len(self.warnings)

	def getComment(self):
		if "comment" in self.config:
			return self.config["comment"]
		else:
			return ""

	def getVersionHash(self):
		extensions = [".py", ".yaml"]

		# Calcs hash for all logic, test case definitions
		text = ""

		for root, dirs, files in os.walk(self.directory + "/" + self.name):
			for filename in files:
				name, ext = os.path.splitext(filename)
				if ext in extensions:
					with open(root + "/" + filename, "r") as handle:
						text = text + handle.read()  # str(os.path.getmtime(root + "/" + filename))

		text += self.directory + "/" + self.name
		text += self.getMapper().getBinaryHash() + str(self.getMapper().getConfigHash())

		return hashlib.md5(text).hexdigest()

	def serialize(self):
		ser = {}
		ser["name"] = self.name
		ser["path"] = self.path
		ser["config"] = self.config
		ser["config_main"] = self.config_main
		ser["directory"] = self.directory
		ser["mapper"] = self.mapper
		ser["was_run"] = self.was_run
		ser["finished_run"] = self.finished_run
		ser["run_time"] = self.run_time
		ser["warnings"] = self.warnings
		ser["errors"] = self.errors
		ser["run_results"] = self.run_results
		ser["run_results_human"] = self.run_results_human
		ser["sub_results"] = self.sub_results

		return ser

	def unserialize(self, ser):
		self.name = ser["name"]
		self.path = ser["path"]
		self.config = ser["config"]
		self.config_main = ser["config_main"]
		self.directory = ser["directory"]
		self.mapper = ser["mapper"]
		self.was_run = ser["was_run"]
		self.finished_run = ser["finished_run"]
		self.run_time = ser["run_time"]
		self.warnings = ser["warnings"]
		self.errors = ser["errors"]
		self.run_results = ser["run_results"]
		self.run_results_human = ser["run_results_human"]
		self.sub_results = ser["sub_results"]

	def getLocals(self):
		return self.script_locals

	def buildAbsoluteScriptPath(self, filename):
		if "/" in filename:
			# TODO: Fix me for multiple dir. layers
			parts = filename.split("/")

			if len(parts) == 2:
				packagename = parts[0]
				scriptname = parts[1]
				return self.directory + "/" + packagename + "/" + scriptname
			else:
				return filename
		else:
			return self.path + "/" + filename

	def getTestDirectoryByPath(self, test_name_full):
		if "/" in test_name_full:
			# TODO: Fix me for multiple dir. layers
			parts = test_name_full.split("/")
			test_dir = parts[0]
			test_name = parts[1]
			return test_dir
		else:
			return self.directory

	def getTestNameByPath(self, test_name_full):
		if "/" in test_name_full:
			# TODO: Fix me for multiple dir. layers
			parts = test_name_full.split("/")
			test_dir = parts[0]
			test_name = parts[1]
			return test_name
		else:
			return test_name_full

	def load(self):
		# Load test configuration from metafile in test directory
		path = self.directory + "/" + self.getName()
		config_path = path + "/" + self.getName() + ".yaml"
		test_config = None

		try:
			if not config_path in Test.yaml_cache:
				with open(config_path, "r") as test_config_file_handle:
					test_config_text = test_config_file_handle.read()
					test_config = yaml.load(test_config_text)
					if test_config is None:
						self.log("Failed to parse YAML")
						raise IOError("")
					else:
						# Backwards-Compatibility
						if "test" in test_config:
							# self.log("Test "+self.name+"'s config format is deprecated! (Remove 'test:' structure)")
							test_config = merge(test_config, test_config["test"])

						# Set test meta parameters in config
						test_config["_name"] = self.name
						test_config["_path"] = path

						Test.yaml_cache[config_path] = copy.deepcopy(test_config)

			else:
				test_config = copy.deepcopy(Test.yaml_cache[config_path])

		except IOError as e:
			self.mate.error("Failed to load meta-information from \"" + config_path + "\": " + str(e))
			raise Exception()

		# Start using test configuration
		self.config = test_config
		self.path = path

		if self.config == None:
			return False

		# Make script paths absolute
		if "pipeline" in self.config:
			for pname in self.pipeline_types:
				if pname in self.config["pipeline"]:
					for k, v in enumerate(self.config["pipeline"][pname]):
						self.config["pipeline"][pname][k] = self.buildAbsoluteScriptPath(v + ".py")

		# Handle inheritance
		if "base" in self.config and self.config["base"] != None:
			parent_test = Test("", self.getTestNameByPath(self.config["base"]),
							   self.getTestDirectoryByPath(self.config["base"]), self.mate, self.mapper)
			parent_test.load()

			# Special case default values
			parent_test.config["run"] = True
			parent_test.config["is_basic"] = False

			self.config = merge(parent_test.config, self.config)

		return True

	def getParentTest(self):
		if "base" in self.config:
			return str(self.config["base"])
		else:
			return ""

	def evaluate(self):
		self.executePipeline("versioned_evaluate")

	def getMapper(self):
		return self.mapper

	def getName(self):
		return self.name

	def getFullName(self):
		return self.getName() + "_" + self.getMapper().getName()

	def getId(self):
		return self.id

	def getTitle(self):
		if "title" in self.config:
			if self.config["title"] == "A Basic Simulated Mapping Test":
				self.config["title"] = self.getName()
			return self.config["title"]
		else:
			return self.getName()

	def getPath(self):
		return self.path

	def getConfig(self):
		return self.config

	def getRunTime(self):
		return self.run_time

	def getCreateTime(self):
		if "create_time" in self.config:
			return self.config["create_time"]
		else:
			return 0

	def getShouldRun(self):
		if not self.config:
			return False

		return (not self.getIsBasic()) and ("run" in self.config and self.config["run"])

	def getWasRun(self):
		return self.was_run

	def getWasFinished(self):
		return self.finished_run

	def getSuccess(self):
		return len(self.errors) == 0 and self.getWasRun()

	def getIsBasic(self):
		return "is_basic" in self.config and self.config["is_basic"]

	def getResultOverviewText(self, indent=""):
		text = ""
		errcount = len(self.errors)
		warncount = len(self.warnings)
		report_str = self.getName() + " "

		if not self.getWasFinished():
			text = text + indent + "ABORTED: " + report_str + "(See logs)\n"
			return text

		if warncount + errcount == 0:
			text = text + indent + "SUCCESS: " + report_str + "\n"
		elif errcount == 0:
			text = text + indent + "SUCCESS: " + report_str + "(" + str(warncount) + " Warnings)\n"
		else:
			text = text + indent + "FAILURE: " + report_str + "(" + str(errcount) + " Errors, " + str(
				warncount) + " Warnings)\n"

		for err_text, err_file, err_pos in self.errors:
			err = err_text + ", at " + str(err_file) + ":" + str(err_pos) + ""

			text = text + indent + "\t- Error: " + err + "\n"

		for warn_text, warn_file, warn_pos in self.warnings:
			warn = warn_text + ", at " + str(warn_file) + ":" + str(warn_pos) + ""
			text = text + indent + "\t- Warning: " + warn + "\n"

		if warncount + errcount > 0:
			text = text + "\n"

		return text

	def consoleReport(self):
		errcount = len(self.errors)
		warncount = len(self.warnings)

		if not self.getWasFinished():
			self.log("Status: ABORTED (See logs)")
			return text

		if warncount + errcount == 0:
			self.log("Status: SUCCESS")
		elif errcount == 0:
			self.log("Status: SUCCESS")
			self.log(str(warncount) + " Warnings")
		else:
			self.log("Status: FAILURE")
			self.log(str(errcount) + " Errors, " + str(warncount) + " Warnings")

		for err_text, err_file, err_pos in self.errors:
			err = err_text + ", at " + str(err_file) + ":" + str(err_pos) + ""

			self.log("\t- Error: " + err)

		for warn_text, warn_file, warn_pos in self.warnings:
			warn = warn_text + ", at " + str(warn_file) + ":" + str(warn_pos) + ""
			self.log("\t- Warning: " + warn)

	def executePipeline(self, event, args=()):
		result = None

		try:
			script_locals = {}

			self.enterWorkingDirectory()

			self.restoreWorkingDirectory()
			if event in self.getConfig()["pipeline"]:
				for script in self.getConfig()["pipeline"][event]:
					script_name, script_ext = os.path.splitext(script)
					script_name = os.path.basename(script_name)

					self.mate.pushLogPrefix(script_name)
					execfile(script, script_locals, script_locals)
					result = script_locals[script_name](self, *args)
					self.mate.popLogPrefix()
					self.restoreWorkingDirectory()

		except Exception as e:
			self.log(
				"\t*** [INTERNAL] Error occured executing pipeline " + event + " on test " + self.getName() + ": " + str(
					e) + ", traceback: " + traceback.format_exc())
			self.error(
				"Error occured executing pipeline " + event + ": " + str(e) + ", traceback: " + traceback.format_exc(),
				"Test " + self.getName(), event)

		except KeyboardInterrupt:
			raise KeyboardInterrupt

		finally:
			self.restoreWorkingDirectory()

		return result

	def run(self):
		start_time = time.time()
		self.executePipeline("init")
		self.executePipeline("cleanup")

		self.was_run = True
		self.executePipeline("main")

		end_time = time.time()
		self.run_time = end_time - start_time
		self.finished_run = True

	def sub(self,command,description="",detailed=False):
		result = util.runAndMeasure(command, detailed, self.mate._("sub_max_runtime"), self.mate._("sub_max_memory"))
		status=result["status"]

		if status != util.STATUS_NORMAL:
			if status == util.STATUS_MAX_MEMORY_EXCEEDED:
				self.error("Subprocess exceeded maximum allowed memory: %s" % command)
			elif status == util.STATUS_MAX_RUNTIME_EXCEEDED:
				self.error("Subprocess exceeded maximum allowed runtime: %s" % command)
			else:
				self.error("Unknown error occured executing subprocess: %s" % command)

		self.sub_results.append((result, description))

		self.log("[SUBPROCESS] " + command + "\n" + str(result).decode('string_escape'), 3)

		return result

	def enterWorkingDirectory(self):
		if self.in_working_directory:
			return

		self.old_working_directory = os.getcwd()
		if self._("working_directory")[0] == "/":
			working_directory = self._("working_directory")
		else:
			working_directory = self.getPath() + "/" + self._("working_directory") + "/"
		os.chdir(working_directory)

		self.in_working_directory = True

	def restoreWorkingDirectory(self):
		if not self.in_working_directory:
			return

		os.chdir(self.old_working_directory)
		self.in_working_directory = False

	def cleanup(self):
		# self.log("\t\t[INFO] Triggering Cleanup for " + self.getName() + " ...")
		self.executePipeline("cleanup")

	def setRunResults(self, results):
		self.run_results = results

	def getRunResults(self):
		return self.run_results

	def setHumanizedRunResults(self, results):
		self.run_results_human = results

	def getHumanizedRunResults(self):
		return self.run_results_human

	def getSubResults(self):
		return self.sub_results

	def getComparisonTest(self):
		return self.comparison_test

	def setComparisonTest(self, comp):
		self.comparison_test = comp

	def getCSVPath(self,title):
		filename = self.getName()+"_"+title+".csv"
		return filename,self.mate.getReportDirectory()+"/"+filename

	def writeCSV(self,title,csv):
		filename,path=self.getCSVPath(title)
		with open(path,"w") as handle:
			handle.write(csv)
		self.log("Wrote CSV to %s"%path)

		return filename
