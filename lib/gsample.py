#!/usr/bin/env python

import teaser
import random
import sys
import os
import json
import base64
import util

import intervaltree


def log(msg):
	sys.stderr.write(str(msg) + "\n")

def index(reference, fastindex_path = "tools/fastindex"):
	index_filename = reference + ".teaser.findex"
	contig_filename = reference + ".teaser.fcontig"

	try:
		index = json.loads(open(index_filename, "r").read())
		log("Loaded index from " + index_filename)
	except Exception as e:
		log("Indexing " + reference)
		if os.system(fastindex_path + " " + reference) != 0:
			raise Exception("Indexing failed")

		try:
			index = json.loads(open(index_filename, "r").read())
		except Exception as e:
			raise Exception("Could not read index file")

	return index


def index_legacy(reference):
	index_filename = reference + ".teaser.index"
	contig_filename = reference + ".teaser.contig"

	try:
		index = json.loads(open(index_filename, "r").read())
		log("Loaded index from " + index_filename)
		return index
	except Exception as e:
		log("Failed to load index from file")

	chunk_size = 8192

	seq = []
	seq_id = None
	internal_id = 1

	contig_pos = 0
	curr_contig_start = 0

	ref_handle = open(reference, "r")
	contig_handle = open(contig_filename, "w")

	chunk = True
	while chunk:
		chunk = ref_handle.read(chunk_size)

		i = 0
		while i < len(chunk):
			c = chunk[i]
			if c == "\n":
				i += 1
				continue

			if c == ">":
				i += 1
				id_buffer = ""
				while i < len(chunk) and chunk[i] != "\n":
					id_buffer += chunk[i]
					i += 1

				i += 1

				if i == len(chunk):
					break

				if seq_id != None:
					seq.append(
						{"id": seq_id, "start": curr_contig_start, "end": contig_pos, "internal_id": internal_id})
					internal_id += 1

				seq_id = id_buffer
				curr_contig_start = contig_pos

				#log("%s, start=%d" % (seq_id, contig_pos))
				continue
			else:
				contig_handle.write(c)
				contig_pos += 1

			i += 1

	if seq_id != None:
		seq.append({"id": id_buffer, "start": curr_contig_start, "end": contig_pos, "internal_id": internal_id})

	index = {"seqs": seq, "contig_len": contig_pos}

	log("Writing index to " + index_filename)
	open(index_filename, "w").write(json.dumps(index))

	return index


def generateDistribution(transition_probabilities):
	distr = []
	P = 0
	for new, p in transition_probabilities.iteritems():
		distr.append((new,P,P+p))
		P+=p

	return distr

def sampleDistribution(distribution):
	k=random.uniform(0,1)

	for new, start, end in distribution:
		if k>=start and k<end:
			return new
	return None

def methylate(base, transition_distributions):
	if base in transition_distributions:
		new = sampleDistribution(transition_distributions[base])

		if new != None:
			return new
		else:
			return base
	else:
		return base

def methylateSequence(seq, transition_distributions):
	new_seq = ""
	transitions=[]
	for i in range(len(seq)):
		new_base=methylate(seq[i],transition_distributions)
		new_seq+=new_base

		if new_base != seq[i]:
			transitions.append((i,seq[i],new_base))

	return new_seq,transitions

