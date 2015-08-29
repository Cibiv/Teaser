import sys

for line in open(sys.argv[1], "r").readlines():
	if line.strip() == "":
		continue

	if line[0] == "@":
		sys.stdout.write(line)
