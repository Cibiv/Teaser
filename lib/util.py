import copy
import os
import hashlib
import glob
import yaml
import time
import sys
import subprocess
import resource
from multiprocessing import Process
from multiprocessing import Queue

call_cwd = ""
root_cwd = ""

STATUS_NORMAL=1
STATUS_MAX_MEMORY_EXCEEDED=2
STATUS_MAX_RUNTIME_EXCEEDED=3

MAX_LEN_OUT = 10000

def runAndMeasure(command,detailed=True,maxtime=0,maxmem=0):
	if not detailed:
		return runSimple(command)

	return_queue = Queue()
	runner=Process(target=runAndMeasureInternal, args=(return_queue,command,maxtime,maxmem))
	runner.start()
	result = return_queue.get()
	runner.join()

	if result["stdout"] != None:
		result["stdout"] = result["stdout"][:MAX_LEN_OUT]

	if result["stderr"] != None:
		result["stderr"] = result["stderr"][:MAX_LEN_OUT]

	return result

def runSimple(command):
	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,close_fds=True)
	start_time = time.time()
	out, err = process.communicate()
	end_time = time.time()

	result = {}
	result["command"] = command
	result["working_directory"] = os.getcwd()
	result["status"]=STATUS_NORMAL

	result["stdout"] = out
	result["stderr"] = err
	result["return"] = 1
	result["time"] = end_time-start_time
	result["usrtime"] = 0
	result["systime"] = 0

	return result

def runAndMeasureInternal(return_queue,command,maxtime=0,maxmem=0):
	control_queue = Queue()
	process = Process(target=runInternal,args=(control_queue,command,maxmem))
	process.start()

	start_time = time.time()

	result = {}
	result["command"] = command
	result["working_directory"] = os.getcwd()
	result["status"]=STATUS_NORMAL

	result["stdout"] = ""
	result["stderr"] = ""
	result["return"] = 1
	result["time"] = 0
	result["usrtime"] = 0
	result["systime"] = 0

	while control_queue.empty():
		res_curr = resource.getrusage(resource.RUSAGE_CHILDREN)
		if maxmem != 0 and res_curr.ru_maxrss/1000 > maxmem:
			result["status"]=STATUS_MAX_MEMORY_EXCEEDED

			try:
				process.terminate()
			except:
				pass

			return_queue.put(result)
			sys.exit(1)
			return 1

		if maxtime != 0 and time.time()-start_time > maxtime:
			result["status"]=STATUS_MAX_RUNTIME_EXCEEDED

			try:
				process.terminate()
			except:
				pass

			return_queue.put(result)
			sys.exit(1)
			return 1

		time.sleep(1)

	process_result = control_queue.get()

	result["stdout"] = process_result["stdout"]
	result["stderr"] = process_result["stderr"]
	result["return"] = process_result["return"]

	result["time"] = process_result["time"]
	result["memory"] = process_result["memory"]
	result["usrtime"] = process_result["usrtime"]
	result["systime"] = process_result["systime"]

	return_queue.put(result)
	sys.exit(0)

def runInternal(control_queue,command,max_memory):
	result={}

	if max_memory != 0:
		ulimit_command = "ulimit -v %d; "%(max_memory*1000)
	else:
		ulimit_command = ""

	process = subprocess.Popen(ulimit_command + command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)

	res_start = resource.getrusage(resource.RUSAGE_CHILDREN)
	start_time = time.time()
	out, err = process.communicate()
	end_time = time.time()
	res_end = resource.getrusage(resource.RUSAGE_CHILDREN)

	result["time"] = end_time-start_time
	result["usrtime"] = res_end.ru_utime-res_start.ru_utime
	result["systime"] = res_end.ru_stime-res_start.ru_stime
	result["memory"] = res_end.ru_maxrss * 1000

	result["stdout"] = out
	result["stderr"] = err
	result["return"] = process.returncode

	control_queue.put(result)
	sys.exit(0)

