from stats import *
from sam import *
from lib import util

class Evaluator:
	def __init__(self):
		self.stats = ReferenceMappingStatistics()
		self.testee_filename = ""
		self.comparison_filename = ""
		self.position_threshold = 50
		self.export = False
		self.__warnings = []
		self.__errors = []
		self.failed_rows = []

	def set_testee(self, filename):
		self.testee_filename = filename

	def set_comparison(self, filename):
		self.comparison_filename = filename

	def set_position_threshold(self, t):
		self.position_threshold = t

	def set_export(self, export):
		self.export = True

	def set_export_file(self,file):
		self.export_handle = open(file,"w")
		self.export_handle.write("qname,status,reason\n")

	def warn(self, msg, filename, pos):
		print(msg)
		self.__warnings.append(tuple([msg, filename, pos]))

	def error(self, msg, filename, pos):
		print(msg)
		self.__errors.append(tuple([msg, filename, pos]))

	def get_warnings(self):
		return self.__warnings

	def get_errors(self):
		return self.__errors

	def get_stats(self):
		return self.stats

	def export_read(self, status, testee, comparison=None, reason="none"):
		if self.export:
			self.export_handle.write("%s,%s,%s\n"%(testee.qname,status,reason))

	def compute(self):
		raise NotImplementedError

class BasicEvaluator(Evaluator):
	def compute(self):
		sam_test = SAMFile(self.testee_filename)

		while sam_test.next():
			if sam_test.getCurr().is_secondary:
				self.stats.ignored_testee+=1
				continue

			self.stats.total += 1
			
			self.doCompareRows(sam_test.getCurr())

		for i in range(254, -1, -1):
			self.stats.mapq_cumulated[i]["correct"] += self.stats.mapq_cumulated[i + 1]["correct"]
			self.stats.mapq_cumulated[i]["wrong"] += self.stats.mapq_cumulated[i + 1]["wrong"]
		self.stats.computeMeasures()

	def doCompareRows(self, row_testee):
		if row_testee.is_unmapped:
			self.stats.not_mapped += 1
			#self.export_read("fail",row_testee,None,"unmapped")
		else:
			self.stats.correct += 1
			self.stats.mapq_cumulated[row_testee.mapq]["correct"] += 1
			#self.export_read("pass",row_testee)

