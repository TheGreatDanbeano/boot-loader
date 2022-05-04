#!/usr/bin/env python

"""Dephy's firmware loading tool."""

from commands import ListFwCommand
from cleo import Application

application = Application()
application.add(ListFwCommand())

if __name__ == '__main__':
    application.run()
