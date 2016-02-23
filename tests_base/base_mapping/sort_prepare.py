from lib import util
import os

def sort_prepare(self):
	self.enterWorkingDirectory()

	if self.mate.output_bam:
		self.dbg("Generating BAM output...")
		os.system("samtools view -bS %s > %s"%(self._("output:testee_path"),self._("output:testee_path")+".bam"))

	self.dbg("Sorting...")

	sorted_testee_filename = util.sort_sam(self._("output:testee_path"),int(self.mate._("threads")))
	if sorted_testee_filename == False:
		self.error("Failed to sort testee mapping")
		raise SystemExit
	else:
		self.setc("output:sorted_testee_path",sorted_testee_filename)

	if self._("input:mapping_comparison") != "" and not util.is_sam_sorted(self._("input:mapping_comparison")):
		sorted_comparison_filename = util.sort_sam(self._("input:mapping_comparison"),int(self.mate._("threads")))
		if sorted_comparison_filename == False:
			self.error("Failed to sort comparison mapping")
			raise SystemExit
		else:
			os.remove(self._("input:mapping_comparison"))
			os.rename(sorted_comparison_filename,self._("input:mapping_comparison"))
			self.setc("input:sorted_mapping_comparison",self._("input:mapping_comparison"))