def measureProcess(queue, initial_pids, command, measurement_interval=1, max_runtime=0, max_memory=0, debug=False):
	import psutil

	if debug:
		print("[MEASUREMENT] Finding and attaching to target...")
	targets = []

	for pid in initial_pids:
		try:
			targets.append(psutil.Process(pid))
		except Exception as e:
			# print("Measurement Exception: ",e)
			pass

	def extendTargets(targets, proc):
		for p in targets:
			if p.pid == proc.pid:
				return
		targets.append(proc)

	def killTargets(targets):
		for p in targets:
			try:
				p.kill()
			except:
				pass

	def updateTargets(targets, metrics):
		for proc in psutil.process_iter():
			try:
				if command in proc.cmdline() or proc.pid in initial_pids:
					extendTargets(targets, proc)
			except Exception as e:
				# print("Measurement Exception: ",e)
				pass

		targets_append = []
		for target in targets:
			try:
				children = target.get_children(recursive=True)
				for proc in children:
					targets_append.append(proc)
			except Exception as e:
				# print("Measurement Exception: ",e)
				pass

		for target in targets_append:
			extendTargets(targets, target)

		for target in targets:
			if not target.pid in metrics:
				metrics[target.pid] = {"usrtime": 0, "systime": 0, "memory": 0}

	def updateMetrics(target, metrics):
		try:
			usrtime, systime = target.get_cpu_times()
			rss, vms = target.memory_info()
			metrics[target.pid]["usrtime"] = usrtime
			metrics[target.pid]["systime"] = systime
			metrics[target.pid]["memory"] = max(metrics[target.pid]["memory"], rss)
			return metrics[target.pid]["memory"]

		except Exception as e:
			return 0

	metrics = {}
	output_trackcount = -1
	peak_memory_sum = 0
	updateTargets(targets, metrics)

	start_time = time.time()

	while queue.empty():
		if len(targets) != output_trackcount:
			process_names = []
			for t in targets:
				try:
					process_names.append(t.name())
				except:
					targets.remove(t)
			if debug:
				print("[MEASUREMENT] Tracking %d processes: %s" % (len(targets), str(process_names)))
			output_trackcount = len(targets)

		memory_sum = 0
		for target in targets:
			memory_sum += updateMetrics(target, metrics)

		if int(memory_sum / 1000000) > int(peak_memory_sum / 1000000) and debug and max_memory != 0 and max_runtime != 0:
			print("[MEASUREMENT] Peak RSS: %dMB (%.3f%% of max), Runtime: %ds (%.3f%% of max)" % (
			memory_sum / 1000000, memory_sum / (10000.0 * max_memory), time.time() - start_time,
			(time.time() - start_time) / float(max_runtime)))

		peak_memory_sum = max(peak_memory_sum, memory_sum)
		updateTargets(targets, metrics)

		if memory_sum / 1000000 > max_memory and max_memory != 0:
			print("Memory usage too high, killing subprocess")
			killTargets(targets)
			queue.get()
			queue.put(STATUS_MAX_MEMORY_EXCEEDED)
			queue.put(metrics)
			queue.put(peak_memory_sum)
			sys.exit(0)

		if time.time() - start_time > max_runtime and max_runtime != 0:
			print("Runtime too long, killing subprocess")
			killTargets(targets)
			queue.get()
			queue.put(STATUS_MAX_RUNTIME_EXCEEDED)
			queue.put(metrics)
			queue.put(peak_memory_sum)
			sys.exit(0)

		time.sleep(measurement_interval)

	if debug:
		print("[MEASUREMENT] Stopping measurement")

	queue.get()
	queue.put(STATUS_NORMAL)
	queue.put(metrics)
	queue.put(peak_memory_sum)
	sys.exit(0)

def loadConfig(name, parent_dir="", already_included=[]):
	config_attempts = ["%s", "%s.yaml", "setups/%s", "setups/%s.yaml"]
	config_filenames = [s % name for s in config_attempts]

	if parent_dir != "":
		parent_path_filenames = []
		for f in config_filenames:
			parent_path_filenames.append(parent_dir + "/" + f)

		for k in config_filenames:
			parent_path_filenames.append(k)

		config_filenames = parent_path_filenames

	config_handle = False
	config_filename = ""

	for filename in config_filenames:
		enterCallDir()
		try:
			config_handle = open(filename, "r")
			config_filename = filename
			config_abs = os.path.abspath(filename)
			config_dir = os.path.dirname(os.path.abspath(filename))
		except Exception as e:
			pass

		enterRootDir()
		try:
			config_handle = open(filename, "r")
			config_filename = filename
			config_abs = os.path.abspath(filename)
			config_dir = os.path.dirname(os.path.abspath(filename))
			break
		except Exception as e:
			pass

	enterRootDir()

	if not config_handle:
		return False, False

	if config_abs in already_included:
		return False, False

	already_included.append(config_abs)
	config = yaml.load(config_handle.read())

	original = copy.deepcopy(config)

	if config == False:
		return False, False

	print("Loaded configuration %s" % config_abs)

	if "include" in config:
		for inc in config["include"]:
			success = False
			inc_files = [inc]
			for attempt in config_attempts:
				inc_files.extend(glob.glob(attempt % inc))

			for inc in inc_files:
				base, original_inc = loadConfig(inc, config_dir, already_included)

				if base != False and base != None:
					config = merge(base, config)
					success = True

			if not success:
				print("Failed to include or match any files for %s" % inc)

	return config, original

def setCallDir(d):
	global call_cwd
	call_cwd = d

