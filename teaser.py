#!/usr/bin/env python

#
# Teaser
# A read mapper benchmark framework
#
#
# =================================================================================
# Main class
# Coordinates loading, execution, caching of and interaction between tests
# Further coordinates execution of Teaser and report generation
# =================================================================================
#
#

class Mate:
	def __init__(self):
		self.deployment_mode = "production"

		self.config = False
		self.config_original = False
		self.script_locals = {"self": self}
		self.tests_run_count = 0
		self.tests_success_count = 0
		self.tests_err_count = 0
		self.tests_warn_count = 0
		self.tests_aborted_count = 0
		self.run_only = False
		self.is_stats_run = True
		self.no_cleanup = False
		self.force_run = False
		self.force_gen = False
		self.tests = {}
		self.run_id = str(int(time.time()))
		self.version_hash = False
		self.clear_fs_cache = False
		self.list_tests = False
		self.tests_ran = 0
		self.mapper_list = False
		self.parameter_list = False

		self.measure_cputime = False
		self.measure_preload = False

		self.report_name = None
		self.report = False
		self.current_test = None
		self.teaser = None

		self.log_file_handle = False
		self.log_file_buffer = ""
		self.log_file_contents = ""
		self.log_prefix = [""]
		self.log_indent = " -> "

		self.computed_runtime_files = []

		self.publicate_export = False

		self.errors = []
		self.warnings = []

	def error(self, msg):
		self.log(msg)
		self.errors.append(msg)

		if self.report != False:
			self.report.generateProgress()

	def warning(self, msg):
		self.log(msg)
		self.warnings.append(msg)

		if self.report != False:
			self.report.generateProgress()

	def getErrors(self):
		return self.errors

	def getWarnings(self):
		return self.warnings

	def version(self):
		return "1.0b-dev"

	def getLogPrefix(self):
		return self.log_prefix[len(self.log_prefix) - 1]

	def pushLogPrefix(self, prefix, left="[", right="] "):
		prefix = prefix.ljust(12, " ")
		p = left + prefix + right
		self.log_prefix.append(p)

	def pushLogPrefixRaw(self, prefix):
		self.log_prefix.append(prefix)

	def popLogPrefix(self):
		self.log_prefix.pop()

	def log(self, text, level=2, newline="\n"):
		text = "[" + datetime.now().strftime("%H:%M:%S") + "] " + self.getLogPrefix() + str(text)

		if self._("debug_level", level) >= level:
			if self._("debug_out_console", True):
				sys.stdout.write(text + newline)
				sys.stdout.flush()

			if self.log_file_handle != False:
				if self.log_file_buffer != "":
					self.log_file_handle.write(self.log_file_buffer)
					self.log_file_buffer = ""
				self.log_file_handle.write(text + newline)
				self.log_file_handle.flush()
			else:
				self.log_file_buffer += text + newline

			self.log_file_contents += text + newline

	def logNewline(self, text="", level=2, newline="\n"):
		if self._("debug_level", level) >= level:
			if self._("debug_out_console", True):
				sys.stdout.write(text + newline)
				sys.stdout.flush()

			if self.log_file_handle != False:
				if self.log_file_buffer != "":
					self.log_file_handle.write(self.log_file_buffer)
					self.log_file_buffer = ""
				self.log_file_handle.write(text + newline)
				self.log_file_handle.flush()
			else:
				self.log_file_buffer += text + newline

			self.log_file_contents += text + newline

	def getLogFileContents(self):
		return self.log_file_contents

	def traceback(self):
		self.log(traceback.format_exc())

	def log_traceback(self, msg):
		self.log("%s, exception: %s" % (msg, traceback.format_exc()))

	# Config getter shortcut
	def _(self, field, default=None):
		if not self.config:
			return default

		value = self.config
		for part in field.split(":"):
			if part in value:
				value = value[part]
			else:
				return default
		return value

	def executeEvent(self, event):
		self.current_event = event

		event_inline = event + "Inline"

		if event_inline in self.config:
			for code in self.config[event_inline]:
				exec(code, globals(), self.script_locals)


	def getTesteeID(self):
		if self.getIsStatsRun():
			return None
		else:
			return self.config["mapper_testee"]

	def getBaseID(self):
		if self.getIsStatsRun():
			return None
		else:
			return self.config["mapper_base"]

	def getConfig(self):
		# Set by main method
		return self.config

	def getRunID(self):
		return self.run_id

	def getReportName(self):
		if not "name" in self.config["report"]:
			return str(self.run_id) + "-" + self.getCondensedVersionHash()
		else:
			return self.config["report"]["name"]

	def getReportDirectory(self):
		return self._("report:directory") + "/" + self._("report:name")

	def initReport(self):
		if not os.path.exists(self.getReportDirectory()):
			os.makedirs(self.getReportDirectory())

		self.report = report.ReportHTMLGenerator(mate, False)
		self.report.generateProgress()

	def getReport(self):
		return self.report

	def getIsStatsRun(self):
		return self.is_stats_run

	def getVersionHash(self):
		return "dev"

		if self.version_hash != False:
			return self.version_hash

		extensions = [".py", ".yaml"]

		text = ""

		dirs = ["./lib", "./tests_base"]
		exclude_files = []

		for filename in os.listdir("."):
			name, ext = os.path.splitext(filename)

			if ext in extensions:
				text = text + open(filename, "r").read()

		for curr_dirname in dirs:
			for root, dirs, files in os.walk(curr_dirname):
				for filename in files:
					name, ext = os.path.splitext(filename)

					if ext in extensions and not filename in exclude_files:
						text = text + open(root + "/" + filename, "r").read()

		self.version_hash = hashlib.md5(text).hexdigest()
		return self.version_hash

	def getCondensedVersionHash(self):
		condensed_len = 5
		long_hash = self.getVersionHash()
		condensed_hash = ""

		seed = 0

		for i in range(0, 5):
			seed = seed + ord(long_hash[i % len(long_hash)])

		for i in range(condensed_len):
			seed = 7721387812838 * seed + 12345678
			condensed_hash += long_hash[seed % len(long_hash)]

		return str(condensed_hash)

	def cleanCache(self):
		# if self.no_cleanup:
		#	return

		version = self.getVersionHash()
		cleaned = 0

		for filename in os.listdir(self.config["cache_directory"]):
			parts = filename.split("_")
			name, ext = os.path.splitext(filename)

			if ext == ".test" and parts[0] != version:
				os.remove(self.config["cache_directory"] + "/" + filename)
				cleaned = cleaned + 1

		if cleaned > 0:
			self.log("Cleaned " + str(cleaned) + " tests from cache")

	def cleanCacheFull(self):
		# if self.no_cleanup:
		#	return

		version = self.getVersionHash()
		cleaned = 0

		for filename in os.listdir(self.config["cache_directory"]):
			name, ext = os.path.splitext(filename)

			if ext == ".test":
				os.remove(self.config["cache_directory"] + "/" + filename)
				cleaned = cleaned + 1

		if cleaned > 0:
			self.log("Cleaned " + str(cleaned) + " tests from cache (full clean)")

	def triggerCleanupEvents(self, tests):
		if self.no_cleanup:
			return

		for test_name in tests:
			the_test = tests[test_name]

			if the_test.getWasRun():
				the_test.cleanup()

	def getTestCachedPath(self, test):
		return self.getCachePathPrefix() + test.getVersionHash() + ".test"

	def getCachePathPrefix(self):
		return self.config["cache_directory"] + "/" + self.framework_hash + "_"

	def loadTestsFor(self, mapper_id):
		mapper_conf = self.config["mappers"][mapper_id]
		mapper_module = util.locate("lib.mapper")

		if mapper_conf["type"] == "ngm":
			mapper_class = "MapperNGM"
		else:
			mapper_class = mapper_conf["type"]

		the_class = getattr(mapper_module, mapper_class)

		inst = the_class(mapper_id,mapper_conf)
		try:
			bin_hash = inst.getBinaryHash()
		except:
			self.error("Failed to access mapper binary %s for mapper %s" % (str(inst.getBinaryPath()),mapper_id))
			return []

		tests = {}

		for test_directory in self.config["test_directories"]:
			for test_short_name in os.listdir(test_directory):
				test_id = test_directory.replace("/", "_") + "_" + mapper_id + "_" + test_short_name
				test_name = test_short_name

				try:
					if not os.path.isdir(test_directory + "/" + test_short_name):
						continue

					self.pushLogPrefixRaw("[Load " + test_short_name + "] ")

					mapper_inst = the_class(mapper_id, mapper_conf)
					mapper_inst.setThreadCount(self._("threads"))

					# Try to load test object from cache
					the_test = test.Test(test_id, test_short_name, test_directory, self, mapper_inst)

					if self.run_only != False and not test_name in self.run_only:
						self.popLogPrefix()
						continue

					the_test.load()
					if not self.isTestIncluded(the_test):
						self.log("Cancelling loading (not included)")
						self.popLogPrefix()
						continue

					if not self.force_run and self.config["cache_results"]:
						cached_path = self.getTestCachedPath(the_test)

						if os.path.isfile(cached_path):
							# Cached version of test object with results present
							self.log(
								"Loading cached version of " + the_test.getName() + "<" + mapper_id + "> " + cached_path)
							try:
								the_test.unserialize(pickle.load(open(cached_path, "r")))
								the_test.executeEvent("onInit")
							except Exception:
								pass
						else:
							the_test.load()

					the_test.internal_name = test_name
					tests[test_name] = the_test
					self.popLogPrefix()

				except Exception as e:
					self.popLogPrefix()
					self.error("Failed to load test %s for %s" % (test_short_name,mapper_id) )
					#self.log_traceback("Loading failed for " + test_short_name)

		return tests

	def getTestList(self):
		tests = []
		for mapper in self.tests:
			tests.extend([self.tests[mapper][t] for t in self.tests[mapper]])
		return tests

	def getTestNameList(self):
		if self.run_only != False:
			return self.run_only

		test_names = []

		for mapper_id in self.tests:
			for test_name in self.tests[mapper_id]:
				if not test_name in test_names:
					test_names.append(test_name)

		return sorted(test_names)

	def getTestsByName(self, target_test_name):
		test_objects = []

		for mapper_id in self.tests:
			for test_name in self.tests[mapper_id]:
				if test_name == target_test_name:
					test_objects.append(self.tests[mapper_id][test_name])
		return test_objects

	def getTestByMapperName(self, test_name, mapper_id):
		try:
			return self.tests[mapper_id][test_name]
		except:
			return None

	def getMappers(self):
		return self.tests.keys()

	def getSortedMapperList(self):
		return sorted(self.tests, key=self.tests.get)

	def isTestIncluded(self, the_test):
		should_run = True

		if self.config["include_tags"] != None:
			should_run = False

			if the_test._("tags") != None:
				for tag in the_test._("tags"):
					if tag in self.config["include_tags"]:
						should_run = True
						break

		if self.config["ignore_tags"] != None:
			if the_test._("tags") != None:
				for tag in the_test._("tags"):
					if tag in self.config["ignore_tags"]:
						should_run = False
						break

		return should_run

	def getTestsToRunCount(self):
		run_count = 0

		for mapper_id in self.config["test_mappers"]:
			if not mapper_id in self.tests:
				continue
			for test_name in self.tests[mapper_id]:
				if self.shouldRunTest(self.tests[mapper_id][test_name]):
					run_count += 1

		return run_count

	def getTestsRanCount(self):
		return self.tests_ran

	def shouldRunTest(self, the_test):
		if not self.is_stats_run and not the_test._("is_version_relative") and the_test.getMapper().getId() != self.config["mapper_testee"]:
			return False

		if not self.isTestIncluded(the_test):
			return False

		if self.run_only != False:
			if not the_test.getName() in self.run_only:
				return False

		return True

	def getCurrentTest(self):
		return self.current_test

	def getTeaser(self):
		return self.teaser

	def clearFilesystemCache(self):
		if self.clear_fs_cache:
			self.log("Clearing filesystem cache! (-cfs)")
			os.system("sudo /sbin/clearcache.sh")

	def runTests(self, tests):
		tests_sorted = []

		for test_name in tests:
			tests_sorted.append(test_name)

		tests_sorted.sort()

		for test_name in tests_sorted:
			the_test = tests[test_name]

			if not self.shouldRunTest(the_test):
				continue

			if the_test.getWasRun():
				# Already ran, probably was loaded from cache
				self.log("Skip: " + the_test.getName() + "<" + the_test.getMapper().getName() + "> (already run)")
				self.logNewline()
				continue

			if not the_test.getShouldRun():
				continue

			self.log(the_test.getName() + " (base: " + the_test.getParentTest() + ")")

			self.pushLogPrefixRaw(self.log_indent)

			try:
				self.clearFilesystemCache()

				self.current_test = the_test
				self.report.generateProgress()
				self.tests_ran += 1
				the_test.run()
				self.report.generateProgress()

			except KeyboardInterrupt:
				print("Terminate only current test (y/n)? (Default: Terminate run)")
				choice = raw_input()
				if len(choice) > 0 and choice[0] == "y":
					self.log("\t*** [INTERNAL] User triggered test abort")
					the_test.warn("User triggered abort", "Test " + the_test.getName())
				else:
					raise SystemExit

			except SystemExit:
				the_test.warn("The test was aborted by the system")


			except Exception as e:
				self.log("\t*** [INTERNAL] Fatal error caused test abort: " + str(
					e) + ", traceback: " + traceback.format_exc())
				the_test.error("Fatal error caused test abort: " + str(e) + ", traceback: " + traceback.format_exc(),
							   "Test " + the_test.getName())

			except:
				self.log(
					"\t*** [INTERNAL] Fatal unidentified error caused test abort, " + ", traceback: " + traceback.format_exc())
				the_test.error("Fatal unidentified error caused test abort" + ", traceback: " + traceback.format_exc(),
							   "Test " + the_test.getName())

			finally:
				the_test.restoreWorkingDirectory()

			self.popLogPrefix()

			if the_test.getWasFinished() and self.config["cache_results"]:
				cached_path = self.getTestCachedPath(the_test)
				if the_test.getSuccess():
					pickle.dump(the_test.serialize(), open(cached_path, "w"))
				else:
					try:
						os.remove(cached_path)
					except:
						pass
					self.log("Errors in test, not caching!")

			# self.log("")
			self.logNewline()

	def evaluateTests(self, tests, comparison_tests):
		for test_name in tests:
			the_test = tests[test_name]

			if the_test.getWasRun():
				if the_test._("is_version_relative"):
					if comparison_tests == None:
						self.log(
							"\t!!! Skipping evaluation of test " + test_name + " (test is version relative but doing a statistics run)")
						return
					else:
						the_test.setComparisonTest(comparison_tests[test_name])

				if not self.is_stats_run:
					self.log(the_test.getName() + " (base: " + the_test.getParentTest() + ")")
				self.pushLogPrefix("\t", "", "")

				the_test.evaluate()

				if self._("debug_level") <= 1:
					self.log(the_test.getResultOverviewText(), 1, "")

				self.popLogPrefix()

				if not the_test.getWasFinished():
					self.tests_aborted_count = self.tests_aborted_count + 1
					continue

				self.tests_run_count = self.tests_run_count + 1

				if the_test.getSuccess():
					self.tests_success_count = self.tests_success_count + 1

	def createArgParser(self):
		parser = argparse.ArgumentParser(description="Teaser - a read mapper benchmark framework")
		parser.add_argument("config", help="The test run configuration file to use", default="base_teaser.yaml", nargs="?")
		parser.add_argument("-t", "--test", help="Run the and only the specified tests (separate with comma)", default="")
		#parser.add_argument("-q", "--qrun", help="Quality-control run, run only for testee and base mappers",
		#					default=False, action="store_true")
		parser.add_argument("-nc", "--nocleanup", help="Dont clean up output / temporary files", default=False,
							action="store_true")
		#parser.add_argument("-ign", "--ignore",
		#					help="Comma-separated list of ignore tags (overwrites value from run config if set)",
		#					default=None)
		#parser.add_argument("-inc", "--include",
		#					help="Comma-separated list of include tags (overwrites value from run config if set)",
		#					default=None)
		#parser.add_argument("-mt", "--mappertestee", help="Testee mapper ID (overwrites value from run config if set)",
		#					default=None)
		#parser.add_argument("-mb", "--mapperbase",
		#					help="Comparison mapper ID (overwrites value from run config if set)", default=None)
		parser.add_argument("-m", "--mappers",
							help="Comma-separated list of mapper IDs to test", default=None)
		parser.add_argument("-p", "--parameters",
							help="Comma-separated list of parameter set IDs to test", default=None)
		parser.add_argument("-fc", "--forceclean",
							help="Force cleanup at the end of the run (clean outputs of failed tests as well)",
							default=False, action="store_true")
		parser.add_argument("-rn", "--reportname",
							help="Override for the test run report subdirectory name (Default: timestamp and mate version hash)",
							default=None)
		#parser.add_argument("-cfs", "--clearfscache", help="Clean filesystem cache before every test", default=False, action="store_true")
		#parser.add_argument("-l", "--listtests", help="List available tests and exit", default=False,
		#					action="store_true")
		parser.add_argument("-tc", "--threads", help="Mapper thread count", default=False, action="store")
		parser.add_argument("-fr", "--forcerun", help="Force run tests (do not load cached)", default=False,
							action="store_true")
		parser.add_argument("-fg", "--forcegen", help="Force generate tests (overwrite existing)", default=False,
							action="store_true")
		#parser.add_argument("-px", "--pubexport", help="", default=None, action="store_true")
		parser.add_argument("-mcpu", "--measurecputime", help="Measure mapper CPU time instead of wall clock time", default=False, action="store_true")
		parser.add_argument("-mpre", "--measurepreload", help="Initialize mappers once before measuring initialization time to avoid cache effects", default=True, action="store_true")
		parser.add_argument("-mnopre", "--nomeasurepreload", help="Do not initialize mappers an additional time before measuring initialization time to avoid cache effects", default=False, action="store_true")
		parser.add_argument("-mps", "--measurepsutil", help="Measure mapper CPU time and memory usage with psutil instead of the Python resource module", default=False, action="store_true")
		parser.add_argument("-nm", "--nomonitor", help="Do not monitor mappers for exceeding resource limits using psutil", default=False, action="store_true")
		parser.add_argument("-pc", "--picard", help="Use picard-tools for sorting alignment output files", default=False, action="store_true")

		parser.add_argument("-lm", "--listmappers", help="List available mappers", default=False, action="store_true")
		parser.add_argument("-lp", "--listparameters", help="List available parameter sets", default=False, action="store_true")
		return parser

	def convertConfigPathsToAbs(self):
		self.config["cache_directory"] = os.path.abspath(self.config["cache_directory"])

		abs_test_dirs = [os.path.abspath(dir) for dir in self.config["test_directories"]]
		self.config["test_directories"] = abs_test_dirs

		self.config["report"]["directory"] = os.path.abspath(self.config["report"]["directory"])

		for mapper_id in self.config["mappers"]:
			if isinstance(self.config["mappers"][mapper_id]["bin"], basestring):
				self.config["mappers"][mapper_id]["bin"] = os.path.abspath(self.config["mappers"][mapper_id]["bin"])
			else:
				self.config["mappers"][mapper_id]["bin"] = [os.path.abspath(path) for path in
															self.config["mappers"][mapper_id]["bin"]]

		if "teaser" in self.config:
			if "mason_path" in self.config["teaser"]:
				self.config["teaser"]["mason_path"] = os.path.abspath(self.config["teaser"]["mason_path"])

			if "dwgsim_path" in self.config["teaser"]:
				self.config["teaser"]["dwgsim_path"] = os.path.abspath(self.config["teaser"]["dwgsim_path"])

			if "reference_directory" in self.config["teaser"]:
				self.config["teaser"]["reference_directory"] = os.path.abspath(self.config["teaser"]["reference_directory"])

	def initFromArgs(self):
		parser = self.createArgParser()
		args = parser.parse_args()

		self.config_filename = args.config

		if args.test != "":
			self.run_only = args.test.split(",")

		self.no_cleanup = args.nocleanup
		self.clear_fs_cache = False #args.clearfscache
		self.force_run = args.forcerun
		self.force_gen = args.forcegen

		if args.mappers != None:
			self.mapper_list = args.mappers.split(",")

		if args.parameters != None:
			self.parameter_list = args.parameters.split(",")

		self.measure_cputime = args.measurecputime
		self.measure_preload = not args.nomeasurepreload
		self.measure_psutil = args.measurepsutil
		self.nomonitor = args.nomonitor

		if self.measure_psutil and self.nomonitor:
			self.log("Cannot use --nomonitor with --measurepsutil")
			return False

		self.list_mappers = args.listmappers
		self.list_parameters = args.listparameters

		# Load setup configuration file
		self.config, self.config_original = util.loadConfig(self.config_filename)
		if not self.config:
			self.log("Failed to load setup configuration %s" % self.config_filename)
			return False

		self.convertConfigPathsToAbs()
		
		self.config["_path"] = os.path.dirname(os.path.realpath(__file__))

		if args.threads != False:
			self.config["threads"] = args.threads

		if args.reportname != None:
			self.config["report"]["name"] = args.reportname


		if args.forceclean == True:
			self.config["force_clean"] = True

		if args.picard:
			self.log("Using picard-tools for sorting")
			util.sort_sam = util.sort_sam_picard

		return True

	def enumerateParameterConfigurations(self, top, index=0):
		if index >= len(top):
			return []

		combinations = []
		for k in top[index]:
			extra_combs = self.enumerateParameterConfigurations(top, index + 1)

			if len(extra_combs) > 0:
				for comb in extra_combs:
					if isinstance(k,basestring):
						combinations.append(k + " " + comb)
					else:
						for curr in self.expandRangeParameter(k):
							combinations.append(curr + " " + comb)
			else:
				if isinstance(k,basestring):
					combinations.append(k)
				else:
					for curr in self.expandRangeParameter(k):
						combinations.append(curr)

		return combinations

	def expandRangeParameter(self, param_range):
		def seq(start, stop, step=1):
			n = int(round((stop - start)/float(step)))
			if n>1:
				return [start + step*i for i in range(n+1)]
			else:
				return []

		param = param_range[0]
		min = param_range[1]
		max = param_range[2]
		if len(param_range) > 3:
			step = param_range[3]

		expanded=[]
		for value in seq(min,max,step):
			expanded.append(param+" "+str(value))
		return expanded

	def generateMapperParameterConfigurations(self):
		if self.parameter_list != False:
			self.config["test_parameters"] = self.parameter_list

		if not "test_parameters" in self.config:
			return

		mapper_id_counters = {}

		for parameter_set_id in self.config["test_parameters"]:
			if not parameter_set_id in self.config["parameters"]:
				self.warning("Parameter set with name '%s' not found"%parameter_set_id)
				print(self.config["parameters"])
				continue

			mapper_id = self.config["parameters"][parameter_set_id]["mapper"]

			data = self.config["parameters"][parameter_set_id]
			define = []
			generate = []

			if "define" in data:
				define = data["define"]

			if "generate" in data:
				generate = data["generate"]

			define_expanded = []
			for i, val in enumerate(define):
				if isinstance(val,basestring):
					define_expanded.append(val)
				else:
					define_expanded.extend(self.expandRangeParameter(val))

			define=define_expanded

			combinations_def = define
			combinations_gen = self.enumerateParameterConfigurations(generate)
			combinations = combinations_def + combinations_gen

			if not mapper_id in mapper_id_counters:
				mapper_id_counters[mapper_id] = 1

			for paramstring in combinations:
				mapper = copy.deepcopy(self.config["mappers"][mapper_id])
				if not "param_string" in mapper:
					mapper["param_string"] = ""
				mapper["param_string"] += " " + paramstring

				if "title" in mapper:
					mapper["title"] += " (p%d)" % mapper_id_counters[mapper_id]

				new_id = mapper_id + "_" + ("%02d" % mapper_id_counters[mapper_id])
				self.config["mappers"][new_id] = mapper
				mapper_id_counters[mapper_id] += 1

				self.config["test_mappers"].append(new_id)

			if "title" in self.config["mappers"][mapper_id]:
				self.config["mappers"][mapper_id]["title"] += " (def)"

	def mainStatsRun(self):
		self.executeEvent("onRunPre")

		if not "test_mappers" in self.config:
			self.config["test_mappers"] = []
			for mapper_id in self.config["mappers"]:
				self.config["test_mappers"].append(mapper_id)

		if self.mapper_list != False:
			self.config["test_mappers"] = []
			for pattern in self.mapper_list:
				for mapper_id in self.config["mappers"]:
					if fnmatch.fnmatch(mapper_id, pattern):
						self.config["test_mappers"].append(mapper_id)

		self.generateMapperParameterConfigurations()

		for mapper_id in self.config["test_mappers"]:
			self.tests[mapper_id] = self.loadTestsFor(mapper_id)

		for mapper_id in self.config["test_mappers"]:
			self.pushLogPrefix(mapper_id)
			self.runTests(self.tests[mapper_id])
			self.evaluateTests(self.tests[mapper_id], None)
			self.popLogPrefix()

	def mainNormalRun(self):
		testee_id = self.config["mapper_testee"]
		base_id = self.config["mapper_base"]

		self.pushLogPrefix("Load/Testee")
		self.tests[testee_id] = self.loadTestsFor(testee_id)
		self.popLogPrefix()

		self.pushLogPrefix("Load/Base")
		self.tests[base_id] = self.loadTestsFor(base_id)
		self.popLogPrefix()

		if self.list_tests:
			self.log("Available tests: ")
			self.pushLogPrefixRaw(self.log_indent)

			sorted_tests = []

			for name in self.tests[testee_id]:
				sorted_tests.append(name)

			sorted_tests.sort()

			for name in sorted_tests:
				self.log(name + ": base=" + self.tests[testee_id][name].getParentTest() + ", tags=" + str(
					self.tests[testee_id][name]._("run")) + ", path=" + str(self.tests[testee_id][name]._("_path")))

			self.popLogPrefix()

			raise SystemExit

		self.executeEvent("onRunPre")

		self.pushLogPrefix("Run/Testee")

		self.runTests(self.tests[testee_id])

		self.popLogPrefix()

		if self.config["mapper_testee"] != self.config["mapper_base"]:
			self.pushLogPrefix("Run/Base")
			self.runTests(self.tests[self.config["mapper_base"]])
			self.popLogPrefix()
		else:
			self.log("Base equals testee, not performing base run", 2)

		self.pushLogPrefix("Evaluate")
		self.evaluateTests(self.tests[testee_id], self.tests[base_id])
		self.popLogPrefix()

		self.logNewline()
		self.logNewline()

		self.pushLogPrefix("Report")

		for test_name in self.tests[testee_id]:
			the_test = self.tests[testee_id][test_name]
			if the_test.getIsBasic() or not the_test.getWasRun():
				continue

			self.log(the_test.getName() + " (base: " + the_test.getParentTest() + ")")

			self.pushLogPrefixRaw(self.log_indent)

			self.tests_err_count = self.tests_err_count + len(the_test.getErrors())
			self.tests_warn_count = self.tests_warn_count + len(the_test.getWarnings())
			the_test.consoleReport()

			self.popLogPrefix()
			self.logNewline()

		self.popLogPrefix()

	def INDEV(self):
		return self.deployment_mode == "devel"

	def getStartTime(self):
		return self.start_time

	def getElapsedTime(self):
		return time.time() - self.start_time

	def main(self):
		no_generate_report = False

		try:
			self.start_time = time.time()
			self.pushLogPrefix("Main")
			self.initFromArgs()

			if not self.config:
				return

			if self.list_mappers:
				self.log("Available mappers: %s" % (", ".join(self.config["mappers"].keys())))
				no_generate_report=True
				return

			if self.list_parameters:
				self.log("Available parameter sets: %s" % (", ".join(self.config["parameters"].keys())) )
				no_generate_report=True
				return

			if self.config["include_tags"] != None and len(self.config["include_tags"]) > 0:
				include_tags_str = str(self.config["include_tags"])
			else:
				include_tags_str = "(Any)"

			if self.config["ignore_tags"] != None and len(self.config["ignore_tags"]) > 0:
				ignore_tags_str = str(self.config["ignore_tags"])
			else:
				ignore_tags_str = "(None)"

			self.framework_hash = self.getVersionHash()
			self.log("framework cmd:  " + " ".join(sys.argv))
			self.log("framework hash: " + self.getCondensedVersionHash())
			self.log("deployment mode: %s (%r)" % (self.deployment_mode, self.INDEV()))

			self.log(self.config["title"] + " - \"" + self.config["description"] + "\"", 2)
			# self.log("-> Run tests including " + include_tags_str + ", excluding " + ignore_tags_str)
			self.logNewline()

			self.initReport()
			self.log_file_handle = open(self.getReportDirectory() + "/teaser.log", "w")

			self.report.generateProgress()

			if "teaser" in self.config:
				self.log("Using Teaser for data set creation")
				from lib import teaser

				self.teaser = teaser.Teaser(self, self.config["teaser"])

				tests_teaser = self.teaser.main()
				if self.run_only == False:
					self.run_only = tests_teaser

				self.log("Data set creation completed")
				self.log("")

			self.executeEvent("onInit")

			if self.is_stats_run:
				self.mainStatsRun()
			else:
				self.mainNormalRun()

		except KeyboardInterrupt:
			self.log("User triggered run abort.")

		except Exception as e:
			self.log_traceback("Except")

		finally:
			if self.config != False and not no_generate_report:
				self.finalize()

	def getWallClockTime(self):
		return time.time() - self.start_time

	def getWallClockTime(self):
		time_sum = 0
		for test in self.getTestList():
			res = test.getRunResults()
			try:
				time_sum += res.maptime
			except:
				pass
		return time_sum

	def finalize(self):
		self.executeEvent("onRunPost")
		self.executeEvent("onReport")

		mate.log("Generate HTML report -> " + self.getReportDirectory() + "...")
		self.report.generate()

		if not self.no_cleanup:
			self.executeEvent("onCleanup")

		self.cleanCache()
		self.logNewline()

		for mapper_id in self.tests:
			self.log("Cleaning for " + mapper_id + "...")
			self.triggerCleanupEvents(self.tests[mapper_id])

		self.log_file_handle.flush()
		self.log_file_handle.close()


print("importing libraries...")

import os
import time
import copy

call_dir = os.getcwd()
root_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(root_dir)

import sys
import pickle
import yaml
import argparse
import hashlib
import traceback
from datetime import datetime
import fnmatch

from lib import test
from lib import util
from lib import report

setCallDir = util.setCallDir
setRootDir = util.setRootDir
enterCallDir = util.enterCallDir
enterRootDir = util.enterRootDir

setCallDir(call_dir)
setRootDir(root_dir)

enterRootDir()

mate = Mate()

if "MATE_DEPLOYMENT_MODE" in os.environ:
	mate.deployment_mode = os.environ["MATE_DEPLOYMENT_MODE"]

mate.main()
