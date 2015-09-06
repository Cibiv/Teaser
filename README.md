# Teaser
Welcome to the official github page of Teaser, an analytical framework for benchmarking NGS read mappers. Teaser allows researchers to identify the optimal mapper, parameter set and mapping quality thresholds for data sets that mimic their real data. Teaser is easy-to-use, flexible and fast thanks to its genome subsampling process, allowing users to test a variety of scenarios within minutes. Teaser is available as [web application](http://teaser.cibiv.univie.ac.at), a virtual machine image and normal installable version.

# Quickstart
Getting started with Teaser takes just a few minutes. The following sections contain possible next steps for beginners and advanced users.

## Example Report
For every benchmark Teaser generates an interactive HTML report summarizing the accuracy and performance of each mapper. A good way to get an overview of some of the features of Teaser could be to browse such a report. In the following example, Teaser was used to test five mappers on a [D. melanogaster Ion Torrent resequencing](http://teaser.cibiv.univie.ac.at/static/dataset_gallery/D3_n.html) data set:

## Web Application
To quickly get started with testing mappers for your personalized data set, Teaser is available as a public [web application](http://teaser.cibiv.univie.ac.at) that requires no registration.

## Learning more
For topics such as adding support for new mappers or creating customized parameter sets or even test procedures, please see our [Github Wiki](https://github.com/Cibiv/Teaser/wiki) for detailed information regarding the usage and extension of Teaser.

## Advanced Users: Virtual Machine Image
Using the virtual machine / installed version of Teaser enables features such as adding new reference genomes, parameter sets and mappers. We provide a ready-to-go installation as a VirtualBox virtual machine image. The [Github Wiki](https://github.com/Cibiv/Teaser/wiki) contains details on how to configure Teaser.

The Teaser virtual machine image will be made available soon.

## Advanced Users: Installation
For advanced users we recommend installing Teaser directly on your computer. Using the virtual machine / installed version of Teaser enables features such as adding new reference genomes, parameter sets and mappers. Teaser is bundled with an installation script that will download and install a predefined set of read mappers and read simulators.

Requirements:
* UNIX-like Operating System
* Python 2.x

Packages that may need to be installed before downloading and installing Teaser:
* python-pip
* python-dev

Packages that may be needed for the automatic building of mapper binaries:
* build-essentials
* cmake
* zlib

Installation:
```
git clone https://github.com/Cibiv/Teaser.git
cd Teaser
./install.py
```

##Command-Line Usage

Example usage: Running the built-in E. coli example benchmark:
```
./teaser.py example_ecoli.yaml
```

Example Usage: Starting the web interface:
```
./server.py
```

Accessing the web interface: `http://localhost:8888`

The command-line version of Teaser is controlled using configuration files in YAML format. The [Command Line](https://github.com/Cibiv/Teaser/wiki/Command-Line) Wiki page includes examples on how they can be used to define data sets and control benchmarks.

#License
Teaser is made available under the MIT License.
