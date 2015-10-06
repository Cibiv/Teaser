function escapeRegExp(str) {
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}

function exportSVG(id)
{
	var tmp = document.getElementById(id);
	var svg = tmp.getElementsByTagName("svg")[0];
	var serializer = new XMLSerializer();
	var source = serializer.serializeToString(svg);
	if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
	    source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
	}
	if(!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)){
	    source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
	}
	source = '<?xml version="1.0" standalone="no"?>\r\n' + source;

	//Inline C3 styles to make SVG independent
	search=[];
	replace=[];

	search.push('style="visibility: visible; opacity: 1;"');
	replace.push('style="visibility: visible; opacity: 1; fill: none; stroke:#000;"');

	search.push('style="text-anchor: middle; display: block;"');
	replace.push('style="text-anchor: middle; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="text-anchor: middle;"');
	replace.push('style="text-anchor: middle; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="text-anchor: end;"');
	replace.push('style="text-anchor: end; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="text-anchor: middle; display: block;"');
	replace.push('style="text-anchor: middle; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="text-anchor: start;"');
	replace.push('style="text-anchor: start; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="pointer-events: none;"');
	replace.push('style="pointer-events: none; display: block; fill: #000; stroke: none; font: 12px Helvetica, sans-serif;"');

	search.push('style="text-anchor: end;"');
	replace.push('style="text-anchor: end; display: block; fill: #000; stroke: none; font: 13px Helvetica, sans-serif;"');

	search.push('style="overflow: hidden;"');
	replace.push('style="overflow: hidden; font: 13px Helvetica, sans-serif;"');

	search.push('style="opacity: 1;"');
	replace.push('style="opacity: 1; stroke: #aaa; stroke-dasharray: 3 3;"');

	search.push('visibility: hidden;');
	replace.push('visibility: hidden; display: none;');

	search.push('<line class="c3-ygrid"');
	replace.push('<line class="c3-ygrid" style="opacity: 1; stroke: #aaa; stroke-dasharray: 3 3;"');

	search.push('style="opacity: 1; pointer-events: none;"');
	replace.push('style="opacity: 1; pointer-events: none; fill: none;"');

	search.push('class="c3-legend-background"');
	replace.push('class="c3-legend-background" style="opacity: 0.75; fill: white; stroke: lightgray; stroke-width: 1;"');

	for (var i = 0; i < search.length; i++) {
	    source=source.replace(new RegExp(escapeRegExp(search[i]),'g'),replace[i]);
	}

	source  = source.replace(')" style="visibility: visible;"',')" style="visibility: hidden; display: none;"');

	//convert svg source to URI data scheme.
	var url = "data:image/svg+xml;charset=utf-8,"+encodeURIComponent(source);

	//set url value to a element's href attribute.
	//document.getElementById("export_link").href = url;
	window.open(url);
	console.log(url);
}