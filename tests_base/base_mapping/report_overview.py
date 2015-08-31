from lib import util


def generateTestList(self, tests):
	html = ""

	html += "<div class=\"table-responsive\"><table id=\"test_list\" class=\"table table-striped\">"
	html += "<thead>"
	html += "<tr>"
	html += "<th>State</th>"
	html += "<th>Mapper</th>"
	html += "<th>Parameters</th>"
	# html += "<th>Warnings</th>"
	# html += "<th>Errors</th>"
	html += "<th>Correctly Mapped</th>"
	html += "<th>Wrongly Mapped</th>"
	html += "<th>Not Mapped</th>"
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
		# html += "<td>%d</td>" % warnings
		# html += "<td>%d</td>" % errors
		# html += "<td>%ds</td>" % test.getRunTime()
		html += "<td>%.3f%%</td>" % (float(100 * test.getRunResults().correct) / test.getRunResults().total)
		html += "<td>%.3f%%</td>" % (float(100 * test.getRunResults().wrong) / test.getRunResults().total)
		html += "<td>%.3f%%</td>" % (float(100 * test.getRunResults().not_mapped) / test.getRunResults().total)
		html += "<td>%d</td>" % (test.getRunResults().total / float(test.getRunResults().maptime))
		html += "</tr>"

	html += "</table></div>"
	return html


def generateMappingStatisticsPlot(page, test_objects):
	import json

	columns_mapqs = []
	for i in range(256):
		columns_mapqs.append([["Correct"], ["Wrong"], ["Not Mapped"]])
	groups = []
	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None:
			continue

		mapqs = sorted(result.mapq_cumulated)
		for curr in mapqs:
			columns_mapqs[curr][0].append(result.mapq_cumulated[curr]["correct"] / float(result.total))
			columns_mapqs[curr][1].append(result.mapq_cumulated[curr]["wrong"] / float(result.total))
			columns_mapqs[curr][2].append((result.total - (
				result.mapq_cumulated[curr]["correct"] + result.mapq_cumulated[curr]["wrong"])) / float(result.total))

		groups.append(test.getMapper().getTitle())
	page.addSection("Mapping Statistics",
					"""<div align="right">MAPQ cutoff (0-255):&nbsp;<input type="number" onchange="javascript:updateMapstatsChart(this.value);" value="0" min="0" max="255"></div><div id="plot_mapstats"></div>""",
					None,
					"This plot shows the fractions of correctly, wrongly and not mapped reads for each mapper and the selected mapping quality cutoff. Reads that have been filtered using the mapping quality cutoff are shown as unmapped. The interactive legend can be used to, for example, display only the number of wrongly and not mapped reads.")
	page.addScript("""
var column_mapqs=%s;
function updateMapstatsChart(cutoff)
{
	mapstats_chart.load({columns: column_mapqs[cutoff], type:'bar',groups: [['Not Mapped','Wrong','Correct']],order: null});
}
var mapstats_chart = c3.generate({
bindto: '#plot_mapstats',
data: {
  columns: %s,
  type: 'bar',
  groups: [['Not Mapped','Wrong','Correct']],
  order: null,
  colors: {
	    "Correct": d3.rgb('#2CA02C'),
	    "Wrong": d3.rgb('#FF7F0E'),
	    "Not Mapped": d3.rgb('#1F77B4')  }
},
grid: {
  y: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "Mapper", position: "outer-middle" },
    type: "category",
    categories: %s
  },

  y: {
    label: { text: "Percentage of reads", position: "outer-middle" },
    tick: {
      format: d3.format(".3%%")
    },
    padding:
    {
    top:15
    }
  }
},
legend: {
	position: "bottom"
},
tooltip: {
	grouped: false
}
});


""" % (json.dumps(columns_mapqs), json.dumps(columns_mapqs[0]), json.dumps(groups)))


