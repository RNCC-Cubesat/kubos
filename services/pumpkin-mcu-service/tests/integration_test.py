#!/usr/bin/env python3

# Copyright 2018 Kubos Corporation
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""
Integration test for the Pumpkin MCU Service. 

Runs basic queries to pumpkin-mcu-service
"""

import pytest
from typing import Dict, List, Any
import json

from python_graphql_client import GraphqlClient
from requests.exceptions import ConnectionError

ENDPOINT = 'http://localhost:8150'


class PumpkinMcuServiceError(Exception):
    pass


@pytest.fixture(scope='module')
def client():
    return GraphqlClient(ENDPOINT)


@pytest.fixture(scope='module')
def ping(client):
    query = 'query { ping }'
    try:
        result = client.execute(query)
    except ConnectionError as e:
        return {'error': e}
    if 'errors' in result:
        raise PumpkinMcuServiceError(result['errors'])
    return result.get('data')


@pytest.fixture(scope='module')
def module_list(client) -> Dict[str, int]:
    query = 'query { moduleList }'
    result = client.execute(query)
    if 'errors' in result:
        raise PumpkinMcuServiceError(result['errors'])
    return json.loads(result['data']['moduleList'])


@pytest.fixture(scope='module')
def field_lists(client, module_list) -> List[List[str]]:
    all_fields = []
    for mod in module_list:
        query = f'query {{ fieldList(module:"{mod}") }}'
        result = client.execute(query)
        if 'errors' in result:
            raise PumpkinMcuServiceError(result['errors'])
        all_fields.append(result['data']['fieldList'])
    return all_fields


@pytest.fixture(scope='module')
def command_lists(client, module_list) -> List[List[str]]:
    all_commands = []
    for mod in module_list:
        query = f'query {{ commandList(module:"{mod}") }}'
        result = client.execute(query)
        if 'errors' in result:
            raise PumpkinMcuServiceError(result['errors'])
        all_commands.append(result['data']['commandList'])
    return all_commands


@pytest.fixture(scope='module')
def mcu_telemetry(client, module_list) -> Dict[str, Dict[str, Any]]:
    all_telem = {}
    for mod in module_list:
        query = f'query {{ mcuTelemetry(module:"{mod}") }}'
        result = client.execute(query)
        if 'errors' in result:
            raise PumpkinMcuServiceError(f'{mod}: {result["errors"]}')
        all_telem[mod] = json.loads(result['data']['mcuTelemetry'])
    return all_telem


def test_ping(ping):
    """Tests if the pumpkin-mcu-service is reachable."""
    assert ping.get('ping') == 'pong', f'ping failed, is pumpkin-mcu-service running on {ENDPOINT}?'


def test_resolve_module_list(module_list):
    """Tests resolving the module list."""
    assert module_list is not None


def test_resolve_field_lists(module_list, field_lists):
    """Tests resolving the field list of all modules."""
    assert len(field_lists) == len(module_list)


def test_resolve_command_lists(module_list, command_lists):
    """Tests resolving the command list of all modules."""
    assert len(command_lists) == len(module_list)


def test_resolve_mcu_telemetry(mcu_telemetry, module_list):
    """Tests resolving mcu telemetry for all modules."""
    assert len(mcu_telemetry) == len(module_list)


def get_single_telemetry(client, module, field):
    query = f'query {{ mcuTelemetry(module:"{module}", fields:["{field}"]) }}'
    result = client.execute(query)
    if 'errors' in result:
        raise PumpkinMcuServiceError(result['errors'])
    return json.loads(result['data']['mcuTelemetry']).get(field)[0]


def test_send_command(client, module_list):
    """Tests sending a command to each module, checking num_scpi_cmds."""
    for mod in module_list:
        num_cmds_before = get_single_telemetry(client, mod, 'scpi_cmds_processed')
        command = 'SUP:LED FLASH'
        mutation = f'mutation {{ sendCommand(module:"{mod}", command:"{command}"){{ok}} }}'
        result = client.execute(mutation)
        if 'errors' in result:
            raise PumpkinMcuServiceError(result['errors'])
        assert result['data']['sendCommand']['ok']
        num_cmds_after = get_single_telemetry(client, mod, 'scpi_cmds_processed')
        assert num_cmds_after == num_cmds_before + 2    # +1 for LED command +1 for telem command

