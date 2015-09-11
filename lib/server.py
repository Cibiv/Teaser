#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.options
import yaml

from lib import page

Page = page.Page


class Home(tornado.web.RequestHandler):
	def get(self):
		instance.pollJobs()

		page = Page()

		page.setFooter("Copyright &copy; 2015, CIBIV.")

		page.addSection("Home", """

    <div class="jumbotron" style="border-radius:10px;">
      <div class="container">
        <h1>Teaser</h1>
        <p>Rapid Personalized Benchmarks for NGS Read Mapping</p>
        <p><a href="define" class="btn btn-success" role="button"><span class="glyphicon glyphicon-arrow-right" aria-hidden="true"></span> Start a mapper benchmark now</a> <a href="static/dataset_gallery" class="btn btn-info" role="button">View Example Report</a> <a href="http://github.com/cibiv/teaser/" class="btn btn-info" role="button">Visit the Wiki</a></p>
      </div>
    </div>

        <div class="container-fluid">
			<div class="row-fluid" align="center">
				<div class="col-md-3"><h2>Find</h2> <p>...a suitable mapper for your NGS application within minutes</p></div>
				<div class="col-md-3"><h2>Identify</h2> <p>...the right mapping quality thresholds for filtering</p></div>
				<div class="col-md-3"><h2>Optimize</h2> <p>...mapper parameters for accuracy or throughput</p></div>
				<div class="col-md-3"><h2>Compare</h2> <p>...simulation and real data results</p></div>
			</div>
        </div>
		<br>
		<br>
		<br>
		""", "", "", False)

		page.addStyle("""
		div.featurebox
		{
		padding:10px;
		background-color:#CCCCCC;
		margin-left:10px;
		margin-right:10px;
		margin-top:10px;
		margin-bottom:10px;
		border:solid 1px black;
        -webkit-border-radius: 5px;
        -moz-border-radius: 5px;
        border-radius: 5px;
		}
		""")

		if config["teaser"]["server"]["news"] != "":
			page.addSection("Update News", config["teaser"]["server"]["news"])

		page.addNav([{"title": "CIBIV", "link": "http://www.cibiv.at"}])
		page.addNav([{"title": "CSHL", "link": "http://www.cshl.edu"}])
		page.addNav([{"title": "Wiki", "link": "https://github.com/Cibiv/Teaser"}])
		page.enableNavSeparators(False)
		page.enableSidebar(False)

		recent_html = ""
		recent_configs = []
		for rid in os.listdir("reports"):
			if not os.path.isdir("reports/%s" % rid):
				continue

			report_config_filename = "reports/%s/config.yaml" % rid
			try:
				report_config = yaml.load(open(report_config_filename, "r"))
				recent_configs.append(report_config)
			except Exception as e:
				#print("Failed to load report config from %s: %s"%(report_config_filename,str(e)))
				pass

		max_i = 10
		i = 0
		for config_ in sorted(recent_configs, key=lambda k: k["meta_timestamp"], reverse=True):
			test_name = list(config_["teaser"]["tests"].keys())[0]
			test_config = config_["teaser"]["tests"][test_name]
			reference_name, reference_ext = os.path.splitext(test_config["reference"])

			if not "type" in test_config or test_config["type"] == "simulated_teaser":
				recent_html += "<tr><td><a href=\"reports/%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (test_name, test_name, reference_name, datetime.datetime.fromtimestamp(int(config_["meta_timestamp"])).strftime('%Y-%m-%d %H:%M:%S'), str(test_config["platform"]), "paired-end" if test_config["paired"] else "single-end", str(test_config["read_length"]))
			else:
				recent_html += "<tr><td><a href=\"reports/%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (test_name, test_name, reference_name, datetime.datetime.fromtimestamp(int(config_["meta_timestamp"])).strftime('%Y-%m-%d %H:%M:%S'), "Unknown", "paired-end" if test_config["paired"] else "single-end", "Unknown")
			i += 1
			if i >= max_i:
				break

		page.addSection("Recent Benchmarks", """<div class="table-responsive"><table class=table table-striped">
		<thead>
		<tr>
		<th>Teaser Accession</th>
		<th>Organism</th>
		<th>Date</th>
		<th>Platform</th>
		<th>Library</th>
		<th>Read Length</th>
		</tr>
		</thead>
		<tbody>
		%s
		</tbody>
		</table></div>
		""" % recent_html)

		page.addSection("Citation", """If you use Teaser to optimize read mapping in your study, please consider citing: Moritz Smolka, Philipp Rescheneder, Michael C Schatz, Arndt von Haeseler, Fritz J Sedlazeck Teaser: Individualized benchmarking and optimization of read mapping results for NGS data. First published online September 1, 2015. bioRxiv doi: http://dx.doi.org/10.1101/025858""")

		if config["teaser"]["server"]["send_usage_information"]:
			page.addScript("""
	  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
	  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
	  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
	  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

	  ga('create', 'UA-66386566-1', 'auto');
	  ga('send', 'pageview');""")

		self.write(page.html())


