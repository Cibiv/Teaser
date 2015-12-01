from lib import util

def generateTestList(self, tests):
	html = ""

	html += "<table id=\"test_list\" class=\"table table-striped\">"
	html += "<thead>"
	html += "<tr>"
	html += "<th>State</th>"
	html += "<th>Mapper</th>"
	html += "<th>Parameters</th>"
	html += "<th>Warnings</th>"
	html += "<th>Errors</th>"
	html += "<th>Throughput (reads/s)</th>"
	html += "</tr>"
	html += "</thead>"

	for test in tests:
		warnings = 0
		errors = 0

		show_test = True
		if self.mate.run_only != False and not test.getName() in self.mate.run_only:
			show_test = False
			break

		if not test.getWasRun() or not self.mate.isTestIncluded(test):
			show_test = False
			break

		warnings += test.getWarningCount()
		errors += test.getErrorCount()

		if not show_test:
			continue

		tclass = "info"
		icon = "glyphicon-ok"

		if warnings > 0:
			tclass = "warning"
			icon = "glyphicon-exclamation-sign"

		if errors > 0:
			tclass = "danger"
			icon = "glyphicon-remove"

		html += "<tr>"
		html += "<td class=\"col-md-1 " + tclass + "\" align=\"center\"><span class=\"glyphicon " + icon + "\"></span></td>"
		html += "<td><a href=\"" + test.getFullName() + ".html\">" + test.getMapper().getTitle() + "</a></td>"
		html += "<td>%s</td>" % test.getMapper().param_string

		total=test.getRunResults().total
		if total != 0:
			correct=float(100 * test.getRunResults().correct)/total
			wrong=float(100 * test.getRunResults().wrong)/total
			not_mapped=float(100 * (test.getRunResults().not_mapped + test.getRunResults().not_found))/total
		else:
			correct=0
			wrong=0
			not_mapped=0

		maptime=test.getRunResults().maptime
		if maptime != 0:
			throughput=total/float(test.getRunResults().maptime)		
		else:
			throughput=-1

		html += "<td>%d</td>" % test.getWarningCount()
		html += "<td>%d</td>" % test.getErrorCount()
		html += "<td>%d</td>" % throughput

		html += "</tr>"

	html += "</table>"

	return html


def report_overview(self, gen, page, test_objects):
	page.addSection("Results Overview", generateTestList(self,test_objects), None, "")
	return ""