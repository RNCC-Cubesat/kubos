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
import string
from subprocess import run
from time import sleep

import graphene
from putdig.common.types import ModuleDefinition, SupMCUModuleDefinition
from pumpkin_supmcu.kubos import I2CKubosMaster
from pumpkin_supmcu.supmcu import SupMCUMaster
from pumpkin_supmcu.supmcu import get_values

try:
    from pumpkin_supmcu.i2cdriver import I2CDriverMaster
except ImportError:
    I2CDriverMaster = None

logger = logging.getLogger('pumpkin-mcu-pumpkin_mcu_service')

BUS_DEFINITION: List[ModuleDefinition] = []  # BUS_DEFINITION global set in service.py
I2C_MASTER: Union[I2CKubosMaster, I2CDriverMaster]  # I2C_MASTER global set in service.py


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
    s = re.sub(r'\W+\Z', '', s)  # remove any trailing non-alphanumeric substring
    s = re.sub(r'[\W]+', '_', s)  # replace non-alphanumeric substrings with underscore
    return s.lower()


class Query(graphene.ObjectType):
    """
    Creates query endpoints exposed by graphene.
    """

    ping = graphene.String()
    moduleList = graphene.JSONString()
    fieldList = graphene.List(graphene.String, module=graphene.String())
    commandList = graphene.List(graphene.String, module=graphene.String())
    read = graphene.String(
        module=graphene.String(),
        count=graphene.Int())
    mcuTelemetry = graphene.JSONString(
        module=graphene.String(),
        fields=graphene.List(graphene.String, default_value=[]))

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
    def resolve_fieldList(parent, info, module) -> List[str]:
        """
        This allows discovery of which fields are available for a specific module.
        """
        fields: List[str] = []
        mod = get_module(module)
        for _, item in mod.definition.supmcu_telemetry.items():
            fields.append(normalize(item.name))
        for _, item in mod.definition.module_telemetry.items():
            fields.append(normalize(item.name))
        return fields

    @staticmethod
    def resolve_commandList(parent, info, module) -> List[str]:
        """
        This allows discovery of which commands are available for a specific module.
        """
        mod = get_module(module)
        return [cmd.get('name') for cmd in mod.definition.commands.values()]

    @staticmethod
    def resolve_read(parent, info, module, count):
        """
        Reads number of bytes from the specified MCU
        Returns as a hex string.
        """
        mod = get_module(module)

        try:
            bin_data = I2C_MASTER.read(mod.definition.address, count)
            return bin_data.hex()
        except Exception as e:
            logger.error(f'Failed to read {count} bytes from {module}: {e}')
            raise e

    @staticmethod
    def resolve_mcuTelemetry(parent, info, module: str, fields: List[str]) -> Dict[str, List[Any]]:
        """
        Queries telemetry item fields from the specified module.
        :param module: string specifying the module
        :param fields: optional list of field names used to limit the query (if not included, request all telemetry)
        fields must match the output of resolve_fieldList()
        """
        telemetry = {}
        mod = get_module(module)
        supmcu_telemetry_names = [normalize(d.name) for d in mod.definition.supmcu_telemetry.values()]
        module_telemetry_names = [normalize(d.name) for d in mod.definition.module_telemetry.values()]

        if fields:
            for field in fields:
                if field in supmcu_telemetry_names:
                    telem = next((t for t in mod.definition.supmcu_telemetry.values() if normalize(t.name) == field))
                    telemetry[field] = [d.value for d in get_values(I2C_MASTER, mod.definition.address, 'SUP',
                                                                    telem.idx, telem.format)]
                elif field in module_telemetry_names:
                    telem = next((t for t in mod.definition.module_telemetry.values() if normalize(t.name) == field))
                    telemetry[field] = [d.value for d in get_values(I2C_MASTER, mod.definition.address,
                                                                    mod.definition.cmd_name, telem.idx, telem.format)]
                else:
                    raise KeyError(f'Could not resolve unknown field name {field}')

        else:
            for telem in mod.definition.supmcu_telemetry.values():
                field = normalize(telem.name)
                telemetry[field] = []
                for data_item in get_values(I2C_MASTER, mod.definition.address, 'SUP', telem.idx, telem.format):
                    telemetry[field].append(data_item.value)
            for telem in mod.definition.module_telemetry.values():
                field = normalize(telem.name)
                telemetry[field] = []
                for data_item in get_values(I2C_MASTER, mod.definition.address, mod.definition.cmd_name, telem.idx,
                                            telem.format):
                    telemetry[field].append(data_item.value)
        return telemetry


class SendCommand(graphene.Mutation):
    """
    Send commands to bus modules.
    TODO: return actual command status/results from bus
    """
    class Arguments:
        module = graphene.String()
        command = graphene.String()
        validate = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(parent, info, module: str, command: str, validate=True):

        def validate_command(cmd: str, mod_: SupMCUModuleDefinition):
            table = str.maketrans('', '', string.ascii_lowercase)
            normalized_cmd = cmd.translate(table).split(' ')[0]  # remove optional SCPI lowercase, isolate command
            commands = [c['name'] for c in mod_.commands.values()]
            commands = [c.translate(table).split(' ')[0] for c in commands]   # do the same for known commands
            if normalized_cmd not in commands:
                raise KeyError(f'Unknown command {cmd}')

        mod = get_module(module)
        sup_master = SupMCUMaster(I2C_MASTER, [mod.definition for mod in BUS_DEFINITION])
        if validate:
            validate_command(command, mod.definition)
        sup_master.send_command(mod.definition.name, command)
        return SendCommand(ok=True)


class UsbOn(graphene.Mutation):
    """
    Turns on power to the BeagleBone Black's USB-A Host port.
    """
    ok = graphene.Boolean()

    @staticmethod
    def mutate(parent, info):
        with open('/sys/bus/usb/drivers/usb/bind', 'w') as fp:
            status = run(['echo', 'usb1'], stdout=fp)
        if status.returncode != 0:
            return UsbOn(ok=False)
        sleep(1)
        status = run(['devmem2', '0x47401c60', 'b', '0x01'])
        return UsbOff(status.returncode == 0)


class UsbOff(graphene.Mutation):
    """
    Turns off power to the BeagleBone Black's USB-A Host port.
    """
    ok = graphene.Boolean()

    @staticmethod
    def mutate(parent, info):
        status = run(['devmem2', '0x47401c60', 'b', '0x00'])
        if status.returncode != 0:
            return UsbOff(ok=False)
        sleep(1)
        with open('/sys/bus/usb/drivers/usb/unbind', 'w') as fp:
            status = run(['echo', 'usb1'], stdout=fp)
        return UsbOff(status.returncode == 0)


class Mutations(graphene.ObjectType):
    """
    Creates mutation endpoints exposed by graphene.
    """
    send_command = SendCommand.Field()
    usb_on = UsbOn.Field()
    usb_off = UsbOff.Field()


def get_schema():
    """
    Returns graphene Schema object with out Query and Mutation
    """
    return graphene.Schema(query=Query, mutation=Mutations)
