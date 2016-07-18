from lib import util

def generateTestList(self, tests):
	html = ""

	html += "<table id=\"test_list\" class=\"table table-striped\">"
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

	csv = "mapper,additional_parameters,correctly_mapped_percent,wrongly_mapped_percent,not_mapped_percent,throughput_reads_per_sec\n"

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

		if errors == 0:
			html += "<td>%.3f%%</td>" % correct
			html += "<td>%.3f%%</td>" % wrong
			html += "<td>%.3f%%</td>" % not_mapped
			html += "<td>%d</td>" % throughput
			csv+="%s,%s,%.4f,%.4f,%.4f,%d\n" % (test.getMapper().getTitle(),test.getMapper().param_string,correct,wrong,not_mapped,throughput)
		else:
			html += "<td></td>"
			html += "<td></td>"
			html += "<td></td>"
			html += "<td></td>"
			csv+="%s,%s,-,-,-,-\n" % (test.getMapper().getTitle(),test.getMapper().param_string)

		html += "</tr>"

	csv_filename = self.writeCSV("overview",csv)

	html += "</table>"
	html += util.makeExportDropdown("",csv_filename) 


	return html

def generateEditDistancePlot(self, page, test_objects):
	import json

	data_dist = []
	max_edit_dist = 0

	reads_by_edit_distance = {}
	for test in test_objects:
		results = test.getRunResults()
		if len(results.reads_by_edit_distance)!=0:
			reads_by_edit_distance = results.reads_by_edit_distance

	max_edit_dist = max([key for key in reads_by_edit_distance])

	x=[]
	for key in reads_by_edit_distance:
		if reads_by_edit_distance[key] > 100:
			x.append(key)


	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		column_dist = [test.getMapper().getTitle()]
		results = test.getRunResults()

		if results == None or test.getErrorCount():
			continue

		reads_by_edit_distance = results.reads_by_edit_distance
		mapped_by_edit_distance = results.mapped_by_edit_distance

		for i in range(max_edit_dist+1):
			mapped = mapped_by_edit_distance[i] if i in mapped_by_edit_distance else 0
			reads = reads_by_edit_distance[i] if i in reads_by_edit_distance else 0

			if reads > 100:
				column_dist.append((reads-mapped)/float(reads))
			else:
				pass

		data_dist.append(column_dist)
		print(column_dist)

	data_dist.append(["x"]+x)

	page.addSection("Edit Distance",
					"""This plot shows the effect of the number of mismatches introduced in reads on mapping rates.<br><br><div id="plot_edit_dist"></div>%s""" %  util.makeExportDropdown("plot_edit_dist",""),
					None,
					"")

	page.addScript("""
var chart = c3.generate({
    bindto: '#plot_edit_dist',
    size: {
      height: 500
    },
    data: {
      x: 'x',
      columns: %s
    },
    grid: {
      y: {
        show: true
      }
    },
    axis: {
      x: {
        label: {text: "Edit distance in read", position: "outer-middle"}
      },

      y: {
        label: {text: "Not mapped reads [%%]", position: "outer-middle"},
		tick: {
		  format: d3.format(".3%%")
		}
      }
    },
    legend: {
		show:true
    },
    point: {
    	show: false
    }
});""" % json.dumps(data_dist))

