def calc_time(self):
	mapper_result = self._("output:mapper_result")

	if mapper_result == None:
		return False

	stats_out = self.getRunResults()

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