def downsample(index, contig_filename, downsampled_filename, region_count, target_len, single_contig=False, region_list=False, spacer_len=200, methylation={"enable":False}):
	if methylation["enable"]:
		transition_distributions = {"A":[],"C":[],"G":[],"T":[]}
		for base, transitions in methylation["rates"].iteritems():
			transition_distributions[base] = generateDistribution(transitions)

		methylation_info_handle = open(downsampled_filename+"_methylation_positions.tsv","w")
		methylation_base_count = 0

	rlist = False
	if region_list != False:
		rlist = []
		lines = open(region_list, "r").read().split("\n")
		for l in lines:
			if l.strip() == "" or len(l.split(",")) < 3:
				log("Ignoring CSV line: %s" % l)
				continue

			split = l.strip().split(",")
			r = {}
			chrom = split[0].split(" ")[0]

			for seq in index["seqs"]:
				if seq["id"].split(" ")[0] == chrom:
					r["seq"] = seq

			if not "seq" in r:
				log("Region not found in index: %s (%s)" % (chrom, l.strip()))
				continue

			log("Seq" + str(r["seq"]))

			r["start"] = r["seq"]["start"] + int(split[1])
			r["end"] = r["seq"]["start"] + int(split[2])

			rlist.append(r)
			rlist_idx = 0

		region_count = len(rlist)
		region_len = 0
	else:
		region_len = int(target_len / region_count)

	sampled_count = 0
	sampled_intervals = intervaltree.IntervalTree()
	sampled_info = []

	contig_handle = open(contig_filename, "r")
	downsampled_handle = open(downsampled_filename, "w")
	downsampled_pos = 0

	spacer = "N" * spacer_len
	min_region_distance = 0

	if single_contig:
		downsampled_handle.write(">contig\n")

	log("Sampling %d regions" % region_count)
	old_percent = 0

	while sampled_count < region_count:
		if rlist == False:
			start = random.randrange(0, index["contig_len"])

			if len(sampled_intervals[(start - min_region_distance):(start + region_len + min_region_distance)]) > 0:
				# log("Region start too close to already sampled region")
				continue

		else:
			if rlist_idx >= len(rlist):
				break

			r = rlist[rlist_idx]
			rlist_idx += 1
			start = r["start"]
			region_len = r["end"] - r["start"]
		# log("Sampling from rlist: %d, len %d"%(start,region_len))

		start_ok = True

		selected_region = None
		for seq in index["seqs"]:
			if start >= seq["start"] and start < seq["end"]:
				selected_region = seq

				# log("Selected seq "+str(seq))

				# Avoid sequence-overlapping samples
				if start + region_len >= seq["end"]:
					# log("Region would exceed sequence length")
					start_ok = False
					break

		if not start_ok:
			continue

		contig_handle.seek(start)

		sample_contig = contig_handle.read(region_len)
		n_only = True
		for c in sample_contig:
			if c.upper() != "N":
				n_only = False
				break

		sampled_intervals[start:(start + region_len)] = True
		if n_only:
			# log("Sampled region contained only Ns")
			continue

		if methylation["enable"]:
			sample_contig, transitions=methylateSequence(sample_contig,transition_distributions)

			#for pos, old, new in transitions:
			#	methylation_info_handle.write("%s\t%d\t%s\t%s\n"%(selected_region["id"].split(" ")[0], start - selected_region["start"] + pos, old, new))
				

		if not single_contig:
			downsampled_handle.write(">%s_%d\n" % (str(selected_region["internal_id"]), start - selected_region["start"]))
		downsampled_handle.write(sample_contig)

		sampled_info_entry = {"start": downsampled_pos, "end": downsampled_pos + region_len, "source": selected_region, "source_offset": (start - selected_region["start"])}

		if methylation["enable"]:
			sampled_info_entry["methylation"] = transitions
			methylation_base_count += len(sampled_info_entry["methylation"])
				

		sampled_info.append(sampled_info_entry)
		downsampled_pos += region_len + len(spacer)

		if not single_contig:
			downsampled_handle.write("\n")
		else:
			downsampled_handle.write(spacer)

		sampled_count += 1
		percent = int((10 * sampled_count) / region_count) * 10
		if percent != old_percent:
			log("%d%%" % percent)
			old_percent = percent

	if methylation["enable"]:
		methylation_info_handle.close()
		print("%d bases were transitioned due to methylation"%methylation_base_count)

	return sampled_info


def csample(infile, region_size, sample_fraction, spacer_len=200, fastindex_path="", methylation={"enable":False}, region_list_path=False):
	outfile=infile + ".sampled.%d.%d.%d%s.fasta" % (int(1/sample_fraction),region_size,spacer_len, ".m" if methylation["enable"] else "")
	outfile_index=outfile+".index"

	log("csample %s %d %f" % (infile, region_size, sample_fraction))

	if os.path.exists(outfile) and os.path.exists(outfile_index) and not methylation["enable"]:
		log("Sampled file exists, skip sampling")
		return outfile,outfile_index

	idx = index(infile,fastindex_path)
	total_size = int(float(sample_fraction) * idx["contig_len"])
	region_count = int(total_size / region_size)
	log("Sampling as contig: %d regions of size %d (pad %d), totalling %d base pairs" % (region_count, region_size, spacer_len, total_size))

	sampled_info = downsample(idx, infile + ".teaser.fcontig", outfile, int(region_count), int(total_size), True, region_list_path, spacer_len, methylation)
	open(outfile + ".index", "w").write(json.dumps(sampled_info))

	return outfile,outfile_index


def writeReadMethylationInfo(handle,methylation,qname,flag,pos,cigar):
	cigar_parts = util.parseCIGAR(cigar)
	start_pos = int(pos)
	end_pos = int(pos)

	for part, length in cigar_parts:
		if part in ["D","M","S","H"]:
			end_pos += length

	print(qname,methylation,start_pos,end_pos)

	for methylation_pos, old, new in methylation:
		if methylation_pos >= start_pos and methylation_pos <= end_pos:
			handle.write("%s\t%d\t%s\t%s\n"%(qname,methylation_pos-start_pos+2,old,new))