def generateMappingStatisticsPlot(self, page, test_objects):
	import json

	csv = "mapper,mapq_threshold,correctly_mapped_percent,wrongly_mapped_percent,not_mapped_percent\n"

	columns_mapqs = []
	for i in range(256):
		columns_mapqs.append([["Correct"], ["Wrong"], ["Not Mapped"]])
	groups = []
	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None or test.getErrorCount():
			continue

		mapqs = sorted(result.mapq_cumulated)
		for curr in mapqs:
			correct,wrong,not_mapped=0,0,0
			if result.total != 0:
				correct=result.mapq_cumulated[curr]["correct"] / float(result.total)
				wrong=result.mapq_cumulated[curr]["wrong"] / float(result.total)
				not_mapped=(result.total - (
result.mapq_cumulated[curr]["correct"] + result.mapq_cumulated[curr]["wrong"])) / float(result.total)

			columns_mapqs[curr][0].append(correct)
			columns_mapqs[curr][1].append(wrong)
			columns_mapqs[curr][2].append(not_mapped)

			csv += "%s,%d,%.4f,%.4f,%.4f\n" % (test.getMapper().getTitle(), curr, correct, wrong, not_mapped)

		groups.append(test.getMapper().getTitle())

	csv_filename = self.writeCSV("mapping_statistics",csv)

	page.addSection("Mapping Statistics",
					"""
					<div class="panel panel-default">
						<div class="panel-body">
							<div class="row">
								<div class="col-md-6">
									<label for="mapqSelect">MAPQ cutoff (<span id="cutoffText">0</span>):</label>
									<div class="input-group">
										<input id="mapqSelect" type="range" oninput="javascript:$('#cutoffText').html(this.value);" onchange="javascript:updateMapstatsChart(this.value);" value="0" min="0" max="255">
									</div>
								</div>
							</div>
						</div>
					</div>
					<div id="plot_mapstats"></div>%s""" % util.makeExportDropdown("plot_mapstats",csv_filename),
					None,
					"This plot shows the fractions of correctly, wrongly and not mapped reads for each mapper and the selected mapping quality cutoff. Reads that have been filtered using the mapping quality cutoff are shown as unmapped. The interactive legend can be used to, for example, display only the number of wrongly and not mapped reads.")
	page.addScript("""
var column_mapqs=%s;
function updateMapstatsChart(cutoff)
{
	mapstats_chart.axis.labels({x:"Mappers (MAPQ Threshold "+cutoff+")"});
	mapstats_chart.load({columns: column_mapqs[cutoff], type:'bar',groups: [['Not Mapped','Wrong','Correct']],order: null});
}
var mapstats_chart = c3.generate({
bindto: '#plot_mapstats',
size: {
  height: 400
},
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
    label: { text: "Mapper (MAPQ Threshold 0)", position: "outer-middle" },
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

	csv = "parameter,correct_percent,throughput_reads_per_sec\n"
	# csv = "correct_percent,reads_per_sec\n"

	columns = []
	xs = {}
	labels = {}

	max_throughput = 0
	for test in test_objects:
		if test.getRunResults() != None and test.getErrorCount() == 0:
			throughput=-1
			if test.getRunResults().maptime != 0:
				throughput=test.getRunResults().correct / test.getRunResults().maptime
			max_throughput = max(throughput, max_throughput)

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None or test.getErrorCount():
			continue

		mapper_name = test.getMapper().getTitle() + " " + test.getMapper().param_string

		correct,throughput=0,0
		if result.total != 0:
			correct=result.correct / float(result.total)

		if result.maptime != 0:
			throughput=round((result.total / result.maptime), 0)
			labels[int(result.total / result.maptime)] = test.getMapper().getTitle() + " " + test.getMapper().param_string

		columns.append([mapper_name + "_x", throughput, 0])
		columns.append([mapper_name, correct])
		xs[mapper_name] = mapper_name + "_x"

		csv += "%s,%s,%f,%f\n" % (test.getMapper().getName(),test.getMapper().param_string,round(correct,3),throughput)

	csv_filename = self.writeCSV("overview_scatter",csv)

	page.addSection("Results Overview", generateTestList(self,test_objects) + """<p style="margin-top:15px;">The figure below visualizes above results by directly comparing accuracy and throughput. The optimal mapper showing both highest accuracy and throughput, if any, will be located in the top right corner. <div id="plot_os"></div>%s""" % util.makeExportDropdown("plot_os",csv_filename), None, """Mappers were evaluated for the given test <a href="#section2">data set</a>. The table below shows the used parameters, mapping statistics and throughput for each mapper. Detailed results for a mapper can be displayed by clicking on its name in the table or the navigation on top.""")

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


def generatePrecisionRecallPlot(self, page, test_objects):
	import json

	csv = "mapper,precision,recall\n"
	columns = [["Precision"], ["Recall"]]
	groups = []

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None or test.getErrorCount():
			continue
		groups.append(test.getMapper().getTitle())
		columns[0].append(round(result.precision, 4))
		columns[1].append(round(result.recall, 4))

		csv += "%s,%.4f,%.4f\n" % (test.getMapper().getTitle(),result.precision,result.recall)

	csv_filename = self.writeCSV("precision_recall",csv)

	page.addSection("Precision and Recall", """<div id="plot_pr"></div>%s""" % util.makeExportDropdown("plot_pr",csv_filename) )
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

def generateROCPlot(self, page, test_objects):
    import json
    import math

    xs = {}
    columns = []

    labels=[]

    for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
        result = test.getRunResults()
        if result == None or test.getErrorCount():
            continue

        xs[test.getMapper().getTitle()] = test.getMapper().getTitle() + "_x"

        column_x=[test.getMapper().getTitle()+"_x"]
        column_data = [test.getMapper().getTitle()]

        for mapq in range(255):
            correctfrac=result.mapq_cumulated[mapq]["correct"]
            wrongfrac=result.mapq_cumulated[mapq]["wrong"]
            if wrongfrac==0 or correctfrac==0:
                continue
            correctfrac=math.log(correctfrac,10)
            wrongfrac=math.log(wrongfrac,10)
            column_x.append(wrongfrac)
            column_data.append(correctfrac)


        columns.append(column_x)
        columns.append(column_data)


    page.addSection("MAPQ ROC",
                    """
                    <div id="mapq_roc"></div>%s""" % (util.makeExportDropdown("mapq_roc","")),
                    None,
                    "")

    page.addScript("""
var roc_plot = c3.generate({
bindto: '#mapq_roc',
size: { height: 500 },
data: {
  xs: %s,
  columns: %s
},
grid: {
  x: {
    show: true
  },
  y: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "log10(Wrongly Mapped)", position: "outer-middle" },
    tick: { fit: false, format: d3.format("10.3f") }
  },

  y: {
    label: { text: "log10(Correctly Mapped)", position: "outer-middle"},
    tick: { format: d3.format("10.3f") }
  }
},
point: {
  r: 5
},
legend: {
    position: "bottom",
    inset: {
        anchor: 'top-left',
        x: 20,
        y: 10,
        step: 2
    }
},
tooltip: {
	grouped: false
}});

