#!/usr/bin/env python
"""
Convert FASTQ output of simulators containing simulation information into SAM alignment file
"""

import traceback
import base64


def encode_qname(qname, retain_petag=True):
	# return md5.new(str(qname)).hexdigest()
	if qname[-2] == "/":
		if retain_petag:
			return base64.b64encode(qname[0:-2], "-_") + qname[-2:]
		else:
			return base64.b64encode(qname[0:-2], "-_")
	else:
		return base64.b64encode(qname, "-_")


class Object:
	def __init__(self):
		pass


class FASTQ:
	def __init__(self, filename, pe):
		self.handle = open(filename, "r")
		self.out_handle = open("enc_" + filename, "w")
		self.lines = iter(self.handle.readlines())
		self.is_paired = pe

	def readline(self):
		return next(self.lines).strip()

	def next_read(self):
		read = Object()
		read.valid = False

		try:
			read.id = self.readline()
			if len(read.id) > 0 and read.id[0] == "@":
				read.id = read.id[1:]
			else:
				raise

			read.id_encoded = encode_qname(read.id, self.is_paired)
			read.seq = self.readline()
			read.desc = self.readline()
			read.qual = self.readline()
			read.valid = True

			self.out_handle.write("@" + read.id_encoded + "\n")
			self.out_handle.write("%s\n%s\n%s\n" % (read.seq, read.desc, read.qual))
		except Exception as e:
			pass

		return read


"""
Aligns reads based on their data
"""


class Aligner:
	def __init__(self):
		pass

	def align(read):
		pass


class dwgsim(Aligner):
	def align(self, read, paired=False, is_read1=True):
		# @random_sequence_632951_1_1_0_0_0_2:0:0_0:0:0_0
		parts = read.id.split("_")
		if is_read1:
			read.pos = parts[-9]
		else:
			read.pos = parts[-8]

		if paired:
			read.is_read1 = is_read1
			read.is_read2 = not is_read1
		else:
			read.is_read1 = False
			read.is_read2 = False

		read.chrom = "_".join(parts[0:-9])
		# print(read.id,read.chrom,read.pos)

		read.flags = 0

		reverse = (int(parts[-7]) == 1)
		if read.is_read2:
			reverse = not reverse

		if reverse:
			read.flags = read.flags | 0x10

		if paired:
			read.flags = read.flags | 0x1

		if read.is_read1:
			read.flags = read.flags | 0x40

		if read.is_read2:
			read.flags = read.flags | 0x80

	def align_pair(self, read1, read2):
		self.align(read1, True, True)
		self.align(read2, True, False)


class Converter:
	def __init__(self, aligner, outfile):
		self.aligner = aligner
		self.sam = open(outfile, "w")
		self.sam_enc = open("enc_" + outfile, "w")

	def write(self, what):
		self.sam.write(what)
		self.sam_enc.write(what)

	def write_sam_header(self, reads):
		seq = []
		for read in reads:
			if not read.chrom in seq:
				seq.append(read.chrom)

		for s in sorted(seq):
			self.write("@SQ\tSN:%s\tLN:10000\n" % s)

		self.write("@PG\tID:mapper\tPN:mapper\tVN:1.0\n")

	def write_single(self, read, to):
		read_id = read.id
		if read_id[-2] == "/":
			read_id = read_id[0:-2]
		to.write("%s\t%d\t%s\t%d\t60\t*\t*\t0\t0\t%s\t%s\n" % (
			read_id, read.flags, read.chrom, int(read.pos), read.seq, read.qual))

	def align_se(self, infile):
		fastq = FASTQ(infile, False)

		read = fastq.next_read()
		# aligned = []
		while read.valid:
			self.aligner.align(read)
			# aligned.append(read)

			self.write_single(read, self.sam)
			read.id = read.id_encoded
			self.write_single(read, self.sam_enc)
			del read
			read = fastq.next_read()
		# self.write_sam_header(aligned)

		# for read in aligned:
		#	self.write_single(read,self.sam)
		#	read.id = read.id_encoded
		#	self.write_single(read,self.sam_enc)

		self.sam.close()
		self.sam_enc.close()

	def align_pe(self, infile_1, infile_2):
		fq1 = FASTQ(infile_1, True)
		fq2 = FASTQ(infile_2, True)

		read1 = fq1.next_read()
		read2 = fq2.next_read()
		aligned1 = []
		aligned2 = []
		while read1.valid and read2.valid:
			self.aligner.align_pair(read1, read2)
			aligned1.append(read1)
			aligned2.append(read2)
			read1 = fq1.next_read()
			read2 = fq2.next_read()

		self.write_sam_header(aligned1)

		for i in range(len(aligned1)):
			self.write_single(aligned1[i], self.sam)
			self.write_single(aligned2[i], self.sam)

			aligned1[i].id = aligned1[i].id_encoded
			aligned2[i].id = aligned2[i].id_encoded

			self.write_single(aligned1[i], self.sam_enc)
			self.write_single(aligned2[i], self.sam_enc)

		self.sam.close()
		self.sam_enc.close()


if __name__ == "__main__":
	import sys

	if len(sys.argv) < 3:
		print("Usage: fastq2sam.py <simulator> <reads.fastq> [<reads_2.fastq>]")
		raise SystemExit

	arg_sim = sys.argv[1]
	arg_reads1 = sys.argv[2]

	if len(sys.argv) > 3:
		arg_reads2 = sys.argv[3]
		paired = True
	else:
		paired = False

	if arg_sim == "dwgsim":
		aligner = dwgsim()
	else:
		raise "Simulator not supported"

	conv = Converter(aligner, arg_reads1 + ".sam")

	if not paired:
		print(
			"Align single-end reads from " + arg_sim + ", input: " + arg_reads1 + ", output " + arg_reads1 + ".sam...")
		conv.align_se(arg_reads1)
	else:
		print(
			"Align paired-end reads from " + arg_sim + ", input: " + arg_reads1 + " + " + arg_reads2 + ", output " + arg_reads1 + ".sam...")
		conv.align_pe(arg_reads1, arg_reads2)