class DefineJob(tornado.web.RequestHandler):
	def makeButton(self, type, selected_type, link):
		if not type in config["teaser"]["server"]["allowed_types"]:
			return "<br><i>Please download Teaser for this option</i>"

		if type == selected_type:
			return """<a href="#" class="btn btn-default" role="button" disabled>Selected</a>"""
		else:
			return """<a href="%s" class="btn btn-info" role="button">Choose</a>""" % link

	def getReferenceOptions(self):
		reference_extensions = [".fa", ".fasta", ".fas"]
		reference_ignore = ".sampled"
		reference_files = []
		for file in os.listdir(config["teaser"]["reference_directory"]):
			name, ext = os.path.splitext(file)
			if ext in reference_extensions and not reference_ignore in file:
				reference_files.append((file, name))

		return ["<option value=\"%s\"%s>%s</option>" % (filename, (" selected" if "D_melanogaster" in filename else ""), title) for filename, title in reference_files]

	def getFileOptions(self, file_extensions=[".fastq", ".fq"]):
		files = []
		for file in os.listdir(config["teaser"]["import_directory"]):
			name, ext = os.path.splitext(file)
			if ext in file_extensions:
				files.append(file)

		return ["<option value=\"%s\">%s</option>" % (filename, filename) for filename in files]

	def addSectionDataSource(self, page, type=""):
		button_teaser = self.makeButton("simulated_teaser", type, "/define")
		button_custom = self.makeButton("simulated_custom", type, "/define-custom")
		button_real = self.makeButton("real", type, "/define-real")

		page.addSection("Choose Data Source", """
			  To begin, choose the source of the NGS read data that mappers should be benchmarked for.<br><hr>
              <div class="container-fluid">
			     <div class="row-fluid" align="center">
				    <div class="col-md-4" style="border-right:2px solid grey;"><h3>New Simulation</h3> <p style="height:75px;"> Use Teaser to quickly define a simulated data set and benchmark mappers on it.</p><p>%s</p></div>
				    <div class="col-md-4" style="border-right:2px solid grey;"><h3>Existing Simulation</h2> <p style="height:75px;"> Provide a custom set of reads and gold standard alignment for benchmarking mappers.</p><p>%s</p></div>
				    <div class="col-md-4"><h3>Real Data</h3> <p style="height:75px;"> Provide real read data to benchmark mapped percentages and throughput of mappers.</p><p>%s</p></div>
			     </div>
              </div>
              <form method="post" role="form" action="submitjob" class="form-horizontal" name="mainForm" id="mainForm">
              <input type="hidden" name="type" value="%s">""" % (button_teaser, button_custom, button_real, type), """<div class="form-group"><a href="../" class="btn btn-warning" role="button">Cancel</a> <a href="#section2" class="btn btn-info" role="button">Next</a></div>""")

	def addSectionHaplotype(self, page):
		page.addSection("Data: Haplotype", """
        	This section covers key properties related to the organism that is the target of sequencing. If you do not find your desired reference sequence in the list, please download and place the uncompressed FASTA file in the <i>Teaser/references</i> directory.<br><hr>
			<div class="form-horizontal">
              <div class="form-group">
                <label for="reference" class="col-sm-2 control-label">Reference Genome</label>
                <div class="col-sm-4">
                  <select id="reference" class="form-control" name="reference">
                    """ + "\n".join(self.getReferenceOptions()) + """
                  </select>
                </div>
              </div>
			
              <div class="form-group">
                <label for="mutation_rate" class="col-sm-2 control-label">Mutation Rate</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="mutation_rate" name="mutation_rate" min="0" max="0.5" value="0.001" step="0.001">
                </div>
              </div>

              <div class="form-group">
                <label for="mutation_indel_frac" class="col-sm-2 control-label">Mutation Indel Fraction</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="mutation_indel_frac" name="mutation_indel_frac" min="0" max="1" value="0.3" step="0.001">
                </div>
              </div>

              <div class="form-group">
                <label for="mutation_indel_avg_len" class="col-sm-2 control-label">Mutation Indel Avg. Length</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="mutation_indel_avg_len" name="mutation_indel_avg_len" min="0" max="1000" value="1" step="1">
                </div>
              </div>


            </div>

            """, """<div class="form-group">
                <a href="#section1" class="btn btn-info" role="button">Back</a> <a href="#section3" class="btn btn-info" role="button">Next</a>  
              </div>""")

	def addSectionSequencing(self, page):
		page.addSection("Data: Sequencing", """
        	This section covers properties related to basic library preparation and sequencing.<br><hr>
        	<div class="form-horizontal">
              <div class="form-group">
                <label for="platform" class="col-sm-2 control-label">Sequencing Platform</label>
                <div class="col-sm-4">
                  <select id="platform" name="platform" class="form-control">
                    <option value="illumina">Illumina</option>
                    <option value="454">454</option>
                    <option value="ion_torrent">Ion Torrent</option>
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label for="read_length" class="col-sm-2 control-label">Read Length</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="read_length" name="read_length" size="1" min="22" max="10000" step="1" value="60">
                </div>
              </div>

              <div class="form-group">
                <label for="coverage" class="col-sm-2 control-label">Coverage</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="coverage" name="coverage" size="1" min="0.1" max="5" step="0.1" value="1">
                </div>
              </div>

              <div class="form-group">
                <label for="error_rate_mult" class="col-sm-2 control-label">Sequencing Error Multiplier</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="error_rate_mult" name="error_rate_mult" min="0" max="1000" step="0.01" value="1">
                </div>
              </div>

              <div class="form-group">
              <label class="col-sm-2 control-label">
              Library Type
              </label>
              <div class="radio">
                <label>
                  <input type="radio" name="paired" id="optionsRadios1" value="false" onClick="javascript:$('#insert_size').prop('disabled',true);" checked>
                  Single-End
                </label>
                <label>
                  <input type="radio" name="paired" id="optionsRadios2" value="true" onClick="javascript:$('#insert_size').prop('disabled',false);">
                  Paired-End
                </label>
              </div>
              </div>

              <div class="form-group">
                <label for="insert_size" class="col-sm-2 control-label">Insert Size</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="insert_size" name="insert_size" min="0" max="1000" step="1" value="100" disabled>
                </div>
              </div>

            </div>
            """, """<div class="form-group">
                <a href="#section2" class="btn btn-info" role="button">Back</a> <a href="#section4" class="btn btn-info" role="button">Next</a>
              </div>""")

	def addSectionEvaluation(self, page):
		mapper_options = ""
		for mapper_id in sorted(config["mappers"]):
			if "title" in config["mappers"][mapper_id]:
				mapper_title = config["mappers"][mapper_id]["title"]
			else:
				mapper_title = mapper_id

			mapper_options += """<optgroup label="%s">""" % mapper_title
			mapper_options += """<option value="m%s" selected>%s - Default</option>""" % (mapper_id, mapper_title)

			if "parameters" in config:
				for parameter_id in sorted(config["parameters"]):
					if config["parameters"][parameter_id]["mapper"] != mapper_id:
						continue

					if "title" in config["parameters"][parameter_id]:
						param_title = config["parameters"][parameter_id]["title"]
					else:
						param_title = parameter_id
					mapper_options += """<option value="p%s">%s - %s</option>""" % (parameter_id, mapper_title, param_title)

			mapper_options += """</optgroup>"""

		page.addSection("Evaluation", """
        	Finally, select the mappers and parameter sets that should be evaluated. Community-created parameter sets are available for download at: <a href="https://github.com/Cibiv/Teaser">https://github.com/Cibiv/Teaser</a>. <br><hr>
			<div class="form-horizontal">
               <div class="form-group">
                <label for="mappers" class="col-sm-2 control-label">Mappers and Parameter Settings</label>
                <div class="col-sm-4">
                    <select class="selectpicker" name="mappers" id="mappers" data-width="100%" multiple>
                       """ + mapper_options + """
                    </select>
                </div>
              </div>

              <div class="form-group">
                <label for="evaluator" class="col-sm-2 control-label">Alignment Evaluation Method</label>
                <div class="col-sm-4">
                  <select id="evaluator" class="form-control" name="evaluator">
                     <option value="1" selected>Position-based using gold standard</option>
                  </select>
                </div>
              </div>
 
              <div class="form-group">
                <label for="pos_threshold" class="col-sm-2 control-label">Position threshold (bp)</label>
                <div class="col-sm-4">
                  <select id="pos_threshold" class="form-control" name="pos_threshold">
                     <option value="-1" selected>Default (50% of read length)</option>
                     <option>0</option>
                     <option>5</option>
                     <option>25</option>
                     <option>50</option>
                     <option>200</option>
                     <option>500</option>
                     <option>1000</option>
                  </select>
                </div>
              </div>

            </div>
            """, """<div class="form-group">
                <a href="#section3" class="btn btn-info" role="button">Back</a> <button type="submit" class="btn btn-primary" id="submitButton" name="submitButton">Run Teaser</button> <a href="#section5" class="btn btn-info" role="button">Advanced Options</a>
              </div>""")

		page.addScript("""window.onload = function () {$('.selectpicker').selectpicker();}""")

	def addSectionAdvanced(self, page):
		page.addSection("Advanced", """
            The options below allow adjusting the resources used for evaluation and other advanced options. Please note that for large, i.e. complex mammalian, genomes simulation and mapping may require up to 16GB of memory.<br><hr>
			<div class="form-horizontal">
              <div class="form-group">
                <label for="threads" class="col-sm-2 control-label">Number of CPU cores to use</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="threads" name="threads" min="1" max="%d" value="%d" step="1">
                </div>
              </div>

              <div class="form-group">
                <label for="sub_max_memory" class="col-sm-2 control-label">Max. Mapper Memory Usage (MB)</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="sub_max_memory" name="sub_max_memory" min="1" max="%d" value="%d" step="1">
                </div>
              </div>

              <div class="form-group">
                <label for="sub_max_runtime" class="col-sm-2 control-label">Max. Mapper Runtime (s)</label>
                <div class="col-sm-2">
                  <input type="number" class="form-control" id="sub_max_memory" name="sub_max_runtime" min="60" max="%d" value="%d" step="1">
                </div>
              </div>

              <div class="form-group">
                <label for="simulator" class="col-sm-2 control-label">Simulator</label>
                <div class="col-sm-4">
                  <select id="simulator" class="form-control" name="simulator">
                    <option value="none">Choose Automatically</option>
                    <option value="mason">Mason (Illumina,454)</option>
                    <option value="dwgsim">DWGSIM (Illumina,454,Ion Torrent)</option>
                  </select>
                </div>
              </div>
            </div>
            """ % (config["teaser"]["server"]["max_threads"], config["teaser"]["server"]["default_threads"], config["teaser"]["server"]["max_memory"], config["teaser"]["server"]["default_memory"], config["teaser"]["server"]["max_runtime"], config["teaser"]["server"]["default_runtime"]), """<div class="form-group">
              <a href="#section4" class="btn btn-info" role="button">Back</a> <button type="submit" class="btn btn-primary" id="submitButton" name="submitButton">Run Teaser</button>
              </div></form>""")