def compileReadMethylationInfo(methylation,qname,flag,pos,cigar):
	cigar_parts = util.parseCIGAR(cigar)
	start_pos = int(pos)
	end_pos = int(pos)

	for part, length in cigar_parts:
		if part in ["D","M","S","H"]:
			end_pos += length

	result=[]

	for methylation_pos, old, new in methylation:
		if methylation_pos >= start_pos and methylation_pos <= end_pos:
			result.append((methylation_pos-start_pos+2,old,new))

	return result

def ctranslate(reference_file, sampled_index_file, sam_file, target_file, fastindex_path="", methylation={"enable":False}):
	log("Translating SAM file coordinates (as contig)...")

	#if methylation["enable"]:
		#methylation_info_handle = open(sampled_index_file+".methylation.tsv","w")
		#print("Methylation handle: %s"%(sampled_index_file+".methylation.tsv"))


	idx = index(reference_file,fastindex_path)
	sampled_idx = json.loads(open(sampled_index_file, "r").read())

	sampled_tree = intervaltree.IntervalTree()
	for sampled in sampled_idx:
		sampled_tree[(sampled["start"]):(sampled["end"])] = sampled

	handle = open(sam_file, "r")
	out_handle = open(target_file, "w")
	wrote_header = False
	for line in handle:
		if line.startswith("@") or line.strip() == "":
			if line[:3] != "@SQ":
				out_handle.write(line)
			continue

		if not wrote_header:
			unique_seqs = {}
			for seq in idx["seqs"]:
				unique_seqs[seq["id"]] = seq
			for seqid in unique_seqs:
				seq = unique_seqs[seqid]
				out_handle.write("@SQ\tSN:%s\tLN:%d\n" % (seq["id"].split(" ")[0], seq["end"] - seq["start"]))
			wrote_header = True

		parts = line.split("\t")
		if len(parts) < 8:
			raise Exception

		read_pos = int(parts[3])

		source_sample_set = sampled_tree[read_pos]
		if len(source_sample_set) != 1:
			log("Warning: Len of source sample set = %d, read %s" % (len(source_sample_set), parts[0]))
			continue

		source_sample = source_sample_set.pop().data
		source_seq = source_sample["source"]

		if source_seq == None:
			raise "Source sequence could not be identified for aligned read"

		parts[2] = source_seq["id"].split(" ")[0]

		sample_pos = int(parts[3]) - source_sample["start"]

		adjusted_pos = int(parts[3]) - source_sample["start"] + source_sample["source_offset"]
		parts[3] = str(adjusted_pos)


		if "methylation" in source_sample:
			info=compileReadMethylationInfo(source_sample["methylation"],parts[0],parts[1],sample_pos,parts[5])
			parts[-1]=parts[-1].strip()
			parts.append("MT:"+json.dumps(info)+"\n")


		out_handle.write("\t".join(parts))


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: gsample.py")
		print(
			"  Downsample:                  sample <reference.fasta> <region size (mb)> <total sampled base count (mb)>")
		print(
			"                               psample <reference.fasta> <fraction of reference to sample in 500kb pieces>")
		print("  Downsample as contig:        csample <reference.fasta> <region count> <total sampled base count>")
		print("  Downsample as contig:        csample_list <reference.fasta> <region list csv file>")
		print("  Fix locations:               translate <reference.fasta> <in_alignment.sam>")
		print("  Fix locations as contig:     ctranslate <reference.fasta> <in_alignment.sam>")
		sys.exit()

	if sys.argv[1] == "sample":
		if len(sys.argv) < 5:
			print("Usage: gsample.py sample <reference.fasta> <region count> <total sampled base count>")
			sys.exit()

		infile = sys.argv[2]
		idx = index(infile)

		region_size = float(sys.argv[3]) * (1000 * 1000)
		total_size = float(sys.argv[4]) * (1000 * 1000)
		region_count = int(total_size / region_size)

		downsample(idx, infile + ".teaser.fcontig", infile + ".sampled.fasta", int(region_count), int(total_size))

	if sys.argv[1] == "psample":
		if len(sys.argv) < 4:
			print("Usage: gsample.py psample <reference.fasta> <fraction of reference to sample in 500kb pieces>")
			sys.exit()

		infile = sys.argv[2]
		frac = float(sys.argv[3])
		idx = index(iscrennfile)
		total_len = int(idx["contig_len"] * frac)
		region_count = total_len / (500 * 1000)
		region_count = max(region_count, 1)
		downsample(idx, infile + ".teaser.fcontig", infile + ".sampled.fasta", region_count, total_len)
		log("Downsampled %d regions totaling %d MB\n" % (region_count, total_len / (1000 * 1000)))

	if sys.argv[1] == "csample":
		if len(sys.argv) < 5:
			print("Usage: gsample.py csample <reference.fasta> <region size> <fraction to sample>")
			sys.exit()

		infile = sys.argv[2]
		idx = index(infile)

		region_size = int(sys.argv[3])
		total_size = int(float(sys.argv[4]) * idx["contig_len"])
		region_count = int(total_size / region_size)

		log("Sampling as contig: %d regions of size %d, totalling %d base pairs" % (
			region_count, region_size, total_size))

		sampled_info = downsample(idx, infile + ".teaser.fcontig", infile + ".sampled.fasta", int(region_count),
								  int(total_size), True)
		open(infile + ".sampled.fasta.index", "w").write(json.dumps(sampled_info))

	if sys.argv[1] == "csample_list":
		if len(sys.argv) < 4:
			print("Usage: gsample.py csample_list <reference.fasta> <region list csv file>")
			sys.exit()

		infile = sys.argv[2]
		idx = index(infile)

		region_list = sys.argv[3]

		log("Sampling as contig: List of regions %s." % region_list)

		sampled_info = downsample(idx, infile + ".teaser.fcontig", infile + ".sampled.fasta", 0, 0, True, region_list)
		open(infile + ".sampled.fasta.index", "w").write(json.dumps(sampled_info))

	if sys.argv[1] == "translate":
		if len(sys.argv) < 4:
			print("Usage: gsample.py translate <reference.fasta> <in_alignment.sam>")
			sys.exit()

		log("Translating SAM file coordinates...")

		idx = index(sys.argv[2])

		handle = open(sys.argv[3], "r")
		wrote_header = False
		for line in handle:
			if line.startswith("@") or line.strip() == "":
				if line[:3] != "@SQ":
					sys.stdout.write(line)
				continue

			if not wrote_header:
				unique_seqs = {}
				for seq in idx["seqs"]:
					unique_seqs[seq["id"]] = seq
				for seqid in unique_seqs:
					seq = unique_seqs[seqid]
					sys.stdout.write("@SQ\tSN:%s\tLN:%d\n" % (seq["id"].split(" ")[0], seq["end"] - seq["start"]))
				wrote_header = True

			parts = line.split("\t")
			if len(parts) < 8:
				raise Exception

			reg = parts[2]

			reg_parts = reg.split("_")
			internal_id = reg_parts[0]
			offset = reg_parts[1]

			source_seq = None
			for seq in idx["seqs"]:
				if str(seq["internal_id"]) == internal_id:
					source_seq = seq

			if source_seq == None:
				raise "Source sequence could not be identified for aligned read"

			parts[2] = source_seq["id"].split(" ")[0]

			adjusted_pos = int(parts[3]) + int(offset)
			parts[3] = str(adjusted_pos)

			sys.stdout.write("\t".join(parts))

	if sys.argv[1] == "ctranslate":
		if len(sys.argv) < 4:
			print("Usage: gsample.py translate <reference.fasta> <in_alignment.sam>")
			sys.exit()

		log("Translating SAM file coordinates (as contig)...")

		idx = index(sys.argv[2])
		sampled_idx = json.loads(open(sys.argv[2] + ".sampled.fasta.index", "r").read())

		sampled_tree = intervaltree.IntervalTree()
		for sampled in sampled_idx:
			sampled_tree[(sampled["start"]):(sampled["end"])] = sampled

		handle = open(sys.argv[3], "r")
		wrote_header = False
		for line in handle:
			if line.startswith("@") or line.strip() == "":
				if line[:3] != "@SQ":
					sys.stdout.write(line)
				continue

			if not wrote_header:
				unique_seqs = {}
				for seq in idx["seqs"]:
					unique_seqs[seq["id"]] = seq
				for seqid in unique_seqs:
					seq = unique_seqs[seqid]
					sys.stdout.write("@SQ\tSN:%s\tLN:%d\n" % (seq["id"].split(" ")[0], seq["end"] - seq["start"]))
				wrote_header = True

			parts = line.split("\t")
			if len(parts) < 8:
				raise Exception

			read_pos = int(parts[3])

			source_sample_set = sampled_tree[read_pos]
			if len(source_sample_set) != 1:
				log("Warning: Len of source sample set = %d" % len(source_sample_set))
				continue

			source_sample = source_sample_set.pop().data
			source_seq = source_sample["source"]

			if source_seq == None:
				raise "Source sequence could not be identified for aligned read"

			parts[2] = source_seq["id"].split(" ")[0]

			adjusted_pos = int(parts[3]) - source_sample["start"] + source_sample["source_offset"]
			parts[3] = str(adjusted_pos)

			sys.stdout.write("\t".join(parts))
