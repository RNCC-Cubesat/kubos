#!/usr/bin/env python3

# Copyright 2018 Kubos Corporation
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

'''
main for Pumpkin MCU pumpkin_mcu_service
'''

import logging
import sys
import json
from pathlib import Path

from logging.handlers import SysLogHandler
from putdig.common import import_bus_telemetry_definition

from kubos_service import http_service
from kubos_service.config import Config
from pumpkin_mcu_service import schema

c = Config('pumpkin-mcu-service')

# Setup logging
logger = logging.getLogger('pumpkin-mcu-service')
logger.setLevel(logging.DEBUG)
handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_DAEMON)
formatter = logging.Formatter('pumpkin-mcu-service: %(message)s')
handler.formatter = formatter
logger.addHandler(handler)

# Set up a handler for logging to stdout
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setFormatter(formatter)
logger.addHandler(stdout)

# Load the bus definition from json file (see pumqry)
file = Path(c.raw['bus_path'])
schema.BUS_DEFINITION = import_bus_telemetry_definition(file)


def execute():
    """
    Runs pumpkin-mcu-service
    """
    http_service.start(c, schema.get_schema())