""" % (json.dumps(xs), json.dumps(columns)))

def generatePrecisionRecallScatterPlot(self, page, test_objects):
	import json

	csv = "mapper,precision,recall\n"
	columns = []
	xs = {}
	groups = []

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None or test.getErrorCount():
			continue
		groups.append(test.getMapper().getTitle())
		columns.append([test.getMapper().getTitle()+"_x",round(result.recall, 4), 0])
		columns.append([test.getMapper().getTitle(),round(result.precision, 4)])
		xs[test.getMapper().getTitle()] = test.getMapper().getTitle() + "_x"

		csv += "%s,%.4f,%.4f\n" % (test.getMapper().getTitle(),result.precision,result.recall)

	csv_filename = self.writeCSV("precision_recall",csv)

	page.addSection("Precision and Recall", """<div id="plot_pr"></div>%s""" % util.makeExportDropdown("plot_pr",csv_filename) )
	page.addScript("""
var chart = c3.generate({
bindto: '#plot_pr',
size: { height: 500 },
data: {
  xs: %s,
  columns: %s,
  type: 'scatter',
},
grid: {
  x: {
    show: true
  },
  y: {
    show: true
  }
},
axis: {
  x: {
    label: { text: "Recall", position: "outer-middle" },
    tick: { fit: false, format: d3.format("10.3f") }
  },

  y: {
    label: { text: "Precision", position: "outer-middle"},
    tick: { format: d3.format("10.3f") }
  }
},
point: {
  r: 5
},
legend: {
	position: "bottom",
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
});""" % (json.dumps(xs), json.dumps(columns)))


def generateResourcePlot(self, page, test_objects, measure):
	import json

	if measure == "runtime":
		columns = [["Runtime/mio. reads"]]
		title = "Runtime [min/mio. reads]"
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

	csv = "mapper,%s\n" % measure

	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		result = test.getRunResults()
		if result == None or test.getErrorCount():
			continue

		groups.append(test.getMapper().getTitle())
		try:
			if measure == "runtime":
				columns[0].append(round( (result.maptime / 60.0) * (1000000.0/result.total), 3))
			elif measure == "memory":
				columns[0].append(round(result.memory / (1000 * 1000)))
			elif measure == "corrects":
				columns[0].append(round((result.correct) / result.maptime, 3))
		except ZeroDivisionError:
			columns[0].append(0)

		csv += "%s,%f\n" % (test.getMapper().getTitle(),columns[0][-1])

	csv_filename = self.writeCSV(measure,csv)

	page.addSection(section_title, """<div id="plot_resource_%s"></div>%s""" % (measure,util.makeExportDropdown("plot_resource_%s"%measure,csv_filename)))
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


def generateMappingQualityOverview(self, page, test_objects):
	import json

	csv_rating = "mapper,mapq_threshold,filtered_wrong_per_filtered_correct\n"
	csv_distribution = "mapper,mapq_value,read_count\n"

	data = []
	data_dist = []
	x_values_dist = []
	for test in sorted(test_objects, key=lambda k: k.getMapper().getTitle()):
		column = [test.getMapper().getTitle()]
		column_dist = [test.getMapper().getTitle()]
		results = test.getRunResults()

		if results == None or test.getErrorCount():
			continue

		x_values_dist = []

		mapqs = sorted(results.mapq_cumulated)
		for curr in mapqs:
			lost_correct = (results.correct - results.mapq_cumulated[curr]["correct"])
			lost_wrong = (results.wrong - results.mapq_cumulated[curr]["wrong"])
			if curr < 30 or (curr < 100 and curr%10==0) or curr%20==0 or curr==255:
				try:
					column.append(round(lost_wrong / float(lost_correct), 4))
				except ZeroDivisionError:
					column.append(0)

				
				if curr <= 255:
					column_dist.append(results.mapq_cumulated[curr]["correct"]+results.mapq_cumulated[curr]["wrong"]  )
				else:
					column_dist.append(0)

				x_values_dist.append(curr)

			csv_rating += "%s,%d,%.4f\n" % (test.getMapper().getTitle(),curr,column[-1])
			csv_distribution += "%s,%d,%d\n" % (test.getMapper().getTitle(),curr,column_dist[-1])

		data.append(column)
		data_dist.append(column_dist)

	data.append(["x"]+x_values_dist)
	data_dist.append(["x"]+x_values_dist)

	csv_filename_rating = self.writeCSV("mapq_rating",csv_rating)
	csv_filename_distribution = self.writeCSV("mapq_distribution",csv_distribution)

	page.addSection("Mapping Quality",
					"""<div id="plot_mapq_rating"></div>%s<p>&nbsp;</p><div id="plot_mapq_dist"></div>%s""" % (util.makeExportDropdown("plot_mapq_rating",csv_filename_rating), util.makeExportDropdown("plot_mapq_dist",csv_filename_distribution)),
					None,
					"This section represents an overview of the distribution of mapping quality values for all mappers. A detailed evaluation of mapping qualities for specific mappers can be found on the respective mapper results page (accessible using the navigation on top). The first plot rates each mapping quality threshold (0-255) by comparing the numbers of wrongly and correctly mapped reads that would be removed due to falling under the threshold. The second plot shows the total number of mapped reads for each mapping quality threshold (all reads with a mapping quality value smaller or equal to the threshold).")
	page.addScript("""
var chart = c3.generate({
    bindto: '#plot_mapq_rating',
    size: {
      height: 500
    },
    data: {
      x: 'x',
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
		show:true
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
      x: 'x',
      columns: %s,
      type: 'step'
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
        label: {text: "Number of Reads Mapped", position: "outer-middle"}
      }
    },
    legend: {
		show:true
    },
    point: {
    	show: false
    }
});""" % (json.dumps(data_dist)) )


def generateDataSetInfo(self,page,test):
	import json

	test_name = self.internal_name
	self.enterWorkingDirectory()

	html = "This section contains information on the benchmark data set. <center><h4>Simulation Overview</h4></center>"
	html += "<div class=\"table-responsive\"><table class=\"table table-striped\">"
	html += "<tbody>"

	test_input_type = test._("input_info:type")

	input_type_description = "Unknown"
	if test_input_type == "simulated_teaser":
		input_type_description = "Simulated data set (created using Teaser)"
	elif test_input_type == "simulated_custom":
		input_type_description = "Simulated data set (imported)"
	elif test_input_type == "real":
		input_type_description = "Real data / no gold standard"

	html += "<tr>"
	html += "<th width=\"25%\">Input Data Source</th>"
	html += "<td>%s</td>" % input_type_description
	html += "</tr>"


	if test_input_type == "simulated_teaser":
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
		html += "<th>Reads by Edit Distance</th>"
		html += """<td>The edit distance of a read is calculated as the total number of bases that are different to the reference. This includes mutations and sequencing errors.<div id="plot_edit_distr"></div></td>"""
		html += "</tr>"

		html += "</tbody>"
		html += "</table></div>"

		html += "<center><h4>Simulation Details</h4></center>"
		html += "<small><div class=\"table-responsive table-sm\"><table class=\"table table-striped table-sm\">"
		html += "<tbody>"
		html += "<tr>"
		html += "<th width=\"25%\">Subsampling enabled</th>"
		html += "<td>%s</td>" % util.yes_no(test._("input_info:sampling"))
		html += "</tr>"
		html += "<tr>"
		html += "<th>Simulator</th>"
		html += "<td>%s</td>" % str(test._("input_info:simulator"))
		html += "</tr>"

		if test._("input_info:sampling"):
			html += "<tr>"
			html += "<th>Sampling ratio</th>"
			html += "<td>%.3f</td>" % float(test._("input_info:sampling_ratio",-1))
			html += "</tr>"
			html += "<tr>"
			html += "<th>Sampling region length</th>"
			html += "<td>%d</td>" % int(test._("input_info:sampling_region_len",-1))
			html += "</tr>"

		max_nonzero = max(sorted(test.getRunResults().reads_by_edit_distance)) if len(test.getRunResults().reads_by_edit_distance) else 0

		data_dist_edit=[["Percentage of Reads"]+[(test.getRunResults().reads_by_edit_distance[i] if i in test.getRunResults().reads_by_edit_distance else 0)/float(test.getRunResults().total) for i in range(max_nonzero)]]

		page.addScript("""
	var chart = c3.generate({
	bindto: '#plot_edit_distr',
	size: {
	  height: 200
	},
	data: {
	  columns: %s,
	  type: "bar",
	  colors: {
			"Percentage of Reads": d3.rgb('#FF7F0E')
	  }
	},
	grid: {
	  y: {
		show: true
	  }
	},
	axis: {
	  x: {
		label: {text: "Edit Distance", position: "outer-middle"}
	  },

	  y: {
		label: {text: "Percentage of Reads [%%]", position: "outer-middle"},
				tick: {
				  format: d3.format(".3%%")
				}
	  }
	},
	legend: {
				show:false
	},
	point: {
		show: false
	}
	});""" % json.dumps(data_dist_edit))

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

	html += "</tbody>"
	html += "</table></div></small>"

	self.restoreWorkingDirectory()
	page.addSection("Data Set", html, None, "")



def report_overview(self, gen, page, test_objects):
	page.addScript("""$(document).ready(function() {
    $('#test_list').dataTable({
    "bPaginate": false,
    "bFilter": false,
    "bInfo": false,
    "order": [[ 3, "desc" ]]
  });
} );