class DefineJobTeaser(DefineJob):
	def get(self):
		page = Page()

		page.enableFullscreenSections()

		self.addSectionDataSource(page, "simulated_teaser")
		self.addSectionHaplotype(page)
		self.addSectionSequencing(page)
		self.addSectionEvaluation(page)
		self.addSectionAdvanced(page)

		page.setNavRight("""<a href="/" class="btn btn-warning" role="button">Back to Teaser Home</a>""")

		self.write(page.html())


class DefineJobCustom(DefineJob):
	def addSectionSelectData(self, page):
		page.addSection("Import Data Set", """
        	Teaser supports reads in FASTQ format and gold standard alignments in SAM format. First, place your data files in the <i>Teaser/import</i> directory. After refreshing this page, you will be able to select the files to import below. If you do not find your desired reference sequence in the list, please download and place the uncompressed FASTA file in the <i>Teaser/references</i> directory.<br><hr>
	        <div class="form-horizontal">
	          <div class="form-group">
	            <label for="reference" class="col-sm-2 control-label">Reference Genome</label>
	            <div class="col-sm-4">
	              <select id="reference" class="form-control" name="reference">
	                """ + "\n".join(self.getReferenceOptions()) + """
	              </select>
	            </div>
	          </div>

              <div class="form-group">
              <label class="col-sm-2 control-label">
              Library Type
              </label>
              <div class="radio">
                <label>
                  <input type="radio" name="paired" id="optionsRadios1" value="false" onClick="javascript:$('#reads2').prop('disabled',true);" checked>
                  Single-End
                </label>
                <label>
                  <input type="radio" name="paired" id="optionsRadios2" value="true" onClick="javascript:$('#reads2').prop('disabled',false);">
                  Paired-End
                </label>
              </div>
              </div>

              <div class="form-group">
                <label for="reads1" class="col-sm-2 control-label">Simulated Reads File (1)</label>
                <div class="col-sm-4">
                  <select id="reads1" class="form-control" name="reads1">
                    """ + "\n".join(self.getFileOptions()) + """
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label for="reads2" class="col-sm-2 control-label">Simulated Reads File (2)</label>
                <div class="col-sm-4">
                  <select id="reads2" class="form-control" name="reads2" disabled>
                    """ + "\n".join(self.getFileOptions()) + """
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label for="gold_standard" class="col-sm-2 control-label">Gold Standard Alignment File</label>
                <div class="col-sm-4">
                  <select id="gold_standard" class="form-control" name="gold_standard">
                    """ + "\n".join(self.getFileOptions([".sam"])) + """
                  </select>
                </div>
              </div>
            </div>

            """, """<div class="form-group">
                <a href="#section1" class="btn btn-info" role="button">Back</a> <a href="#section3" class="btn btn-info" role="button">Next</a>  
              </div>""")

	def get(self):
		page = Page()

		page.enableFullscreenSections()

		self.addSectionDataSource(page, "simulated_custom")
		self.addSectionSelectData(page)
		self.addSectionEvaluation(page)
		self.addSectionAdvanced(page)

		page.setNavRight("""<a href="/" class="btn btn-warning" role="button">Back to Teaser Home</a>""")

		self.write(page.html())


