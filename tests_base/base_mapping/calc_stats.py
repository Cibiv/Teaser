import os
import csv

from lib import util
from lib import stats

percent = util.percent

def calc_stats(self):
	self.dbg("Compute mapping statistics (%s, threshold %d)... " % (self._("evaluation:class"),self._("evaluation:pos_threshold")) )
	self.enterWorkingDirectory()

	actual_comparison_path = self._("input:mapping_comparison")
	if os.path.exists(self._("input:sorted_mapping_comparison")):
		actual_comparison_path = self._("input:sorted_mapping_comparison")

	eval_class = util.locate(self._("evaluation:class"))
	generator = eval_class()
	generator.set_position_threshold(self._("evaluation:pos_threshold"))

	if self._("input_info:methylation:enable"):
		generator.set_methylation_frequencies(self._("input_info:methylation")["rates"])

	try:
		generator.set_testee(self._("output:sorted_testee_path"))
	except Exception as e:
		self.error("Failed to open output file for comparison - mapping might have failed, see subprocess logs (" + str(
			e) + ")", sam_testee_sorted_path, None)
		raise SystemExit

	try:
		generator.set_comparison(actual_comparison_path)
	except Exception as e:
		self.error("Failed to open comparison file for comparison (" + str(e) + ")", actual_comparison_path, None)
		raise SystemExit


	if self.mate.export_reads:
		generator.set_export(True)
		_,reads_csv_path=self.getCSVPath(self.getMapper().getName()+"_reads")
		generator.set_export_file(reads_csv_path)
		self.dbg("Exporting reads to %s"%reads_csv_path)

	generator.compute()
	stats_out = generator.get_stats()
	self.log(stats_out.to_string())

	for msg, file, pos in generator.get_warnings():
		self.warn(msg, file, pos)

	for msg, file, pos in generator.get_errors():
		self.error(msg, file, pos)

	self.setRunResults(stats_out)

