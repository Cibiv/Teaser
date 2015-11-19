def evaluate(self):
	if self.getMapper().getName() == self.mate._("evaluation:versioned:testee"):
		comparison_test = self.mate.getTestByMapperName(self.getName(), self.mate._("evaluation:versioned:base"))

		testee_result = self.getRunResults()
		comparison_result = comparison_test.getRunResults()

		if testee_result.correct < comparison_result.correct:
			self.warn("Less correct reads than base %s"%comparison_test.getMapper().getTitle())
