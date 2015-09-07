#!/usr/bin/env python
import os
import shutil
import time
import yaml
import util
import simulator

from lib import gsample
from tools import fastq2sam
from lib import sam


class Teaser:
	def __init__(self, mate, config):
		self.mate = mate
		self.config = config

		self.supported_platforms = ["illumina","454","ion_torrent"]

		self.tests = self.config["tests"]

		self.default_test = {}
		self.default_test["title"] = None
		self.default_test["order"] = None
		self.default_test["type"] = "simulated_teaser"

		self.default_test["sampling"] = {}
		self.default_test["sampling"]["enable"] = True
		self.default_test["sampling"]["ratio"] = None
		self.default_test["sampling"]["region_len_multiplier"] = 10
		self.default_test["sampling"]["region_len"] = None
		self.default_test["sampling"]["region_pad"] = None

		self.default_test["simulator"] = None
		self.default_test["reference"] = None
		self.default_test["platform"] = "illumina"

		self.default_test["read_length"] = 100
		self.default_test["read_count"] = None
		self.default_test["paired"] = False
		self.default_test["insert_size"] = 500
		self.default_test["coverage"] = 1
		self.default_test["mutation_rate"] = 0.001
		self.default_test["mutation_indel_frac"] = 0.3
		self.default_test["mutation_indel_avg_len"] = 1
		self.default_test["error_rate_mult"] = 1
		self.default_test["extra_params"] = ""
		self.default_test["simulator_cmd"] = ""

		self.default_test["import_read_files"] = None
		self.default_test["import_gold_standard_file"] = None

		self.created_count = 0

		gsample.log = lambda msg: self.log(msg)

	def log(self, msg):
		self.mate.log(msg)

	def preprocessTests(self):
		for name in self.tests:
			self.tests[name] = util.merge(self.default_test, self.tests[name])

		for name in self.tests:
			test = self.tests[name]
			if "base" in test:
				print("Derive %s from %s" % (name, test["base"]))
				self.tests[name] = util.merge(self.tests[self.tests[name]["base"]], self.tests[name])
				print(self.tests[self.tests[name]["base"]])

			if test["reference"] == None:
				raise RuntimeError("Reference genome path must be defined for data set")

			if not os.path.exists(test["reference"]):
				if os.path.exists(self.config["reference_directory"] + "/" + test["reference"]):
					test["reference"] = os.path.abspath(self.config["reference_directory"] + "/" + test["reference"])
			else:
				test["reference"] = os.path.abspath(test["reference"])

			if not os.path.exists(test["reference"]):
				raise RuntimeError("Reference '%s' not found for test '%s'"%(test["reference"],name))

			if test["title"] == None:
				test["title"] = name

			if test["order"] == None:
				test["order"] = name

			if test["simulator"] == None:
				if test["platform"] == "ion_torrent":
					test["simulator"] = "dwgsim"
				else:
					test["simulator"] = "mason"

			test["name"] = name
			test["dir"] = os.path.abspath(self.config["test_directory"] + "/" + name)

	def existsTest(self, test):
		if not os.path.exists(test["dir"]):
			return False

		if not os.path.exists(test["dir"] + "/" + test["name"] + ".yaml"):
			return False

		if not os.path.exists(test["dir"] + "/reads.fastq") and not (os.path.exists(test["dir"] + "/reads1.fastq") and os.path.exists(test["dir"] + "/reads2.fastq")):
			return False

		return True

	def createTest(self, test):
		start_time = time.time()
		self.mate.getReport().generateProgress()

		self.log("\nCreating test %s" % test["name"])
		try:
			os.mkdir(test["dir"])
		except:
			self.log("Failed to create test directory, probably existing")

			self.rm(test["dir"] + "/" + test["name"] + ".yaml")
			self.rm(test["dir"] + "/mapping_comparison.sam")
			self.rm(test["dir"] + "/reads.fastq")
			self.rm(test["dir"] + "/reads1.fastq")
			self.rm(test["dir"] + "/reads2.fastq")

		self.ch(test)

		try:
			if test["type"] == "simulated_teaser":
				if test["sampling"]["enable"]:
					self.makeDatasetDS(test)
				else:
					self.makeDatasetNoDS(test)
			elif test["type"] == "simulated_custom" or test["type"] == "real":
				self.makeDatasetNoSim(test)

			else:
				self.mate.error("Teaser: Unknown test type '%s' for test '%s'."%(test["type"],test["name"]))
				raise
		except RuntimeError as e:
			self.mate.error("Teaser: Test creation failed for '%s': %s"%(test["name"],str(e)))
			raise SystemExit

		except Exception as e:
			self.mate.error("Teaser: Test creation failed for '%s' due to an exception: %s"%(test["name"],str(e)))
			self.mate.log_traceback("Teaser Error")
			raise SystemExit

		end_time = time.time()
		test["create_time"] = end_time - start_time
		self.log("Took %d seconds for generating %s" % (test["create_time"], test["name"]))
		self.writeYAML(test)
		util.enterRootDir()
		self.created_count += 1

		self.mate.getReport().generateProgress()

	def getTestCount(self):
		return len(self.tests)

	def getTestCreatedCount(self):
		return self.created_count

	def writeYAML(self, test):
		config = {}

		if test["type"] == "simulated_teaser" or test["type"] == "simulated_custom":
			config["base"] = "tests_base/base_mapping"
		elif test["type"] == "real":
			config["base"] = "tests_base/base_mapping_real"
		else:
			self.mate.error("Teaser: Tried to create test of unsupported type '%s': %s"%(test["name"],str(test["type"])))
			return False

		config["title"] = test["title"]
		config["tags"] = ["teaser"]

		if test["type"] == "simulated_teaser":
			config["input_info"] = {"type":test["type"],"simulator": str(test["simulator_cmd"]), "platform": str(test["platform"]),
								"read_length": str(test["read_length"]), "read_count": str(test["read_count"]),
								"insert_size": str(test["insert_size"]), "sampling": test["sampling"]["enable"],
								"sampling_ratio": str(test["sampling"]["ratio"]),
								"sampling_region_len": str(test["sampling"]["region_len"]),
								"divergence": "%.4f overall mutation rate, %.4f indel fraction, %.4f indel average length" % (test["mutation_rate"],test["mutation_indel_frac"],test["mutation_indel_avg_len"])  }
		else:
			config["input_info"] = {"type": test["type"],"read_count": test["read_count"]}


		config["input"] = {"reference": test["reference"], "reads_paired_end": test["paired"]}

		if test["paired"]:
			config["input"]["reads"] = ["reads1.fastq", "reads2.fastq"]
		else:
			config["input"]["reads"] = ["reads.fastq"]

		config["mapping_comparison"] = "mapping_comparison.sam"
		config["create_time"] = test["create_time"]

		with open(test["dir"] + "/" + test["name"] + ".yaml", "w") as yml:
			yml.write(yaml.dump(config))
			yml.flush()
			yml.close()

	def calculateSamplingRatio(self,contig_len):
		ratio = 0.01
		if contig_len <= 1000 * 1000 * 500:
			ratio = 0.25

		if contig_len <= 1000 * 1000 * 100:
			ratio = 0.5

		return ratio

	def calcualteRegionLen(self,test):
		if test["paired"]:
			return test["sampling"]["region_len_multiplier"] * test["insert_size"]
		else:
			return test["sampling"]["region_len_multiplier"] * test["read_length"]

	def calculateRegionPadding(self,test):
		if test["paired"]:
			return 2 * test["insert_size"]
		else:
			return 2 * test["read_length"]		

	def makeDatasetDS(self, test):
		self.ch(test)

		idx = gsample.index(test["reference"])

		if test["sampling"]["region_len"] == None:
			test["sampling"]["region_len"] = self.calcualteRegionLen(test)

		if test["sampling"]["region_pad"] == None:
			test["sampling"]["region_pad"] = self.calculateRegionPadding(test)

		if test["sampling"]["ratio"] == None:
			test["sampling"]["ratio"] = self.calculateSamplingRatio(idx["contig_len"])

		sampled_file,sampled_index_file=gsample.csample(test["reference"], test["sampling"]["region_len"], test["sampling"]["ratio"],
						test["sampling"]["region_pad"])
		
		test["reference_sim"] = sampled_file

		if "coverage" in test and test["read_count"] == None:
			test["read_count"] = int(
				((idx["contig_len"] * test["sampling"]["ratio"]) / test["read_length"]) * test["coverage"])

			test["read_count"] = max(test["read_count"],150000)

		self.simulate(test)

		self.ch(test)
		self.mv("mapping_comparison.sam", "mapping_comparison_unfixed.sam")
		gsample.ctranslate(test["reference"], sampled_index_file, "mapping_comparison_unfixed.sam", "mapping_comparison.sam")

		self.rm(sampled_file)
		self.rm(sampled_index_file)
		self.rm("mapping_comparison_unfixed.sam")

	def makeDatasetNoDS(self, test):
		if test["read_count"] == None:
			index = gsample.index(test["reference"])
			test["read_count"] = index["contig_len"] / test["read_length"]
			#self.mate.error("Teaser: Read count must be set manually when subsampling is disabled, for test '%s'"%test["name"])
			#raise RuntimeError

		test["reference_sim"] = test["reference"]
		self.ch(test)
		self.simulate(test)

	def isFastq(self,filename):
		name,ext=os.path.splitext(filename)
		return ext.lower() in [".fq",".fastq"]

	def makeDatasetNoSim(self,test):
		util.enterRootDir()

		if test["import_read_files"] == None or len(test["import_read_files"])==0:
			self.mate.error("Teaser: No read files given to import for test '%s'"%test["name"])
			test["type"]=None
			raise RuntimeError

		if test["paired"]:
			if len(test["import_read_files"]) != 2:
				self.mate.error("Teaser: Expected 2 files in field 'import_read_files' for paired-end test '%s', got %d"%(test["name"],len(test["import_read_files"])))
				raise RuntimeError
		else:
			if len(test["import_read_files"]) != 1:
				self.mate.error("Teaser: Expected 1 file in field 'import_read_files' for paired-end test '%s', got %d"%(test["name"],len(test["import_read_files"])))
				raise RuntimeError

		for filename in test["import_read_files"]:
			if not self.isFastq(filename):
				self.mate.error("Teaser: Unsupported read file type of '%s' for test '%s'. Expected FASTQ." % (filename,test["name"]) )
				raise RuntimeError

		if test["type"] == "simulated_custom":
			self.importDatasetCustom(test)
		elif test["type"] == "real":
			self.importDatasetReal(test)

		self.ch(test)

	def importDatasetCustom(self,test):
		self.cp(test["import_gold_standard_file"],test["dir"]+"/mapping_comparison.sam")
		test["read_count"] = self.importReadFiles(test)
		self.log("Data set import successful")

	def importReadFiles(self,test):
		if len(test["import_read_files"]) > 1:
			i=1
			for f in test["import_read_files"]:
				self.cp(f,test["dir"]+("/reads%d.fastq"%i) )
				if i==1:
					line_count = util.line_count(f)
				i+=1
		else:
			self.cp(test["import_read_files"][0],test["dir"]+("/reads.fastq"))
			line_count = util.line_count(test["import_read_files"][0])

		return (line_count - line_count%4)/4

	def importDatasetReal(self,test):
		if test["sampling"]["enable"] == False:
			self.log("Subsampling disabled; Importing all reads")
			test["read_count"] = self.importReadFiles(test)
			self.log("Data set import successful")
			return

		if test["read_count"] == None:
			self.log("No target read count given for real data test, estimating using reference and avg. read length")

			fastq=sam.FASTQ(test["import_read_files"][0])
			i=0
			read=fastq.next_read()
			length_sum=0
			while read.valid and i < 10000:
				length_sum+=len(read.seq)
				i+=1
				read=fastq.next_read()
			avg_len = length_sum/i
			contig_len = gsample.index(test["reference"])["contig_len"]

			if test["sampling"]["ratio"] == None:
				sampling_ratio = self.calculateSamplingRatio(contig_len)
			else:
				sampling_ratio = test["sampling"]["ratio"]

			test["read_count"] = (contig_len/avg_len) * sampling_ratio * test["coverage"]
			self.log("Reference length: %d, Sampling Ratio: %f, Estimated avg. read length: %d"%(contig_len,sampling_ratio,avg_len))

		self.log("Sampling %d reads."%test["read_count"])
		if test["paired"]:
			test["read_count"] /= 2

		line_counts = []
		for file in test["import_read_files"]:
			count = util.line_count(file)
			if count == -1:
				self.mate.error("Teaser: Real data import: Failed to get line count for '%s' during data set import."%file)
				raise RuntimeError
			line_counts.append(count)

		for c in line_counts:
			if c != line_counts[0]:
				self.mate.error("Teaser: Real data import: FASTQ files to import have different line counts")
				raise RuntimeError

		line_count = line_counts[0]
		if line_count % 4 != 0:
			self.mate.error("Teaser: Real data import: FASTQ file line count is not a multiple of four. This may lead to errors.")

		line_count -= line_count % 4
		import_files_readcount = line_counts[0] / 4
		if import_files_readcount < test["read_count"]:
			self.mate.warning("Teaser: Real data import: Tried to sample more reads than present in FASTQ files. Using all input instead.")
			test["read_count"] = import_files_readcount

		sample_fraction = float(test["read_count"])/import_files_readcount

		if test["paired"]:
			self.sampleFastq(test["import_read_files"][0],test["dir"]+"/reads1.fastq",sample_fraction)
			test["read_count"] = self.sampleFastq(test["import_read_files"][1],test["dir"]+"/reads2.fastq",sample_fraction)
		else:
			test["read_count"] = self.sampleFastq(test["import_read_files"][0],test["dir"]+"/reads.fastq",sample_fraction)

		self.log("Data set import successful")

	def sampleFastq(self,input,output,sample_fraction=1.0):
		input=sam.FASTQ(input)
		output=sam.FASTQ(output,True)
		to_sample = 0
		sampled_count = 0
		read = input.next_read()
		while read.valid:
			if to_sample > 1:
				while to_sample > 1:
					to_sample -= 1
					output.write_read(read)
					sampled_count += 1
					read = input.next_read()
			else:
				to_sample += sample_fraction
				read = input.next_read()

		input.close()
		output.close()

		return sampled_count

	def simulate(self, test):
		if test["mutation_indel_frac"] <= 0:
			test["mutation_snp_frac"] = 1
		else:
			test["mutation_snp_frac"] = 1.0 - test["mutation_indel_frac"]

		test["mutation_indel_rate"] = test["mutation_rate"] * test["mutation_indel_frac"]
		test["mutation_snp_rate"] = test["mutation_rate"] * test["mutation_snp_frac"]

		if not test["platform"] in self.supported_platforms:
			raise RuntimeError("Not implemented")

		if test["simulator"] == "mason":
			sim=simulator.Mason(test,self.config["mason_path"],self)
		elif test["simulator"] == "dwgsim":
			sim=simulator.Dwgsim(test,self.config["dwgsim_path"],self)
		else:
			raise RuntimeError("Not implemented")

		sim.simulate()

	def subprogram(self, cmd):
		self.log("subprogram %s" % cmd)
		if os.system(cmd) != 0:
			self.log("Return value != 0 for: %s" % cmd)
			raise RuntimeError("Return value != 0 for: %s" % cmd)

	def ch(self, test):
		self.log("change directory %s" % test["dir"])
		os.chdir(test["dir"])

	def mv(self, a, b):
		self.log("move %s -> %s" % (a, b))
		shutil.move(a, b)

	def rm(self, f):
		self.log("remove %s" % f)
		try:
			os.remove(f)
		except:
			#self.log("Failed to remove file %s" % f)
			pass

	def cp(self, a, b):
		self.log("copy %s -> %s" % (a, b))
		shutil.copy(a, b)

	def main(self):
		self.mate.pushLogPrefix("Teaser")
		self.log("Init. Creating %d test datasets." % len(self.tests))

		try:
			self.preprocessTests()
		except RuntimeError as e:
			self.mate.error("Teaser: " + str(e))
			raise SystemExit

		force_recreate = self.mate.force_gen

		for name in sorted(self.tests, key=lambda k: self.tests[k]["order"]):
			if self.mate.run_only != False:
				if name not in self.mate.run_only:
					self.created_count += 1
					self.log("Data set %s is excluded, not creating." % name)
					continue

			if self.existsTest(self.tests[name]) and not force_recreate:
				self.mate.getReport().generateProgress()
				self.created_count += 1
				self.log("Data set %s already exists, not creating." % name)
				continue

			try:
				self.createTest(self.tests[name])
			except RuntimeError as e:
				self.mate.error("Teaser: " + str(e))
				raise SystemExit

		util.enterRootDir()

		self.mate.popLogPrefix()
		return [name for name in sorted(self.tests, key=lambda k: self.tests[k]["order"])]


if __name__ == "__main__":
	import main