def generateOverallScatterPlot(self, page, test_objects):
	import json

	csv = "parameter,correct_percent,runtime\n"
	# csv = "correct_percent,reads_per_sec\n"

	columns = []
	xs = {}
	labels = {}

	max_throughput = 0
	for test in test_objects:
		if test.getRunResults() != None:
			max_throughput = max(test.getRunResults().correct / test.getRunResults().maptime, max_throughput)

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None:
			continue

		mapper_name = test.getMapper().getTitle() + " " + test.getMapper().param_string
		columns.append([mapper_name + "_x", round((result.total / result.maptime), 0)])
		columns.append([mapper_name, result.correct / float(result.total)])
		xs[mapper_name] = mapper_name + "_x"

		labels[int(result.total / result.maptime)] = test.getMapper().getTitle() + " " + test.getMapper().param_string

		# csv += "%f,%d\n" % (round(result.correct / float(result.total), 3), int(result.total / result.maptime))
		csv += test.getMapper().getName() + "" + test.getMapper().param_string + ",%f,%f" % (
		round(result.correct / float(result.total), 3), result.maptime) + "\n"

	page.addSection("Results Overview", generateTestList(self,test_objects) + """<p style="margin-top:15px;">The figure below visualizes above results by directly comparing accuracy and throughput. The optimal mapper showing both highest accuracy and throughput, if any, will be located in the top right corner.</p> <div id="plot_os"></div>""", None, """Mappers were evaluated for the given test <a href="#section2">data set</a>. The table below shows the used parameters, mapping statistics and throughput for each mapper. Detailed results for a mapper can be displayed by clicking on its name in the table or the navigation on top.""")
	#page.addSection("Overall Performance: Raw CSV Data", """<pre>%s</pre>""" % csv)

	show_legend = len(columns) < 30

	page.addScript("""
var params=%s;

var chart = c3.generate({
bindto: '#plot_os',
size: {
  height: 500
},
data: {
  xs: %s,
  columns: %s,
  type: 'scatter'
},
grid: {
  y: {
    show: true
  },
  x: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "Throughput [Reads/s]", position: "outer-middle"},
    tick: {fit: false, format: d3.format("d")},
    padding: {
    left: 500
    }
  },

  y: {
    label: { text: "Correctly Mapped [%%]", position: "outer-middle"},
    tick: {
      format: d3.format(".3%%")
    }
  }
},
point: {
  r: 5
},
legend: {
	position: "bottom",
	show:%s,
	inset: {
		anchor: 'top-left',
		x: 20,
		y: 10,
		step: 2
	}
},
tooltip: {
	format: {
		//title: function (d) { return ""; }
	},
	grouped: false
}
});""" % (json.dumps(labels), json.dumps(xs), json.dumps(columns), str(show_legend).lower()))


def generatePrecisionRecallPlot(page, test_objects):
	import json

	columns = [["Precision"], ["Recall"]]
	groups = []

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None:
			continue
		groups.append(test.getMapper().getTitle())
		columns[0].append(round(result.precision, 4))
		columns[1].append(round(result.recall, 4))

	page.addSection("Precision and Recall", """<div id="plot_pr"></div>""")
	page.addScript("""
var chart = c3.generate({
bindto: '#plot_pr',
data: {
  columns: %s,
  type: 'bar',
},
grid: {
  y: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "Mapper", position: "outer-middle" },
    type: "category",
    categories: %s
  },

  y: {
    label: { text: "Value", position: "outer-middle"}
  }
},
legend: {
	position: "bottom"
},
tooltip: {
	grouped: false
}
});""" % (json.dumps(columns), json.dumps(groups)))


def generateResourcePlot(page, test_objects, measure):
	import json

	if measure == "runtime":
		columns = [["Runtime"]]
		title = "Runtime [min]"
		section_title = "Runtime"
	elif measure == "memory":
		columns = [["Memory Usage"]]
		title = "Memory Usage [MB]"
		section_title = "Memory Usage"
	elif measure == "corrects":
		columns = [["Correct/s"]]
		title = "Correctly Mapped [reads/s]"
		section_title = "Correctly Mapped/s"
	groups = []

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None:
			continue
		groups.append(test.getMapper().getTitle())
		if measure == "runtime":
			columns[0].append(round(result.maptime / 60.0, 3))
		elif measure == "memory":
			columns[0].append(round(result.memory / (1000 * 1000)))
		elif measure == "corrects":
			try:
				columns[0].append(round(result.correct / result.maptime, 3))
			except ZeroDivisionError:
				columns[0].append(0)

	page.addSection(section_title, """<div id="plot_resource_%s"></div>""" % measure)
	page.addScript("""
var chart = c3.generate({
bindto: '#plot_resource_%s',
data: {
  columns: %s,
  type: 'bar',
},
grid: {
  y: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "Mapper", position: "outer-middle" },
    type: "category",
    categories: %s
  },

  y: {
    label: { text: "%s", position: "outer-middle" },
    tick: { format: d3.format("10.3f") }
  }
},
legend: {
	position: "inset",
	show:false,
	inset: {
		anchor: 'top-right'
	}
}
});""" % (measure, json.dumps(columns), json.dumps(groups), title))


