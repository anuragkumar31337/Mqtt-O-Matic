# MQTT-O-Matic

A professional MQTT scanner and authentication tester tool for identifying and testing MQTT brokers.

![MQTT-O-Matic](https://img.shields.io/badge/Version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.6%2B-green.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

## Features

- Scan multiple MQTT brokers simultaneously
- Test for unauthenticated access
- Test common default credentials
- Support for custom ports
- Multiple output formats (TXT, JSON, CSV)
- Verbose mode for detailed output
- Progress indicator
- Comprehensive results summary

## Installation

```bash
git clone https://github.com/a1c3venom/mqtt-o-matic.git
cd mqtt-o-matic
pip3 install -r requirements.txt

```

## Examples

```
Scan targets from a file
python mqtt-o-matic.py -t targets.txt -o results.txt

# Scan specific IPs with verbose output
python mqtt-o-matic.py -t 192.168.1.1,192.168.1.2:1884 -o results.json -f json -v

# Scan a single target with custom port
python mqtt-o-matic.py -t 10.0.0.5:1883 -o results.csv -f csv

# Output to stdout in JSON format
python mqtt-o-matic.py -t targets.txt -o - -f json
```