class ThresholdBasedEvaluator(Evaluator):
	def compute(self):
		sam_test = SAMFile(self.testee_filename)
		sam_comp = SAMFile(self.comparison_filename)

		dont_advance_test = False
		warned_testee_end = False
		warned_comp_end = False

		while sam_comp.next():
			self.stats.total += 1

			edit_distance = len(util.parseMD(sam_comp.getCurr().getTag("MD"),sam_comp.getCurr().seq))
			if not edit_distance in self.stats.reads_by_edit_distance:
				self.stats.reads_by_edit_distance[edit_distance]=0
			self.stats.reads_by_edit_distance[edit_distance]+=1

			if dont_advance_test:
				dont_advance_test = False
			else:
				if sam_test.next():
					self.stats.total_testee += 1
				else:
					if not warned_testee_end:
						if self.stats.total_testee == 0:
							self.error("Unexpectedly reached end of mapper output", self.testee_filename, sam_comp.getCurr().qname)
						else:
							self.warn("Unexpectedly reached end of mapper output", self.testee_filename, sam_comp.getCurr().qname)
						warned_testee_end = True

					self.stats.not_found += 1
					self.export_read("fail", sam_comp.getCurr(), sam_comp.getCurr(), "not_found")
					continue

			#Check if source read identifiers are equal
			#If source read is not equal, theres been a shift in the rows of one of the alignments
			#which we have to adapt for
			while sam_test.getCurr().qname != sam_comp.getCurr().qname or sam_test.getCurr().is_secondary:
				if sam_test.getCurr().is_secondary:
					self.stats.ignored_testee += 1
					self.stats.total_testee += 1

					if not sam_test.next():
						self.warn("Unexpectedly reached end of mapper output while skipping secondary alignment",
								  self.testee_filename, sam_comp.getCurr().qname)
						break

					continue

				if sam_test.getCurr().qname > sam_comp.getCurr().qname:
					self.stats.not_found += 1
					self.export_read("fail", sam_comp.getCurr(), sam_comp.getCurr(), "not_found")

					if not sam_comp.next():
						self.warn(
							"Unexpectedly reached end of gold standard while searching for alignment with query name",
							self.comparison_filename, sam_test.getCurr().qname)
						break

					self.stats.total += 1
					
					edit_distance = len(util.parseMD(sam_comp.getCurr().getTag("MD"),sam_comp.getCurr().seq))
					if not edit_distance in self.stats.reads_by_edit_distance:
						self.stats.reads_by_edit_distance[edit_distance]=0
					self.stats.reads_by_edit_distance[edit_distance]+=1
				else:
					self.stats.not_found_comparison += 1
					if not sam_test.next():
						self.warn(
							"Unexpectedly reached end of mapper output while searching for alignment with query name",
							self.testee_filename, sam_comp.getCurr().qname)
						break
					self.stats.total_testee += 1

			#Handle paired end reads
			if sam_test.getCurr().is_paired or sam_comp.getCurr().is_paired:
				#Some sanity checks
				"""if sam_test.getCurr().is_paired and not sam_comp.getCurr().is_paired:
					self.warn("Testee read is part of a pair, but comparison read not", self.testee_filename,
							  sam_test.getCurr().qname)

				if sam_comp.getCurr().is_paired and not sam_test.getCurr().is_paired:
					self.warn("Comparison read is part of a pair, but test read not", self.testee_filename,
							  sam_test.getCurr().qname)"""

				#Dealing with paired end reads here
				if sam_test.getCurr().is_read1 and sam_comp.getCurr().is_read2:
					if sam_test.getLast() and sam_test.getLast().qname == sam_comp.getCurr().qname and sam_test.getLast().is_read2:
						self.doCompareRows(sam_test.getLast(), sam_comp.getCurr())
						continue
					else:
						if not sam_test.next():
							#self.warn("Reached end of testee mapping while trying to match pair", self.testee_filename,
							#		  sam_comp.getCurr().qname)
							break

						dont_advance_test = True

						if sam_test.getCurr().qname == sam_comp.getCurr().qname and sam_test.getCurr().is_read2:
							self.doCompareRows(sam_test.getCurr(), sam_comp.getCurr())
						else:
							#self.warn("Could not match pair", self.testee_filename, sam_test.getCurr().qname)
							self.stats.not_found += 1
							self.export_read("fail", sam_comp.getCurr(), sam_comp.getCurr(), "not_found")
						continue

				elif sam_test.getCurr().is_read2 and sam_comp.getCurr().is_read1:
					if sam_test.getLast() and sam_test.getLast().qname == sam_comp.getCurr().qname and sam_test.getLast().is_read1:
						self.doCompareRows(sam_test.getLast(), sam_comp.getCurr())
						continue
					else:
						if not sam_test.next():
							#self.warn("Reached end of testee mapping while trying to match pair", self.testee_filename,
							#		  sam_comp.getCurr().qname)
							break
						dont_advance_test = True

						if sam_test.getCurr().qname == sam_comp.getCurr().qname and sam_test.getCurr().is_read1:
							self.doCompareRows(sam_test.getCurr(), sam_comp.getCurr())
						else:
							#self.warn("Could not match pair", self.testee_filename, sam_test.getCurr().qname)
							self.stats.not_found += 1
							self.export_read("fail", sam_comp.getCurr(), sam_comp.getCurr(), "not_found")
						continue

			self.doCompareRows(sam_test.getCurr(), sam_comp.getCurr())

		while sam_test.next():
			self.stats.not_found_comparison += 1
			self.stats.total_testee += 1

			if not warned_comp_end:
				self.warn("Unexpectedly reached end of gold standard", self.comparison_filename,
						  sam_test.getCurr().qname)
				warned_comp_end = True

		#Sum up mapping quality threshold read counts
		correct_sum = 0
		wrong_sum = 0
		for i in range(254, -1, -1):
			self.stats.mapq_cumulated[i]["correct"] += self.stats.mapq_cumulated[i + 1]["correct"]
			self.stats.mapq_cumulated[i]["wrong"] += self.stats.mapq_cumulated[i + 1]["wrong"]

		self.stats.computeMeasures()

	def doCompareRows(self, row_testee, row_comp):
		if row_testee.is_unmapped:
			self.stats.not_mapped += 1
			self.export_read("fail", row_testee, row_comp, "unmapped")
			return

		edit_distance = len(util.parseMD(row_comp.getTag("MD"),row_comp.seq))

		if not edit_distance in self.stats.mapped_by_edit_distance:
			self.stats.mapped_by_edit_distance[edit_distance]=0

		self.stats.mapped_by_edit_distance[edit_distance]+=1

		if row_testee.rname != row_comp.rname:
			#Fix for mappers that treat RNAMEs containing special characters differently
			if "|" in row_comp.rname and row_testee.rname == row_comp.rname.split("|")[-2]:
				pass
			else:
				self.stats.wrong += 1
				self.stats.wrong_chromosome += 1
				self.stats.mapq_cumulated[row_testee.mapq]["wrong"] += 1
				self.export_read("fail",  row_testee, row_comp, "region")
				return

		if abs(row_testee.pos - row_comp.pos) > self.position_threshold:
			self.stats.wrong += 1
			self.stats.wrong_pos += 1
			self.stats.mapq_cumulated[row_testee.mapq]["wrong"] += 1
			self.export_read("fail", row_testee, row_comp, "position")
			return

		if row_testee.is_reverse != row_comp.is_reverse:
			self.stats.wrong += 1
			self.stats.reverse += 1
			self.stats.mapq_cumulated[row_testee.mapq]["wrong"] += 1
			self.export_read("fail", row_testee, row_comp, "reverse")
			return

		self.stats.mapq_cumulated[row_testee.mapq]["correct"] += 1
		self.stats.correct += 1
		self.export_read("pass", row_testee, row_comp)

class BasicEvaluatorSAM(ThresholdBasedEvaluator):
	def doCompareRows(self, row_testee, row_comp):
		if row_testee.is_unmapped:
			self.stats.not_mapped += 1
			#self.export_read("fail", row_testee, row_comp, "unmapped")
		else:
			self.stats.mapq_cumulated[row_testee.mapq]["correct"] += 1
			self.stats.correct += 1
			#self.export_read("pass", row_testee, row_comp)

if __name__ == "__main__":
	import sys

	if len(sys.argv) < 3:
		print("Usage: stats.py <testee_aligment.sam> <comparison_alignment.sam> <position threshold (default 50)>")
		raise SystemExit

	gen = ReferenceMappingStatisticsGenerator()

	if len(sys.argv) >= 4:
		gen.set_position_threshold(int(sys.argv[3]))

	gen.set_testee(sys.argv[1])
	gen.set_comparison(sys.argv[2])
	gen.compute()
	s = gen.get_stats()
	print(s.to_csv())