class DefineJobReal(DefineJob):
	def addSectionEvaluation(self, page):
		mapper_options = ""
		for mapper_id in sorted(config["mappers"]):
			if "title" in config["mappers"][mapper_id]:
				mapper_title = config["mappers"][mapper_id]["title"]
			else:
				mapper_title = mapper_id

			mapper_options += """<optgroup label="%s">""" % mapper_title
			mapper_options += """<option value="m%s" selected>%s - Default</option>""" % (mapper_id, mapper_title)

			if "parameters" in config:
				for parameter_id in sorted(config["parameters"]):
					if config["parameters"][parameter_id]["mapper"] != mapper_id:
						continue

					if "title" in config["parameters"][parameter_id]:
						param_title = config["parameters"][parameter_id]["title"]
					else:
						param_title = parameter_id
					mapper_options += """<option value="p%s">%s - %s</option>""" % (parameter_id, mapper_title, param_title)

			mapper_options += """</optgroup>"""

		page.addSection("Evaluation", """
        	Finally, select the mappers and parameter sets that should be evaluated. Community-created parameter sets are available for download at: <a href="https://github.com/Cibiv/Teaser">https://github.com/Cibiv/Teaser</a>. <br><hr>
			<div class="form-horizontal">
               <div class="form-group">
                <label for="mappers" class="col-sm-2 control-label">Mappers and Parameter Settings</label>
                <div class="col-sm-4">
                    <select class="selectpicker" name="mappers" id="mappers" data-width="100%" multiple>
                       """ + mapper_options + """
                    </select>
                </div>
              </div>

              <div class="form-group">
                <label for="evaluator" class="col-sm-2 control-label">Alignment Evaluation Method</label>
                <div class="col-sm-4">
                  <select id="evaluator" class="form-control" name="evaluator">
                     <option value="1" selected>Basic</option>
                  </select>
                </div>
              </div>
            </div>
            """, """<div class="form-group">
                <a href="#section2" class="btn btn-info" role="button">Back</a> <button type="submit" class="btn btn-primary" id="submitButton" name="submitButton">Run Teaser</button> <a href="#section4" class="btn btn-info" role="button">Advanced Options</a>
              </div>""")

		page.addScript("""window.onload = function () {$('.selectpicker').selectpicker();}""")

	def addSectionSelectData(self, page):
		page.addSection("Import Data Set", """
        	Teaser supports reads in FASTQ format. First, place your data files in the <i>Teaser/import</i> directory. After refreshing this page, you will be able to select the files to import below. If you do not find your desired reference sequence in the list, please download and place the uncompressed FASTA file in the <i>Teaser/references</i> directory.<br><hr>
	        <div class="form-horizontal">
	          <div class="form-group">
	            <label for="reference" class="col-sm-2 control-label">Reference Genome</label>
	            <div class="col-sm-4">
	              <select id="reference" class="form-control" name="reference">
	                """ + "\n".join(self.getReferenceOptions()) + """
	              </select>
	            </div>
	          </div>

              <div class="form-group">
              <label class="col-sm-2 control-label">
              Library Type
              </label>
              <div class="radio">
                <label>
                  <input type="radio" name="paired" id="optionsRadios1" value="false" onClick="javascript:$('#reads2').prop('disabled',true);" checked>
                  Single-End
                </label>
                <label>
                  <input type="radio" name="paired" id="optionsRadios2" value="true" onClick="javascript:$('#reads2').prop('disabled',false);">
                  Paired-End
                </label>
              </div>
              </div>

              <div class="form-group">
                <label for="reads1" class="col-sm-2 control-label">Simulated Reads File (1)</label>
                <div class="col-sm-4">
                  <select id="reads1" class="form-control" name="reads1">
                    """ + "\n".join(self.getFileOptions()) + """
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label for="reads2" class="col-sm-2 control-label">Simulated Reads File (2)</label>
                <div class="col-sm-4">
                  <select id="reads2" class="form-control" name="reads2" disabled>
                    """ + "\n".join(self.getFileOptions()) + """
                  </select>
                </div>
              </div>
            </div>

            """, """<div class="form-group">
                <a href="#section1" class="btn btn-info" role="button">Back</a> <a href="#section3" class="btn btn-info" role="button">Next</a>  
              </div>""")

	def get(self):
		page = Page()

		page.enableFullscreenSections()

		self.addSectionDataSource(page, "real")
		self.addSectionSelectData(page)
		self.addSectionEvaluation(page)
		self.addSectionAdvanced(page)

		page.setNavRight("""<a href="/" class="btn btn-warning" role="button">Back to Teaser Home</a>""")

		self.write(page.html())


