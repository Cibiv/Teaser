import os


def cleanup(self):
	if self.getErrorCount() > 0 and self.mate._("main:force_clean") == None:
		self.dbg("Error in test, not cleaning up!")

	self.enterWorkingDirectory()

	self.getMapper().onCleanup()

	# Remove mapper output files
	try:
		os.remove(self._("output:testee_path"))
	except OSError:
		pass

	try:
		os.remove(self._("output:sorted_testee_path"))
	except OSError:
		pass
