from lib import util
from lib import stats

def init(self):
	mapper = self.getMapper()

	if self._("output:bam"):
		self.setc("output:extension", ".bam")
	else:
		self.setc("output:extension", ".sam")

	self.setc("output:testee_path", self._("output:mapping_prefix") + mapper.getName() + self._("output:extension"))
	self.setc("output:sorted_testee_path", "sorted_" + self._("output:testee_path"))

	self.setc("input:sorted_mapping_comparison", "sorted_" + self._("input:mapping_comparison"))

	if self.mate._("evaluation:pos_threshold") != None:
		self.setc("evaluation:pos_threshold", self.mate._("evaluation:pos_threshold"))

	# Translate basic IO configuration into mapper parameters
	mapper.setInReferenceFile(self._("input:reference"))
	mapper.setInReadFiles(self._("input:reads"))
	mapper.setInPaired(self._("input:reads_paired_end"))
	mapper.setOutMappingFile(self._("output:testee_path"))
	mapper.addParams(self._("params"))

	# TODO: Fix
	if self._("output:bam"):
		mapper.addParams({"ngm": {"b": ""}})

	self.enterWorkingDirectory()
	self.dbg("Ref:   " + util.abs_path(self._("input:reference")))
	self.dbg("Reads: " + util.abs_path(self._("input:reads")[0]))
	self.dbg("Output:" + util.abs_path(self._("output:testee_path")))
	self.restoreWorkingDirectory()

	self.setRunResults(stats.ReferenceMappingStatistics())