class RedirectJob(tornado.web.RequestHandler):
	def get(self, jobid):
		try:
			with open("reports/" + jobid + "/index.html", "r") as h:
				if h.read().strip() == "INITIALIZING":
					raise
				else:
					self.redirect("/reports/" + jobid + "/")
		except:
			self.write("""<meta http-equiv="refresh" content="1">Please wait...""")


class SubmitJob(tornado.web.RequestHandler):
	def post(self):
		self.job_id = util.md5(str(int(time.time())) + self.get_argument('reference', ''))
		config_path, config = self.generateConfig()
		teaser = self.startTeaser(config_path)

		try:
			os.mkdir("reports/" + self.getJobId())
		except:
			pass

		with open("reports/" + self.getJobId() + "/index.html", "w") as handle:
			handle.write("INITIALIZING")
			handle.flush()
			handle.close()

		with open("reports/" + self.getJobId() + "/config.yaml", "w") as handle:
			handle.write(yaml.dump(config))
			handle.flush()
			handle.close()

		self.redirect("/redirect/" + self.getJobId())

		job = {"name": self.job_id, "process": teaser}
		instance.jobs.append(job)

		print("Started Teaser with config %s" % config_path)

	def generateConfig(self):
		head, tail = os.path.split(self.get_argument('reference', ''))
		name, ext = os.path.splitext(tail)

		pos_threshold = int(self.get_argument('pos_threshold', -1))
		if pos_threshold < 0:
			pos_threshold = int(self.get_argument('read_length', 60)) / 2

		config_ = {}
		config_["meta_timestamp"] = time.time()
		config_["include"] = ["base_teaser.yaml"]
		config_["report"] = {"name": self.getJobId()}
		config_["evaluation"] = {"pos_threshold": pos_threshold}
		config_["teaser"] = {}
		config_["teaser"]["tests"] = {}
		config_["threads"] = min(int(self.get_argument('threads', 1)), config["teaser"]["server"]["max_threads"])
		config_["sub_max_memory"] = min(int(self.get_argument('sub_max_memory', 16000)), config["teaser"]["server"]["max_memory"])
		config_["sub_max_runtime"] = min(int(self.get_argument('sub_max_memory', 16000)), config["teaser"]["server"]["max_runtime"])

		test = {}
		test["title"] = name
		test["reference"] = tail
		test["type"] = self.get_argument('type', 'simulated_teaser')
		test["paired"] = self.get_argument('paired', 'false') == 'true'

		if self.get_argument('type', '') == "simulated_teaser":
			test["read_length"] = int(self.get_argument('read_length', 60))
			test["mutation_rate"] = float(self.get_argument('mutation_rate', 0.001))
			test["mutation_indel_frac"] = float(self.get_argument('mutation_indel_frac', 0.3))
			test["mutation_indel_avg_len"] = float(self.get_argument('mutation_indel_avg_len', 1))
			test["error_rate_mult"] = float(self.get_argument('error_rate_mult', 1))
			test["platform"] = self.get_argument('platform', 'illumina')

			test["coverage"] = float(self.get_argument('coverage', 0))

			if self.get_argument('simulator', 'none') != "none":
				test["simulator"] = self.get_argument('simulator', 'none')

			if test["paired"]:
				test["insert_size"] = int(self.get_argument('insert_size', ''))

		else:
			if test["paired"]:
				test["import_read_files"] = [config["teaser"]["import_directory"] + "/" + self.get_argument('reads1', 'none'), config["teaser"]["import_directory"] + "/" + self.get_argument('reads2', 'none')]
			else:
				test["import_read_files"] = [config["teaser"]["import_directory"] + "/" + self.get_argument('reads1', 'none')]

			if "gold_standard" in self.request.arguments:
				test["import_gold_standard_file"] = config["teaser"]["import_directory"] + "/" + self.get_argument('gold_standard', 'none')

		config_["test_mappers"] = []
		config_["test_parameters"] = []

		if "mappers" in self.request.arguments:
			for mapper in self.request.arguments["mappers"]:
				if mapper[0] == "m":
					config_["test_mappers"].append(mapper[1:])
				elif mapper[0] == "p":
					config_["test_parameters"].append(mapper[1:])
				else:
					raise

		config_["teaser"]["tests"][self.getJobId()] = test

		config_path = "setups_generated/" + self.getJobId() + ".yaml"
		with open(config_path, "w") as yml:
			yml.write(yaml.dump(config_))
			yml.flush()
			yml.close()

		#print("Wrote config to %s" % config_path)
		return config_path, config_

	def startTeaser(self, config_path):
		cmd = config["teaser"]["server"]["framework_cmd"] % (config_path, self.job_id)
		print("Running Teaser using %s..." % cmd)
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		return proc

	def getJobId(self):
		return self.job_id


