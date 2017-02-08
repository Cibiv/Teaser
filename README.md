#Teaser
Teaser analyzes the performance of read mappers based on a data set provided by you. After you enter key characteristics such as read length and reference genome, Teaser will simulate read data including the gold standard alignment. After the simulation, Teaser automatically runs and evaluates each mapper for the selected parameters and summarizes the results in a report. Teaser also supports benchmarking read mappers on real data or custom simulations, as well as testing new mappers and custom parameter sets. You can start using Teaser right now using our web application, or download and install it to use all advanced features.

* [Try the Teaser Web Application](http://teaser.cibiv.univie.ac.at)

##Documentation
The [GitHub Wiki](https://github.com/Cibiv/Teaser/wiki) contains all information on how to start benchmarking mappers with Teaser as well as customization and extension options.

##Installation
For a detailed guide, see the [Installation](https://github.com/Cibiv/Teaser/wiki/Installation) page in our wiki.

Entering the following commands will install Teaser including a set of popular read mappers:
```
git clone https://github.com/Cibiv/Teaser.git
cd Teaser
./install.py
```

Important: Teaser requires an internet connection during installation in order to download the mappers.

To see if everything is working, you can try benchmarking mappers for a simple E. coli dataset using:

```
./teaser.py example_ecoli.yaml
```

To start the Teaser [graphical interface](https://github.com/Cibiv/Teaser/wiki/Web-Browser-Interface) use:

```
./server.py
```

Then head to `http://localhost:8888` in a web browser of your choice.

##Citation
If you use Teaser to optimize read mapping in your study, please consider citing: [Smolka M, Rescheneder P, Schatz MC, von Haeseler A and Sedlazeck FJ. Teaser: Individualized benchmarking and optimization of read mapping results for NGS data. Genome Biology 2015, 16:235 (22 October 2015).](http://www.genomebiology.com/2015/16/1/235) DOI: 10.1186/s13059-015-0803-1

##License
Teaser is made available under the MIT License.
