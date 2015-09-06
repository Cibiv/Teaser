import math
import os
import yaml

from lib import util


def map(self):
	self.enterWorkingDirectory()

	mapper = self.getMapper()
	mapper.onMapPre()

	try:
		reads_size = 0
		for readfile in self._("input:reads"):
			reads_size = reads_size + os.path.getsize(readfile)
	except:
		self.error("Error accessing read / reference input files for size - do they exist / are accessible?",
				   str(self._("input:reads")), None)
		raise SystemExit

	if os.path.isfile(self._("output:testee_path")):
		self.error("Output file existed before mapper run", self._("output:testee_path"))
		raise SystemExit

	if os.path.isfile(self._("output:sorted_testee_path")):
		self.error("Output file existed before mapper run", self._("output:sorted_testee_path"))
		raise SystemExit

	cmd_pre = mapper.getCommandLinePre()
	self.dbg("Command(pre): " + cmd_pre)

	self.sub(cmd_pre)

	mapper_path = list(self.getMapper().getBinaryPath())[0]
	base_runtime_file = self.mate.getCachePathPrefix() + util.md5(mapper_path + self._("input:reference")) + "_initt.yaml"
	self.restoreWorkingDirectory()

	#if not os.path.exists(base_runtime_file) or (
	#			self.mate.force_run and not base_runtime_file in self.mate.computed_runtime_files):
	if True:
		self.mate.computed_runtime_files.append(base_runtime_file)

		self.dbg("Base run time file not existing, performing base run")

		self.enterWorkingDirectory()

		dummy_fastq_name = "reads_base.fastq"

		dummy_fastq = open(dummy_fastq_name, "w")
		dummy_fastq.write(
			"@read1\nGATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT\n+\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
		dummy_fastq.close()

		mapper.resetParams()
		mapper.setInReferenceFile(self._("input:reference"))
		mapper.setInReadFiles([dummy_fastq_name])
		mapper.setInPaired(False)
		mapper.setOutMappingFile(self._("output:testee_path"))

		cmd = mapper.getCommandLineMain()
		self.dbg("Command(pre-b): " + cmd)

		if self.mate.measure_preload:
			self.mate.clearFilesystemCache()
			result_pre = self.sub(cmd,"",True)

		result = self.sub(cmd,"",True)

		mapper.resetParams()
		mapper.setInReferenceFile(self._("input:reference"))
		mapper.setInReadFiles(self._("input:reads"))
		mapper.setInPaired(self._("input:reads_paired_end"))
		mapper.setOutMappingFile(self._("output:testee_path"))
		mapper.addParams(self._("params"))

		os.remove(dummy_fastq_name)
		self.restoreWorkingDirectory()

		with open(base_runtime_file, "w") as f:
			init_time={}
			init_time["time"]=result["time"]
			init_time["usrtime"]=result["usrtime"]
			init_time["systime"]=result["systime"]
			init_time["cputime"]=result["usrtime"]+result["systime"]
			f.write(yaml.dump(init_time))

		self.enterWorkingDirectory()
		try:
			os.remove(self._("output:testee_path"))
		except:
			pass

	with open(base_runtime_file, "r") as f:
		self.setc("output:mapper_init_time", yaml.load(f.read()))

	self.enterWorkingDirectory()

	cmd = mapper.getCommandLineMain()
	self.dbg("Command(main): " + cmd)

	self.dbg("   Mapping " + util.formatFilesize(reads_size) + " to " + util.formatFilesize(os.path.getsize(
		self._("input:reference"))) + " with " + mapper.getName() + "...")  # + " to " + sam_ngm_path + "..."
	self.mate.clearFilesystemCache()
	mapper_result = self.sub(cmd, "", True)
	self.setc("output:mapper_result", mapper_result)

	self.dbg("   Took %.3f (wall), %.3f (CPU) seconds, initialization time: %.3f (wall), %.3f (CPU) seconds." % (mapper_result["time"], mapper_result["usrtime"]+mapper_result["systime"], init_time["time"], init_time["usrtime"]+init_time["systime"]))

	cmd_post = mapper.getCommandLinePost()
	self.dbg("Command(post): " + cmd_post)

	self.sub(cmd_post)

	if not os.path.isfile(self._("output:testee_path")):
		self.error("Output file not found after mapper run", self._("output:testee_path"))
		raise SystemExit

	self.enterWorkingDirectory()
	mapper.onMapPost()