def setRootDir(d):
	global root_cwd
	root_cwd = d

def enterCallDir():
	os.chdir(call_cwd)

def enterRootDir():
	os.chdir(root_cwd)

def getRootDir():
	return root_cwd

def nl2br(text):
	return text.replace('\n', '<br>\n')

def msg(text="", level=1):
	print(text)

def yes_no(b):
	if bool(b):
		return "Yes"
	else:
		return "No"

def md5(text):
	return hashlib.md5(text).hexdigest()

def merge(x, y):
	merged = copy.deepcopy(x)
	mergee = copy.deepcopy(y)

	for k in mergee:
		if isinstance(mergee[k], dict):
			if k in merged:
				merged[k] = merge(merged[k], mergee[k])
			else:
				merged[k] = copy.deepcopy(mergee[k])
		elif isinstance(mergee[k], list):
			if k in merged:
				# Overwrite lists
				# listcopy = copy.deepcopy(mergee[k])
				# for listitem in listcopy:
				#    merged[k].append(listitem)
				merged[k] = copy.deepcopy(mergee[k])

			else:
				merged[k] = copy.deepcopy(mergee[k])
		else:
			merged[k] = copy.deepcopy(mergee[k])

	return merged

def formatFilesize(n):
	return "%.2fMB"%(n/1000000)

def percent(val, base, offset=0):
	if offset == 100:
		plus = "+"
	else:
		plus = ""

	if base == 0:
		base = 1
		val = 0
		offset = 0

	pval = round((float(val) / float(base)) * 100 - offset, 3)
	if pval > 0:
		pval = plus + str(pval)
	elif (float(val) / float(base)) == 0 and plus == "+":
		pval = "+-" + str(pval)

	return str(pval) + "%"

def abs_path(path):
	if len(path) == 0:
		return ""

	if path[0] != "/":
		return os.getcwd() + "/" + path
	else:
		return path

def get_sam_header_line_count(filename):
	len=0
	with open(filename,"r") as handle:
		line=handle.readline()
		while line!="" and (line[0]=="@" or line.strip()==""):
			len+=1
			line=handle.readline()
	return len

def is_sam_sorted(filename):
	if get_sam_header_line_count(filename) > 1:
		return False

	with open(filename,"r") as handle:
		line=handle.readline()
		while line!="" and (line[0]=="@" or line.strip()==""):
			if line[0:3]=="@HD" and "SO:queryname" in line:
				return True
			line=handle.readline()
		return False

def sort_sam(filename,threads=1):
	sorted_filename = "sorted_%s"%filename
	with open(sorted_filename,"w") as handle:
		handle.write("@HD SO:queryname\n")
		handle.flush()
		handle.close()
	#cmd="tail --lines=+%d %s | sort --parallel %d --buffer-size 25%% -t $'\\t' -k1 >> %s" % (get_sam_header_line_count(filename) + 1,filename,threads,sorted_filename)
	cmd="""/bin/bash -c "tail --lines=+%d %s | sort -t$'\t' -k1 >> %s" """ % (get_sam_header_line_count(filename) + 1,filename,sorted_filename)
	exitcode = os.system(cmd)
	return sorted_filename if exitcode==0 else False

def sort_sam_picard(filename,threads=-1):
	sorted_filename = "sorted_%s"%filename
	cmd="picard-tools SortSam INPUT=%s OUTPUT=%s VALIDATION_STRINGENCY=SILENT SO=queryname" % (filename,sorted_filename)
	exitcode = os.system(cmd)
	return sorted_filename if exitcode==0 else False

def line_count(filename):
	process = subprocess.Popen(['wc', '-l', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	result,errors=process.communicate()
	if process.returncode != 0:
		return -1
	return int(result.strip().split()[0])

def sanitize_string(s):
	remove_chars = "\\/*&^%$#@!<>{}[]'\""
	for r in remove_chars:
		s=s.replace(r,"")
	return s

def makeExportDropdown(plot_id,csv_filename):
	item_plot = """<li><a href="javascript:exportSVG('%s');">Plot (.svg)</a></li>""" % plot_id if plot_id != "" else ""
	item_csv = """<li><a href="%s">Raw Data  (.csv)</a></li>""" % csv_filename if csv_filename != "" else ""

	return """<div align="right" style="margin-top:5px;"><div class="dropdown">
  <button class="btn btn-default btn-xs dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
    <span class="glyphicon glyphicon-download-alt" aria-hidden="true"> Export
    <span class="caret"></span>
  </button>
  <ul class="dropdown-menu dropdown-menu-right" aria-labelledby="dropdownMenu1">
    %s
    %s
  </ul>
</div></div>""" % (item_plot,item_csv)

import pydoc
locate = pydoc.locate
