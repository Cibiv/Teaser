import json

class SAMRow:
	def __init__(self):
		self.qname = False

class SAMFile:
	def __init__(self, filename):
		self.handle = open(filename, "r")
		self.buffer = [SAMRow(), SAMRow()]
		self.current = -1
		self.current_row = self.buffer[0]

	def close(self):
		self.handle.close()

	def hasLast(self):
		return self.getLast().qname != False

	def getLast(self):
		return self.buffer[(self.current - 1) % len(self.buffer)]

	def getCurr(self):
		return self.current_row

	def getHeader(self):
		self.handle.seek(0)
		header = []
		line = self.handle.readline()
		while line != "" and line[:1] == "@":
			header.append(line.strip())
			line = self.handle.readline()

		self.handle.seek(0)
		return header

	def isSorted(self):
		for line in self.getHeader():
			if "SO:queryname" in line:
				return True
		return False

	def next(self):
		while True:
			line = self.handle.readline()
			if line == "":
				return False

			if line[0] == "@":
				continue

			parts = line.strip().split("\t")

			if len(parts) < 11:
				continue
			else:
				break

		self.current = (self.current + 1) % len(self.buffer)
		row = self.buffer[self.current]
		self.current_row = row

		flags = int(parts[1])

		row.qname = parts[0]
		row.flags = flags
		row.rname = parts[2]
		row.pos = int(parts[3])
		row.mapq = int(parts[4])
		row.seq = parts[9]


		row.tags = parts[11:]

		row.methylation = None
		if parts[-1][0:3]=="MT:":
			row.methylation = json.loads(parts[-1][3:])

		row.is_read1 = (flags & 0x40) != 0
		row.is_read2 = (flags & 0x80) != 0
		row.is_secondary = (flags & 0x900) != 0
		row.is_unmapped = (flags & 0x4) != 0
		row.is_reverse = (flags & 0x10) != 0
		row.is_paired = row.is_read1 or row.is_read2

		return True

class Object:
	def __init__(self):
		pass

class FASTQ:
	def __init__(self, filename, write=False):
		self.handle = open(filename, "w" if write else "r")

	def readline(self):
		return self.handle.readline()

	def next_read(self):
		read = Object()
		read.valid = False

		try:
			read.id = self.readline().strip()
			if len(read.id) > 0 and read.id[0] == "@":
				read.id = read.id[1:]
			else:
				raise

			read.seq = self.readline().strip()
			read.desc = self.readline().strip()
			read.qual = self.readline().strip()
			read.valid = True
		except Exception as e:
			pass

		return read

	def write_read(self,read):
		self.handle.write("@" + read.id + "\n")
		self.handle.write("%s\n%s\n%s\n" % (read.seq, read.desc, read.qual))

	def close(self):
		self.handle.close()