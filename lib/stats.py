#!/usr/bin/env python
class ReferenceMappingStatistics:
	def __init__(self):
		#Main statistics (Sum up to total)
		self.correct = 0  #Num. of correctly mapped query sequences
		self.wrong = 0  #Num. of wrongly mapped query sequences (different region or pos diff over threshold)
		self.not_mapped = 0  #Num. of unmapped query sequences
		self.not_found = 0  #Num. of sequences that were not found in the self output (fatal if > 0)

		#Extra statistics
		self.total = 0  #Actual number of reads (in reference mapping)
		self.total_testee = 0  #Number of reads in mapper output (includes secondary alignments)
		self.ignored_testee = 0
		self.reverse = 0
		self.not_found_comparison = 0

		self.wrong_chromosome = 0
		self.wrong_pos = 0

		self.precision = 0
		self.recall = 0
		self.fmeasure = 0

		#Timing
		self.maptime_raw = 1
		self.maptime = 1
		self.inittime = 1

		self.initwalltime = 1
		self.initcputime = 1
		self.initusrtime = 1
		self.initsystime = 1

		self.walltime = 1
		self.cputime = 1
		self.usrtime = 1
		self.systime = 1

		self.memory = 1
		self.time_measure = "None"

		self.mapped_by_edit_distance = {}
		self.reads_by_edit_distance = {}

		#Additional data
		self.failed_rows = []

		self.mapq_cumulated = {}
		for i in range(256):
			self.mapq_cumulated[i] = {"correct": 0, "wrong": 0}

		#Placeholders
		self.maptime = -1

	def to_string(self):
		return self.to_csv()

	def to_csv(self):
		result = "correct,wrong,not_mapped,not_found,not_found_comparison,total,reverse,secondary,precision,recall,fmeasure\n"
		result += ",".join([str(e) for e in
							[self.correct, self.wrong, self.not_mapped, self.not_found, self.not_found_comparison,
							 self.total, self.reverse, self.ignored_testee, self.precision, self.recall,
							 self.fmeasure]])
		return result

	def computeMeasures(self):
		try:
			self.precision = float(self.correct) / float(self.correct + self.wrong)
			self.recall = float(self.correct) / float(self.correct + self.not_mapped)
			self.fmeasure = (2 * (self.precision * self.recall)) / (self.precision + self.recall)
		except:
			pass

	def diff(self, other):
		result = ReferenceMappingStatistics()

		result.correct = self.correct - other.correct
		result.wrong = self.wrong - other.wrong
		result.not_mapped = self.not_mapped - other.not_mapped
		result.not_found = self.not_found - other.not_found
		result.total = self.total - other.total
		result.reverse = self.reverse - other.reverse
		result.not_found_comparison = self.not_found_comparison - other.not_found_comparison

		try:
			result.maptime = self.maptime - other.maptime
		except:
			pass

		return result

class MappingRow:
	def __init__(self, alignment=None):
		return

		if alignment == None:
			return

		self.qname = alignment.qname
		self.rname = alignment.rname
		self.pos = alignment.pos
		self.mapq = alignment.mapq
		self.rnext = alignment.rnext
		self.pnext = alignment.pnext
		self.is_duplicate = alignment.is_duplicate
		self.is_paired = alignment.is_paired
		self.is_proper_pair = alignment.is_proper_pair
		self.is_qcfail = alignment.is_qcfail
		self.is_read1 = alignment.is_read1
		self.is_read2 = alignment.is_read2
		self.is_reverse = alignment.is_reverse
		self.is_secondary = alignment.is_secondary
		self.is_unmapped = alignment.is_unmapped
		self.mate_is_reverse = alignment.mate_is_reverse
		self.mate_is_unmapped = alignment.mate_is_unmapped
		self.seq = alignment.seq