class MyStaticFileHandler(tornado.web.StaticFileHandler):
	def set_extra_headers(self, path):
		self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class TeaserServer:
	def __init__(self):
		self.jobs = []

	def main(self, wsgi=False):
		#args = sys.argv
		#args.append("--log_file_prefix=%s/logs/tornado.log" % util.getRootDir() )

		#print("Log file: %s/logs/tornado.log"%util.getRootDir())

		#tornado.options.parse_command_line(args)

		app = tornado.web.Application([("/", Home), ("/home", Home), ("/define", DefineJobTeaser), ("/define-custom", DefineJobCustom), ("/define-real", DefineJobReal), ("/submitjob", SubmitJob), (r'/reports/(.*)', MyStaticFileHandler, {'path': config["report"]["directory"], "default_filename": "index.html"}), (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': "static", "default_filename": "index.html"}), (r'/redirect/(.*)', RedirectJob)])

		if wsgi:
			print("Running as WSGI")
			app = tornado.wsgi.WSGIAdapter(app)
		else:
			print("Running as standalone HTTP server on port %d" % config["teaser"]["server"]["port"])
			app.listen(config["teaser"]["server"]["port"])
			tornado.ioloop.IOLoop.current().start()

		return app

	def pollJobs(self):
		for job in self.jobs:
			if not job["process"].poll():
				self.jobs.remove(job)


import os
import time
import subprocess
import shutil
import sys
import datetime


def deleteContents(dir, max_age_hours=24 * 365):
	try:
		if not os.path.exists(dir):
			os.mkdir(dir)
	except:
		return

	for file in os.listdir(dir):
		path = dir + "/" + file

		if file[0] == ".":
			continue

		try:
			file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(path))
			if datetime.datetime.now() - file_modified < datetime.timedelta(hours=max_age_hours):
				continue
		except:
			continue

		try:
			if os.path.isfile(path):
				os.remove(path)
			else:
				shutil.rmtree(path)
		except:
			pass


import logging

tornado.options.parse_command_line()

call_dir = os.getcwd()
root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../")
os.chdir(root_dir)

from lib import util

setCallDir = util.setCallDir
setRootDir = util.setRootDir
enterCallDir = util.enterCallDir
enterRootDir = util.enterRootDir

setCallDir(call_dir)
setRootDir(root_dir)

enterRootDir()
logging.getLogger("tornado.access").addHandler(logging.FileHandler("logs/server.access.log"))
logging.getLogger("tornado.application").addHandler(logging.FileHandler("logs/server.application.log"))
logging.getLogger("tornado.general").addHandler(logging.FileHandler("logs/server.general.log"))

deleteContents("setups_generated")
deleteContents("tests_generated")
deleteContents("reports")

config_file = "base_teaser.yaml"
if len(sys.argv) > 1:
	config_file = sys.argv[1]
config, original = util.loadConfig(config_file)

print("Root dir: %s" % root_dir)


#sys.stdout = open("logs/server.txt","w")
#sys.stderr = sys.stdout

# instance = TeaserServer()
# instance.main()
