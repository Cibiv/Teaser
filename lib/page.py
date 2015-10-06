class Page:
	def __init__(self):
		self.nav = []
		self.sections = []
		self.html_data = ""
		self.html_scripts = ""
		self.html_styles = ""
		self.html_footer = ""
		self.html_sidebar_footer =""
		self.nav_right = ""
		self.nav_separators = True
		self.enable_sidebar = True

	def addSection(self, title, content, footer=None, description=None, container=True):
		self.sections.append({"title": title, "content": content, "description":description, "footer": footer, "container":container})

	def addSectionFront(self, title, content, footer=None, description=None, container=True):
		self.sections = [{"title": title, "content": content, "description":description, "footer": footer, "container":container}] + self.sections

	def addNav(self, nav_list, active_title=""):
		self.nav.append({"dropdown": nav_list, "active": active_title})

	def enableNavSeparators(self,enable):
		self.nav_separators=enable

	def addScript(self, script):
		self.html_scripts += script + "\n"

	def addStyle(self, style):
		self.html_styles += style + "\n"

	def setNavRight(self, nav):
		self.nav_right = nav

	def setSidebarFooter(self, html):
		self.html_sidebar_footer = html

	def enableFullscreenSections(self):
		self.addScript("""resizePanels=function (){$(".panel-body").css( "min-height", $( window ).height() - 215 );};
        $(document).ready(resizePanels);
        $(window).resize(resizePanels);""")

	def enableSidebar(self,enable):
		self.enable_sidebar = enable

	def setFooter(self,footer):
		self.html_footer = footer

	def html(self):
		html_nav = ""

		i=0

		for nav in self.nav:
			if i>0 and self.nav_separators:
				html_nav += """<li><a href="#" class="separator"><span class="glyphicon glyphicon-chevron-right" aria-hidden="true"></span></a></li>"""

			dropdown = nav["dropdown"]
			if len(dropdown) == 1:
				html_nav += """<li><a href="%s">%s</a></li>""" % (dropdown[0]["link"], dropdown[0]["title"])
			else:
				html_nav += """<li class="dropdown">"""
				html_nav += """<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">%s<span class="caret"></span></a>""" % \
							nav["active"]
				html_nav += """<ul class="dropdown-menu" role="menu">"""

				for element in dropdown:
					html_nav += """<li><a href="%s">%s</a></li>""" % (element["link"], element["title"])

				html_nav += "</ul>"
				html_nav += "</li>"

			i+=1

		html_section_list = ""
		html_section_bodies = ""
		index = 0
		for s in self.sections:
			if index == 0:
				html_section_list += """<li class="active">"""
			else:
				html_section_list += """<li>"""

			html_section_list += """<a href="#section%d">%s</a></li>""" % (index + 1, s["title"])
			# html_section_bodies += """<section id="section%d"><hr><h3>%s</h3>%s</section>"""%(index+1,s["title"],s["content"])

			if s["description"] != None:
				description="<p>%s</p>"%s["description"]
			else:
				description=""

			if s["container"]:
				panel = """<div class="panel panel-default"><div class="panel-heading">%s</div><div class="panel-body">%s%s</div>""" % (
					s["title"], description, s["content"])

				if s["footer"] != None:
					panel += """<div class="panel-footer">%s</div>""" % s["footer"]

				panel += "</div>"
			else:
				panel=s["content"]

			html_section_bodies += """<section id="section%d">%s</section>""" % (index + 1, panel)

			index += 1

		html_section_bodies += """<p>%s</p><div style="margin:300px; height:300px;">&nbsp;</div>"""%self.html_footer

		head = self.page_template_head % (self.html_styles)

		if not self.enable_sidebar:
			sidebar = ""
			offset = " col-sm-offset-2 col-md-offset-1 "
		else:
			sidebar = self.page_template_sidebar % (html_section_list, self.html_sidebar_footer)
			offset = " col-sm-offset-3 col-md-offset-2 "

		body = self.page_template_body % (html_nav, self.nav_right, sidebar, offset, html_section_bodies)
		footer = self.page_template_footer % (self.html_data, self.html_scripts)

		return head + body + footer

	page_template_head = """
<!DOCTYPE html>
<meta charset="utf-8">
<html lang="en">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>Teaser - Rapid Personalized Benchmarks for NGS Read Mapping</title>
    <link rel="stylesheet" href="http://teaser.cibiv.univie.ac.at/static/bootstrap/css/bootstrap.min.css">
    <link rel="stylesheet" href="http://teaser.cibiv.univie.ac.at/static/DataTables-1.10.8/media/css/jquery.dataTables.css">
    <link rel="stylesheet" href="http://teaser.cibiv.univie.ac.at/static/c3/c3.css">
    <link rel="stylesheet" href="http://teaser.cibiv.univie.ac.at/static/extensions/bootstrap-select.min.css">
    <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <style>
body {
  padding-top: 60px;
  position: relative;
}

.sub-header {
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}


.sidebar {
  display: none;
}

@media (min-width: 768px) {
  .sidebar {
    position: fixed;
    top: 51px;
    bottom: 0;
    left: 0;
    z-index: 1000;
    display: block;
    padding: 20px;
    overflow-x: hidden;
    overflow-y: auto; /* Scrollable contents if viewport is shorter than content. */
    background-color: #f5f5f5;
    border-right: 1px solid #eee;
  }
}

.nav-sidebar {
  margin-right: -21px;
  margin-bottom: 20px;
  margin-left: -20px;
}
.nav-sidebar > li > a {
  padding-right: 20px;
  padding-left: 20px;
}

.nav-sidebar > .active > a,
.nav-sidebar > .active > a:hover,
.nav-sidebar > .active > a:focus {
  color: #fff;
  background-color: #428bca;
}

a.separator
{
color:#777777;
}

a.separator:hover
{
color:#777777;
}

.main {
  padding: 20px;
}
@media (min-width: 768px) {
  .main {
    padding-right: 40px;
    padding-left: 40px;
  }
}
.main .page-header {
  margin-top: 0;
}

.placeholders {
  margin-bottom: 30px;
  text-align: center;
}
.placeholders h4 {
  margin-bottom: 0;
}
.placeholder {
  margin-bottom: 20px;
}
.placeholder img {
  display: inline-block;
  border-radius: 50%%;
}

section {
    padding-top: 60px;
    margin-top: -60px;
}

.bar {
  fill: steelblue;
}

.bar:hover {
  fill: brown;
}

.axis {
  font: 10px sans-serif;
}

.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}

.x.axis path {
  display: none;
}

.main-container
{
   margin: 0 auto;
   max-width: 1300px;
}

%s
    </style>
  </head>
"""

        page_template_sidebar = """
        <div class="col-sm-3 col-md-2 sidebar">
          <div id="sidebar">
          <ul class="nav nav-sidebar">
            %s
          </ul>
          %s
          </div>
        </div>""" 


	page_template_body = """
<body data-spy="scroll" data-target="#sidebar">
    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container-fluid">
        <div class="navbar-header">
          <a class="navbar-brand" href="/">Teaser</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
           %s
          </ul>
          <div class="nav navbar-nav navbar-right" style="padding:5px;">
           %s
          </div>
        </div>
      </div>
    </nav>

    <div class="container-fluid main-container">
      <div class="row">
        %s
        <div class="col-sm-9 %s col-md-10 main" id="content">
            %s
        </div>
      </div>
    </div>
"""

	page_template_footer = """
%s
<script src="http://teaser.cibiv.univie.ac.at/static/js/d3.v3.min.js"></script>
<script src="http://teaser.cibiv.univie.ac.at/static/c3/c3.js"></script>
<script src="http://teaser.cibiv.univie.ac.at/static/js/jquery.js"></script>
<script src="http://teaser.cibiv.univie.ac.at/static/js/svgexport.js"></script>
<script>
%s
</script>
<script src="http://teaser.cibiv.univie.ac.at/static/bootstrap/js/bootstrap.min.js"></script>
<script type="javascript">$('#content').scrollspy();</script>
<script src="http://teaser.cibiv.univie.ac.at/static/extensions/bootstrap-select.min.js"></script>

<script src="http://teaser.cibiv.univie.ac.at/static/DataTables-1.10.8/media/js/jquery.dataTables.js"></script>
<script src="http://teaser.cibiv.univie.ac.at/static/extensions/dataTables.bootstrap.js"></script>
</body>
</html>
"""
