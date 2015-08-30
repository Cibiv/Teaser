#!/usr/bin/env python
import os
import shutil
import time
import yaml
import util
import simulator

from tools import gsample
from tools import fastq2sam


class Teaser:
	def __init__(self, mate, config):
		self.mate = mate
		self.config = config

		self.supported_platforms = ["illumina","454","ion_torrent"]

		self.tests = self.config["tests"]

		self.default_test = {}
		self.default_test["title"] = None
		self.default_test["order"] = None

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
				raise ValueError("Reference genome path must be defined for data set")

			if not os.path.exists(test["reference"]):
				test["reference"] = os.path.abspath(self.config["reference_directory"] + "/" + test["reference"])

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

		if not os.path.exists(test["dir"] + "/mapping_comparison.sam"):
			return False

		if not os.path.exists(test["dir"] + "/reads.fastq") and not (
					os.path.exists(test["dir"] + "/reads1.fastq") and os.path.exists(test["dir"] + "/reads2.fastq")):
			return False

		return True

	def createTest(self, test):
		start_time = time.time()
		self.mate.getReport().generateProgress()

		self.log("Creating test %s" % test["name"])
		try:
			os.mkdir(test["dir"])
		except:
			self.log("Failed to create test directory, probably existing")

			self.rm(test["dir"] + "/mapping_comparison.sam")
			self.rm(test["dir"] + "/reads.fastq")
			self.rm(test["dir"] + "/reads1.fastq")
			self.rm(test["dir"] + "/reads2.fastq")

		self.ch(test)

		if test["sampling"]["enable"]:
			self.makeDatasetDS(test)
		else:
			self.makeDatasetNoDS(test)

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
		config["base"] = "tests_base/base_mapping"
		config["title"] = test["title"]
		config["tags"] = ["teaser"]
		config["input_info"] = {"simulator": test["simulator_cmd"], "platform": test["platform"],
								"read_length": str(test["read_length"]), "read_count": str(test["read_count"]),
								"insert_size": str(test["insert_size"]), "sampling": test["sampling"]["enable"],
								"sampling_ratio": str(test["sampling"]["ratio"]),
								"sampling_region_len": str(test["sampling"]["region_len"])}

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
		test["reference_sim"] = test["reference"]
		self.ch(test)
		self.simulate(test)

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
			self.log("Failed to remove file %s" % f)

	def main(self):
		self.mate.pushLogPrefix("Teaser")
		self.log("Init. Simulating %d test datasets." % len(self.tests))
		
		self.preprocessTests()

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

		util.enterRootDir()

		self.mate.popLogPrefix()
		return [name for name in sorted(self.tests, key=lambda k: self.tests[k]["order"])]


if __name__ == "__main__":
	import main
