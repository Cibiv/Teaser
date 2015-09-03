#!/usr/bin/env python
import os
import sys
major=sys.version_info[0]

errors=[]

def error(msg):
	errors.append(msg)

def sub(cmd):
	if os.system(cmd) != 0:
		errors.append("Command failed: %s"%cmd)

print("Checking Python version...")
if major != 2:
	error("Teaser currently requires Python 2! Version: %s"%str(sys.version_info))

print("Installing Python package dependencies...")
sub("pip install --user intervaltree tornado pyaml psutil")

print("Downloading software packages...")
sub("wget http://www.cibiv.at/~moritz/teaser_software.tar.gz")
sub("tar -xvzf teaser_software.tar.gz")

print("Downloading example reference genome (E. coli)...")
os.chdir("references")
sub("wget http://www.cibiv.at/~moritz/E_coli.fasta")
os.chdir("..")

print("Building NGM...")
os.chdir("software/ngm_build")
sub("mkdir -p build/release")
os.chdir("build/release")
sub("cmake -DCMAKE_BUILD_TYPE=Release ../..")
sub("make")
os.chdir("../../../")
sub("cp -R ngm_build/bin/ngm-0.4.13/* ngm")
os.chdir("..")
sub("rm teaser_software.tar.gz")

if len(errors)==0:
	print("Installation completed successfully!")
else:
	print("Errors occured during installation:")
	for msg in errors:
		print("\t%s"%msg)
