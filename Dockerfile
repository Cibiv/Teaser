FROM ubuntu
RUN apt-get update && apt-get install -y wget zlib1g-dev cmake && apt-get install -y python python-pip git && pip install --upgrade pip && pip install intervaltree tornado pyaml psutil numpy
RUN echo "#!/bin/bash" > /usr/bin/teaser_shell.sh; echo "cd /teaser; python install.py 2> /dev/null; mv install.py _install.py 2> /dev/null;  bash" >> /usr/bin/teaser_shell.sh; chmod +x /usr/bin/teaser_shell.sh; ln -s /teaser/teaser.py /usr/bin/teaser; ln -s /teaser/teaser.py /usr/bin/teaser.py;
