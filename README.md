# Teaser
Welcome on the official github page of Teaser, an analytical framework for benchmarking NGS read mappers. Teaser allows researchers to identify the optimal mapper, parameter set and mapping quality thresholds for data sets that mimic their real data. Teaser is easy-to-use, flexible and fast thanks to its genome subsampling process, allowing users to test a variety of scenarios within minutes. Teaser is available as web application at http://teaser.cibiv.univie.ac.at .

# Quickstart
Getting started with Teaser takes just a few minutes. The following sections contain possible next steps for beginners and advanced users.

## Example Report
For every benchmark Teaser generates an interactive HTML report summarizing the accuracy and performance of each mapper. A good way to get an overview of some of the features of Teaser could be to browse such a report. In the following example, Teaser was used to test five mappers on a D. melanogaster Ion Torrent resequencing data set:

http://teaser.cibiv.univie.ac.at/static/dataset_gallery/D3_n.html

## Web Application
To quickly get started with testing mappers for your personalized data set, Teaser is available as a public web application that requires no registration:

http://teaser.cibiv.univie.ac.at

## Learn more
Please see our github wiki for detailed information regarding the usage and extension of Teaser:
https://github.com/Cibiv/Teaser/wiki

## Intermediate Users: Virtual Machine Image
If you want to provide your own simulated or real data set or reference genome, or customize Teaser by adding new mappers or parameter sets, we provide a ready-to-go installation as a VirtualBox virtual machine image. The Teaser wiki contains details on how to configure Teaser using only human-readable text files.

The Teaser virtual machine image will be made available soon.

## Advanced Users: Installation
For advanced users we recommend installing Teaser directly on your computer. Teaser is bundled with an installation script that will download and install a predefined set of read mappers and read simulators.

Requirements:
* UNIX-like Operating System
* Python 2.x

Installation:
```
git clone https://github.com/Cibiv/Teaser.git
cd Teaser
./install.py
```

Example usage: Running the built-in E. coli example benchmark:
```
./teaser.py example_ecoli
```

Example Usage: Starting the web interface:
```
./server.py
```

Accessing the web interface: `http://localhost:8888`

Note: Teaser by default places results in the `reports` directory.

#License
Teaser is made available under the MIT License.
