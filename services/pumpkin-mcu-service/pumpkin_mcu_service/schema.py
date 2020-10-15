#!/usr/bin/env python3

# Copyright 2018 Kubos Corporation
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""
Graphene schema setup to enable queries.
"""

from typing import List, Union, Dict, Any
import logging
import re
import itertools

import graphene
from putdig.common.types import ModuleDefinition
from pumpkin_supmcu.kubos import I2CKubosMaster
from pumpkin_supmcu.supmcu import SupMCUMaster
from pumpkin_supmcu.supmcu import get_values

logger = logging.getLogger('pumpkin-mcu-pumpkin_mcu_service')

BUS_DEFINITION: List[ModuleDefinition] = []  # BUS_DEFINITION global set in service.py
I2C_BUS: int = 1


def get_module(module_name: str) -> Union[ModuleDefinition, None]:
    """
    Gets the ModuleDefinition of the specified module if it is present in BUS_DEFINITION.
    :param module_name: the name of the module as a string.
    :raises: KeyError if the module is not present in BUS_DEFINITION.
    :return: The ModuleDefiniton of the module if it is present, else None
    """
    mod: ModuleDefinition = next((mod for mod in BUS_DEFINITION if mod.definition.name == module_name.upper()), None)
    if mod is None:
        raise KeyError('Module not configured: {}'.format(module_name))
    return mod


def normalize(s: str) -> str:
    """
    Normalizes a string by replacing any non-alphanumeric substrings with an underscore and making it lowercase.
    Examples:
        'Firmware version' -> 'firmware_version'
        'Payload Currents in mA' -> 'payload_currents_in_ma'
        'Temp sensor 9 reading (0.1K)' -> 'temp_sensor_9_reading_0_1K'
    """
    s = re.sub(r'\W+\Z', '', s)   # remove any trailing non-alphanumeric substring
    s = re.sub(r'[\W]+', '_', s)  # replace non-alphanumeric substrings with underscore
    return s.lower()


class Query(graphene.ObjectType):
    """
    Creates query endpoints exposed by graphene.
    """

    ping = graphene.String()
    moduleList = graphene.JSONString()
    fieldList = graphene.List(graphene.String, module=graphene.String())
    read = graphene.String(
        module=graphene.String(),
        count=graphene.Int())
    mcuTelemetry = graphene.JSONString(
        module=graphene.String(),
        fields=graphene.List(graphene.String, default_value=['all']))

    @staticmethod
    def resolve_ping(parent, info):
        return 'pong'

    @staticmethod
    def resolve_moduleList(parent, info):
        '''
        This allows discovery of which modules are present and what
        addresses they have.
        '''
        return {mod.definition.name: {'address': mod.definition.address} for mod in BUS_DEFINITION}

    @staticmethod
    def resolve_fieldList(parent, info, module_name) -> Union[List[str], Dict[str, str]]:
        """
        This allows discovery of which fields are available for a
        specific module.
        """
        fields: List[str] = []
        mod = get_module(module_name)
        for _, item in mod.definition.supmcu_telemetry.items():
            fields.append(normalize(item.name))
        for _, item in mod.definition.module_telemetry.items():
            fields.append(item.name)
        return fields

    @staticmethod
    def resolve_read(parent, info, module_name, count):
        """
        Reads number of bytes from the specified MCU
        Returns as a hex string.
        """
        mod = get_module(module_name)
        i2c_master = I2CKubosMaster(I2C_BUS)
        try:
            bin_data = i2c_master.read(mod.definition.address, count)
            return bin_data.hex()
        except Exception as e:
            logger.error(f'Failed to read {count} bytes from {module_name}: {e}')
            raise e

    @staticmethod
    def resolve_mcuTelemetry(parent, info, module_name: str, fields: List[str] = None) -> Dict[str, List[Any]]:
        """
        Queries telemetry item fields from the specified module.
        :param module_name: string specifying the module
        :param fields: optional list of field names used to limit the query (if not included, request all telemetry)
        fields must match the output of resolve_fieldList()
        """
        telemetry = {}
        i2c_master = I2CKubosMaster(I2C_BUS)
        mod = get_module(module_name)
        for field in fields:
            all_telemetry = itertools.chain(mod.definition.supmcu_telemetry.values(),
                                            mod.definition.module_telemetry.values())
            telem = next((t for t in all_telemetry if normalize(t.name) == field), None)
            if telem is None:
                raise KeyError(f'Could not resolve unknown field name {field}')
            telemetry[field] = get_values(i2c_master, mod.definition.address, mod.definition.cmd_name, telem.idx,
                                          telem.format)
        return telemetry


class Passthrough(graphene.Mutation):
    """
    Unvalidated command passthrough.
    """

    class Arguments:
        module = graphene.String()
        command = graphene.String()

    @staticmethod
    def mutate(parent, info, module_name: str, command: str) -> None:
        """
        Handles passthrough commands to the Pumpkin MCU modules.
        """
        mod = get_module(module_name)
        if type(command) == str:
            command = str.encode(command)
        i2c_master = I2CKubosMaster(I2C_BUS)
        sup_master = SupMCUMaster(i2c_master, [mod.definition for mod in BUS_DEFINITION])
        try:
            sup_master.send_command(mod.definition.name, command)
        except Exception as e:
            logger.error('Failed to send passthrough to {}: {}'.format(module_name, e))
            raise


class Mutation(graphene.ObjectType):
    """
    Creates mutation endpoints exposed by graphene.
    """
    passthrough = Passthrough.Field()


def get_schema():
    """
    Returns graphene Schema object with out Query and Mutation
    """
    return graphene.Schema(query=Query, mutation=Mutation)