def generateMappingQualityOverview(page, test_objects):
	import json

	data = []
	data_dist = []
	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		column = [test.getMapper().getTitle()]
		column_dist = [test.getMapper().getTitle()]
		results = test.getRunResults()

		if results == None:
			continue

		mapqs = sorted(results.mapq_cumulated)
		for curr in mapqs:
			lost_correct = (results.correct - results.mapq_cumulated[curr]["correct"])
			lost_wrong = (results.wrong - results.mapq_cumulated[curr]["wrong"])
			try:
				column.append(round(lost_wrong / float(lost_correct), 4))
			except ZeroDivisionError:
				column.append(0)

			if curr < 255:
				column_dist.append( (results.mapq_cumulated[curr]["correct"]+results.mapq_cumulated[curr]["wrong"]) - (results.mapq_cumulated[curr+1]["correct"]+results.mapq_cumulated[curr+1]["wrong"])  )
			else:
				column_dist.append(0)

		data.append(column)
		data_dist.append(column_dist)

	page.addSection("Mapping Quality",
					"""<div id="plot_mapq_rating"></div><p>&nbsp;</p><div id="plot_mapq_dist"></div>""",
					None,
					"This section represents an overview of the distribution of mapping quality values for all mappers. A detailed evaluation of mapping qualities for specific mappers can be found on the respective mapper results page (accessible using the navigation on top). The first plot rates each mapping quality threshold (0-255) by comparing the numbers of wrongly and correctly mapped reads that would be removed due to falling under the threshold. The second plot shows the total number of reads for each mapping quality value.")
	page.addScript("""
var chart = c3.generate({
    bindto: '#plot_mapq_rating',
    size: {
      height: 500
    },
    data: {
      columns: %s
    },
    grid: {
      y: {
        show: true
      }
    },
    axis: {
      x: {
        label: {text: "Mapping Quality Threshold", position: "outer-middle"},
        min: -5
      },

      y: {
        label: {text: "Filtered wrong reads  / Filtered correct reads", position: "outer-middle"}
      }
    },
    legend: {
		position: "inset",
		show:true,
		inset: {
			anchor: 'top-right',
			x: 20,
			y: 10,
			step: 2
		}
    },
    point: {
    	show: false
    },
    subchart:
    {
        show:true
    }
});""" % json.dumps(data))

	page.addScript("""
var chart = c3.generate({
    bindto: '#plot_mapq_dist',
    size: {
      height: 500
    },
    data: {
      columns: %s
    },
    grid: {
      y: {
        show: true
      }
    },
    axis: {
      x: {
        label: {text: "Mapping Quality Value", position: "outer-middle"},
        min: -5
      },

      y: {
        label: {text: "Number of Reads", position: "outer-middle"}
      }
    },
    legend: {
		position: "inset",
		show:true,
		inset: {
			anchor: 'top-right',
			x: 20,
			y: 10,
			step: 2
		}
    },
    point: {
    	show: false
    }
});""" % json.dumps(data_dist))


def generateDataSetInfo(self,page,test):
	test_name = self.internal_name
	self.enterWorkingDirectory()

	html = ""
	html += "<div class=\"table-responsive\"><table class=\"table table-striped\">"
	html += "<tbody>"
	html += "<tr>"
	html += "<th>Sequencing Platform</th>"
	html += "<td>%s</td>" % test._("input_info:platform")
	html += "</tr>"
	html += "<tr>"
	html += "<th>Read Length</th>"
	html += "<td>%d</td>" % int(test._("input_info:read_length"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Read Count</th>"
	html += "<td>%d</td>" % int(test._("input_info:read_count"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Sequence Divergence</th>"
	html += "<td>%s</td>" % str(test._("input_info:divergence"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Paired-End</th>"
	html += "<td>%s</td>" % util.yes_no(test._("input:reads_paired_end"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Insert Size</th>"
	html += "<td>%s</td>" % str(test._("input_info:insert_size") if test._("input:reads_paired_end") else "None" )
	html += "</tr>"
	html += "<tr>"
	html += "<th>Subsampling enabled</th>"
	html += "<td>%s</td>" % util.yes_no(test._("input_info:sampling"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Sampling ratio</th>"
	html += "<td>%.3f</td>" % float(test._("input_info:sampling_ratio"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Sampling region length</th>"
	html += "<td>%d</td>" % int(test._("input_info:sampling_region_len"))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Reference Genome File</th>"
	html += "<td>%s</td>" % str(util.abs_path(test._("input:reference")))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Read File(s)</th>"
	html += "<td>%s</td>" % str(", ".join([util.abs_path(f) for f in test._("input:reads")]))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Gold Standard Alignment File</th>"
	html += "<td>%s</td>" % str(util.abs_path(test._("input:mapping_comparison")))
	html += "</tr>"
	html += "<tr>"
	html += "<th>Simulator</th>"
	html += "<td>%s</td>" % str(test._("input_info:simulator"))
	html += "</tr>"
	html += "</tbody>"
	html += "</table></div>"

	self.restoreWorkingDirectory()
	page.addSection("Data Set", html, None, "For data sets simulated using Teaser, details regarding the simulation parameters are displayed here.")	



def report_overview(self, gen, page, test_objects):
	page.addScript("""$(document).ready(function() {
    $('#test_list').dataTable({
    "bPaginate": false,
    "bFilter": false,
    "bInfo": false,
    "order": [[ 3, "desc" ]]
  });
} );""")

	generateOverallScatterPlot(self, page, test_objects)
	generateDataSetInfo(self, page, test_objects[0])
	generateMappingStatisticsPlot(page, test_objects)
	generateMappingQualityOverview(page, test_objects)
	generatePrecisionRecallPlot(page, test_objects)
	generateResourcePlot(page, test_objects, "corrects")
	generateResourcePlot(page, test_objects, "runtime")
	generateResourcePlot(page, test_objects, "memory")
	
	return ""
