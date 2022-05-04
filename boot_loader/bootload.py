#!/usr/bin/env python

"""Dephy's firmware loading tool."""

from cleo import Application
from commands import ListFirmwareCmd
application = Application() 
application.add(ListFirmwareCmd())

if __name__ == "__main__":
    application.run()
