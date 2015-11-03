#!/usr/bin/env python

import sys
if len(sys.argv) < 3:
	print("Usage: rdiff.py <Criterion> <a_reads.csv> [<b_reads.csv>, <c_reads.csv>, ...] ")
	print("Criterion examples:")
	print("   a.ok and b.ok")
	print("   a.ok and not b.ok")
	print("   a.ok != b.ok")
	print("   not a.ok and a.reason=='reverse'")
	print("   [not a.ok,a.reason]                        (Output failure reason for all failed reads)")
	print("   [not a.ok and not b.ok,a.reason==b.reason] (For each failed pair, output if failure reasons were equal)")
	print("   a.ok and b.ok and c.ok and not d.ok")
	print("Failure reasons: position, region, unmapped, not_found, not_found_comparison")
	print("Output: List of matched read qnames (default)")
	raise SystemExit


criterion = sys.argv[1]
handles = [open(f,"r") for f in sys.argv[2:]]

for h in handles:
	h.readline()

class Object:
	pass

def next_read(handles):
	lines=[h.readline() for h in handles]

	if sum([len(l.strip()) for l in lines]) == 0:
		return False

	qname_counts={}
	for hi, l in enumerate(lines):
		parts=l.split(",")
		if len(parts) < 3:
			return True

		qname = parts[0]
		if not qname in qname_counts:
			qname_counts[qname]=0

		qname_counts[qname]+=1


	if len(qname_counts)==1 and qname_counts.itervalues().next()==len(lines):
		globs={}

		for hi, l in enumerate(lines):
			parts=l.split(",")

			symbol = chr(ord("a")+hi)
			obj=Object()
			obj.ok = parts[1].strip()=="pass"
			obj.fail = not obj.ok
			obj.reason = parts[2].strip()
			obj.qname = parts[0].strip()
			globs[symbol]=obj

		result = eval(criterion,globs)

		if result==0 or result==1:
			if result:
				print(qname_counts.iterkeys().next())
		else:
			if result[0]:
				print(result[1])

		return True


	else:
		return True


while next_read(handles):
	pass