#!/usr/bin/env python
import os
import sys
major=sys.version_info[0]

print("Checking Python version...")
if major != 2:
	print("Teaser currently requires Python 2! Version: %s"%str(sys.version_info))
	raise SystemExit

print("Installing Python package dependencies...")
if os.system("pip install --user intervaltree tornado") != 0:
	print("Failed to install dependencies: intervaltree/tornado!")
	raise SystemExit

print("Downloading software packages...")
os.system("wget http://www.cibiv.at/~moritz/teaser_software.tar.gz")
os.system("tar -xvzf teaser_software.tar.gz")

print("Downloading example reference genome (E. coli)...")
os.chdir("references")
os.system("wget http://www.cibiv.at/~moritz/E_coli.fasta")

