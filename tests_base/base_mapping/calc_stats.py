import os
import csv

from lib import util
from lib import stats

percent = util.percent


def calc_stats(self):
	ReferenceMappingStatisticsGenerator = stats.ReferenceMappingStatisticsGenerator

	self.dbg("Compute mapping statistics (threshold %d)... " % self._("pos_threshold"))
	self.enterWorkingDirectory()

	actual_comparison_path = self._("input:mapping_comparison")
	if os.path.exists(self._("input:sorted_mapping_comparison")):
		actual_comparison_path = self._("input:sorted_mapping_comparison")

	stats_gen = ReferenceMappingStatisticsGenerator()
	stats_gen.set_position_threshold(self._("pos_threshold"))
	stats_gen.set_rna(self._("evaluate_rna"))

	try:
		stats_gen.set_testee(self._("output:sorted_testee_path"))
	except Exception as e:
		self.error("Failed to open output file for comparison - mapping might have failed, see subprocess logs (" + str(
			e) + ")", sam_testee_sorted_path, None)
		raise SystemExit

	try:
		stats_gen.set_comparison(actual_comparison_path)
	except Exception as e:
		self.error("Failed to open comparison file for comparison (" + str(e) + ")", actual_comparison_path, None)
		raise SystemExit

	stats_gen.compute()
	stats_out = stats_gen.get_stats()
	self.log(stats_out.to_string())

	for msg, file, pos in stats_gen.get_warnings():
		self.warn(msg, file, pos)

	for msg, file, pos in stats_gen.get_errors():
		self.error(msg, file, pos)

	mapper_result = self._("output:mapper_result")

	if mapper_result != None:
		maptime_raw=0
		inittime=0

		if self.mate.measure_cputime:
			maptime_raw=mapper_result["usrtime"]+mapper_result["systime"]
			inittime=self._("output:mapper_init_time")["cputime"]
			stats_out.time_measure = "CPU"
		else:
			maptime_raw=mapper_result["time"]
			inittime=self._("output:mapper_init_time")["time"]
			stats_out.time_measure = "Wall clock"



		if inittime < maptime_raw:
			maptime = maptime_raw - inittime
		else:
			maptime = maptime_raw
			self.warn("Runtime < Init runtime, using unadjusted runtime as mapping time")

		stats_out.maptime_raw = maptime_raw
		stats_out.maptime = maptime
		stats_out.inittime = inittime

		stats_out.initwalltime = self._("output:mapper_init_time")["time"]
		stats_out.initcputime = self._("output:mapper_init_time")["cputime"]
		stats_out.initusrtime = self._("output:mapper_init_time")["usrtime"]
		stats_out.initsystime = self._("output:mapper_init_time")["systime"]

		stats_out.walltime = mapper_result["time"]
		stats_out.cputime = mapper_result["usrtime"] + mapper_result["systime"]
		stats_out.usrtime = mapper_result["usrtime"]
		stats_out.systime = mapper_result["systime"]

		stats_out.memory = mapper_result["memory"]

	self.setRunResults(stats_out)

	for msg, filename, location in stats_gen.get_warnings():
		self.warn(msg, filename, location)

	for msg, filename, location in stats_gen.get_errors():
		self.error(msg, filename, location)
