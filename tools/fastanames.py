import sys

if len(sys.argv) < 2:
	print("Print sequence identifiers in fasta file")
	print("Usage: fastanames.py input_fasta")
	raise SystemExit

infile = open(sys.argv[1], "r")

for line in infile:
	if len(line) > 0 and line[0] == ">":
		print(line)
