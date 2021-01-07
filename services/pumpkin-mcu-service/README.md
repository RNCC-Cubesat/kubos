# Pumpkin MCU Service

Hardware service for interacting with all Pumpkin Modules.

By default this service listens on port 8150 for UDP graphql queries and mutations.

Configuration for this service is set in `/etc/kubos-config.toml`:

```
[pumpkin-mcu-service.addr]
ip = "0.0.0.0"
port = 8150

[pumpkin-mcu-service]
i2c_type = "kubos"
i2c_port = 1
bus_path = "/home/system/etc/bus.json"
```
The config options in this file are:
* IP address and port to serve on.
* `i2c_type` sets the i2c master type. Either `"kubos"` or `"i2cdriver"`. For flight, this should be set to `"kubos"`, the `"i2cdriver"` option is to facilitate testing this service without re-building kubos for an SBC (see [Testing](#testing)).
* `i2c_port` if `i2c_type` is `kubos` this sets the I2C bus number to use, if `i2c_type` is `i2cdriver` then this sets the linux device path to the i2c driver (e.g. `/dev/ttyUSB0`)
* `bus_path` sets the path to the bus definition file. See [Bus Definition File](#bus-definition-file) below.

## Bus Definition File
This file defines all the modules available on the bus, including the I2C address of each and the telemetry and commands available. This file must match the actual hardware on the bus in order for the pumpkin mcu service to function properly.

The default location of this file in kubos is `/home/system/etc/bus.json`.

The bus definition file can be regenerated using the [pumqry](https://github.com/PumpkinSpace/PuTDIG-CLI) program with this command: `pumqry -t kubos -p 1 -e -d -f /home/system/etc/bus.json`

## Examples

Query for the available modules
```
query {
    moduleList
}
```

Query for the available telemetry fields of a module:
```
query {
    fieldList(module:"BIM")
}
```

Query for the available command names of a module:
```
query {
    commandList(module:"BIM"(
}
```

Query for all telemetry of a module:
```
query {
    mcuTelemetry(module:"BIM")
}
```

Query for specific telmetry of a module:
```
query {
    mcuTelemetry(module:"BIM", fields:["firmware_version", "scpi_cmds_processed", "imu_data"])
}
```

Send a commands to a module:
```
mutation {
    sendCommand(module:"SIM", command:"SUP:LED ON") {
        ok
    }
}
```

### More Examples

Turn PIM power port 2 ON
```
mutation {
    sendCommand(module:"PIM", command:"SUP:PORT:POW ON,2") {
        ok
    }
}
```

Turn on BIM temp sensors and read them
```
mutation bim_temp_on {
    sendCommand(module:"BIM", command:"BIM:TEMP:POW ON") { ok }
}

query get_temp_data {
    mcuTelemetry(module:"BIM", fields:["temperature_0_1_k"])
}

```

Turn on AIM2's Novatel GPS and select its UART channel and enable passthrough
```
mutation gps_setup {
    gps_on: sendCommand(module:"AIM", command:"AIM:GPS:POW ON") { ok }
    gps_comm: sendCommand(module:"AIM", command:"AIM:GPS:COMM UART0") { ok }
    gps_pass: sendCommand(module:"AIM", command:"AIM:GPS:PASS ON") { ok }
}
```

Turn on RHM2 globalstar radio and send a beacon
```
mutation radio_setup {
    rad_on: sendCommand(module:"RHM", command:"RHM:GS:POW ON") { ok }
    rad_pass: sendCommand(module:"RHM", command:"RHM:GS:PASS ON") { ok }
    rad_comm: sendCommand(module:"RHM", command:"RHM:GS:COMM I2C") { ok }
    rad_send: sendCommand(module:"RHM", command:"RHM:GS:SEND 50756D706B696E") { ok }   # send hex string "Pumpkin"
}
```

Send queries and mutations from the command line:

```
echo "query {moduleList}" | nc -uw1 127.0.0.1 8150
echo "query {fieldList(module:\"sim\")}" | nc -uw1 127.0.0.1 8150
echo "mutation {sendCommand(module:\"sim\",command:\"SUP:LED ON\"){ok}}" | nc -uw1 127.0.0.1 8150
```

## Testing
In order to test changes to this service without re-building kubos for an OBC, you can run it from your development machine, talking to a bus over an [i2c driver board](https://i2cdriver.com/).

For example, on a Linux host:
* `pipenv shell`
* `pip install --editable ./`
* `pumpkin-mcu-service -c ./test-config.toml`


In the tests folder, there is an integration test script that can be run to verify communication with all modules on the bus. It will retrieve what modules are present, request what fields are available for each module, and retrieve all available telemetry for each module. To run it, just execute `pytest`.

