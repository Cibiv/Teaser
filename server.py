#!/usr/bin/env python
from lib import server

server.instance = server.TeaserServer()
server.instance.main()
