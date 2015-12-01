def check_format(self):
	self.log("Validating SAM...")

	self.enterWorkingDirectory()
	result = self.sub("picard-tools ValidateSamFile MAX_OUTPUT=1000000000 IGNORE=RECORD_MISSING_READ_GROUP IGNORE=MISMATCH_FLAG_MATE_NEG_STRAND INPUT=%s"%self._("output:testee_path"))

	output=result["stdout"]

	for line in output.split("\n"):
		l=line.strip()
		if "ERROR" in line:
			self.error(line)