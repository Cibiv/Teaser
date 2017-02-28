docker build -t teaser_git . && docker run -v $(pwd):/teaser -it teaser_git "/usr/bin/teaser_shell.sh"

