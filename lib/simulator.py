import os
import shutil
import time

import yaml

from lib import util
from lib import gsample
from tools import fastq2sam

class Simulator:
	def __init__(self,dataset,simulator_bin_path,teaser=None):
		if teaser==None:
			self.log=lambda m: None
		else:
			self.log=teaser.log
		self.dataset = dataset
		self.bin_path = simulator_bin_path

	def simulate(self):
		raise NotImplementedError

	def subprogram(self, cmd):
		self.log("subprogram %s" % cmd)
		if os.system(cmd) != 0:
			self.log("Return value != 0 for: %s" % cmd)
			raise RuntimeError("Return value != 0 for: %s" % cmd)

	def enterWorkingDirectory(self):
		self.log("change directory %s" % self.dataset["dir"])
		os.chdir(self.dataset["dir"])

	def mv(self, a, b):
		self.log("move %s -> %s" % (a, b))
		shutil.move(a, b)

	def rm(self, f):
		self.log("remove %s" % f)
		try:
			os.remove(f)
		except:
			self.log("Failed to remove file %s" % f)

class Mason(Simulator):
	def simulate(self):
		self.enterWorkingDirectory()

		params = ""

		if self.dataset["paired"]:
			params += "--mp "
			read_count = int(self.dataset["read_count"]/2)
		else:
			read_count = self.dataset["read_count"]

		if self.dataset["platform"] == "454":
			readlength_param = "--nm"
			params += "--ne " + str(int(self.dataset["read_length"]) / 10)
		else:
			readlength_param = "-n"

		if self.dataset["error_rate_mult"] != 1:
			if self.dataset["platform"] == "illumina":
				params += " --pmm %f --pi %f --pd %f " % (
					0.004 * self.dataset["error_rate_mult"], 0.001 * self.dataset["error_rate_mult"], 0.001 * self.dataset["error_rate_mult"])
			elif self.dataset["platform"] == "454":
				params += " --bm %f " % (0.23 * self.dataset["error_rate_mult"])

		if self.dataset["insert_size"] != None:
			params += " --ll %d --le %d " % (self.dataset["insert_size"], self.dataset["insert_size_error"])

		params += " --hi %f " % self.dataset["mutation_indel_rate"]
		params += " --hs %f " % self.dataset["mutation_snp_rate"]
		params += " --hm %d --hM %d" % (1, (1 + self.dataset["mutation_indel_avg_len"]) * 2)

		self.dataset["simulator_cmd"] = self.bin_path + " " + str(self.dataset["platform"]) + " --read-name-prefix read --sq " + str(readlength_param) + " " + str(self.dataset["read_length"]) + " -N " + str(read_count) + " " + str(params) + " " + str(self.dataset["extra_params"]) + " " + str(self.dataset["reference_sim"])
		self.log("\tSimulator cmd: %s" % self.dataset["simulator_cmd"])

		self.subprogram(self.dataset["simulator_cmd"])

		if not self.dataset["paired"]:
			self.mv(self.dataset["reference_sim"] + ".fastq", "./reads.fastq")
		else:
			self.mv(self.dataset["reference_sim"] + "_1.fastq", "./reads1.fastq")
			self.mv(self.dataset["reference_sim"] + "_2.fastq", "./reads2.fastq")
		self.mv(self.dataset["reference_sim"] + ".fastq.sam", "./mapping_comparison.sam")

class Dwgsim(Simulator):
	def simulate(self):
		self.enterWorkingDirectory()

		platform_ids = {"illumina":0,"ion_torrent":2}
		params = ""

		if self.dataset["platform"] == "ion_torrent":
			params += " -f TACGTACGTCTGAGCATCGATCGATGTACAGC "

		read_length_1 = str(self.dataset["read_length"])
		if self.dataset["paired"]:
			read_length_2 = read_length_1
			read_2_fastq2sam = " dwgout.bwa.read2.fastq"
			read_count = int(self.dataset["read_count"]/2)
		else:
			read_length_2 = "0"
			read_2_fastq2sam = ""
			read_count = self.dataset["read_count"]

		if self.dataset["insert_size"] != None:
			params += " -d %d -s %d " % (self.dataset["insert_size"],self.dataset["insert_size_error"])

		if self.dataset["error_rate_mult"] != 1:
			self.dataset["extra_params"] += " -e %f " % (self.dataset["error_rate_mult"] * 0.02)

		params += " -r %f " % self.dataset["mutation_rate"]
		params += " -R %f " % self.dataset["mutation_indel_frac"]

		self.dataset["simulator_cmd"] = self.bin_path + " -c " + str(platform_ids[self.dataset["platform"]]) + " -1 " + read_length_1 + " -2 " + read_length_2 + " -N " + str(read_count) + params + " -y 0 " + self.dataset["extra_params"] + " " + self.dataset["reference_sim"] + " dwgout"
		self.subprogram(self.dataset["simulator_cmd"])

		aligner = fastq2sam.dwgsim()
		conv = fastq2sam.Converter(aligner, "dwgout.bwa.read1.fastq.sam")

		if self.dataset["paired"]:
			conv.align_pe("dwgout.bwa.read1.fastq", "dwgout.bwa.read2.fastq")
			self.mv("enc_dwgout.bwa.read1.fastq", "reads1.fastq")
			self.mv("enc_dwgout.bwa.read2.fastq", "reads2.fastq")
		else:
			conv.align_se("dwgout.bwa.read1.fastq")
			self.mv("enc_dwgout.bwa.read1.fastq", "reads.fastq")

		self.mv("enc_dwgout.bwa.read1.fastq.sam", "mapping_comparison.sam")
		self.rm("dwgout.bwa.read1.fastq.sam")
		self.rm("dwgout.mutations.txt")
		self.rm("dwgout.mutations.vcf")
		self.rm("dwgout.bfast.fastq")
		self.rm("dwgout.bwa.read1.fastq")
		self.rm("dwgout.bwa.read2.fastq")
