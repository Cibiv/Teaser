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

		row.is_read1 = (flags & 0x40) != 0
		row.is_read2 = (flags & 0x80) != 0
		row.is_secondary = (flags & 0x900) != 0
		row.is_unmapped = (flags & 0x4) != 0
		row.is_reverse = (flags & 0x10) != 0
		row.is_paired = row.is_read1 or row.is_read2

		return True