window.onload = function () {$('.selectpicker').selectpicker();}""")

	config = self.mate.config

	# mapper_options = ""
	# for mapper_id in sorted(config["mappers"]):
	# 	if "title" in config["mappers"][mapper_id]:
	# 		mapper_title = config["mappers"][mapper_id]["title"]
	# 	else:
	# 		mapper_title = mapper_id

	# 	mapper_options += """<optgroup label="%s">""" % mapper_title
	# 	mapper_options += """<option value="m%s" selected>%s - Default</option>""" % (mapper_id, mapper_title)

	# 	if "parameters" in config:
	# 		for parameter_id in sorted(config["parameters"]):
	# 			if config["parameters"][parameter_id]["mapper"] != mapper_id:
	# 				continue

	# 			if "title" in config["parameters"][parameter_id]:
	# 				param_title = config["parameters"][parameter_id]["title"]
	# 			else:
	# 				param_title = parameter_id
	# 			mapper_options += """<option value="p%s">%s - %s</option>""" % (
	# 				parameter_id, mapper_title, param_title)


	# page.setSidebarFooter("""
	# <hr>
	# <div class="container-fluid">
	# 	Mapping Quality Threshold: <input type="range" name="mq_select" min="0" max="255"><br/>
	#        Mappers: <select class="selectpicker" name="mappers" id="mappers" data-width="100%" multiple>
	#           """ + mapper_options + """
	#        </select>
	# </div>""")

	generateOverallScatterPlot(self, page, test_objects)
	generateDataSetInfo(self, page, test_objects[0])
	generateMappingStatisticsPlot(self, page, test_objects)
	generateEditDistancePlot(self, page, test_objects)
	generateMappingQualityOverview(self, page, test_objects)
	generateROCPlot(self, page, test_objects)
	generatePrecisionRecallScatterPlot(self, page, test_objects)
	generateResourcePlot(self, page, test_objects, "corrects")
	generateResourcePlot(self, page, test_objects, "runtime")
	generateResourcePlot(self, page, test_objects, "memory")
	
	return ""
