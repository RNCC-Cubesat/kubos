#!/usr/bin/env python3.7

import app_api

import argparse
from pprint import pprint
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--config', '-c')

    args = parser.parse_args()

    SERVICES = app_api.Services(args.config) if args.config is not None else app_api.Services()

    request = '{ ping }'

    try:
        response = SERVICES.query(service='monitor-service', query=request)

        data = response['ping']
        if data == 'pong':
            print('We got a pong!')
            status = 'Okay'
        else:
            print(f'Unexpected monitor service response {data}', file=sys.stderr)
            status = 'Unexpected'
    except e:
        print('Something went wrong: ' + str(e), file=sys.stderr)
        status = 'Error'

    request = f'''
        mutation {{
            insert(subsystem: "OBC", parameter: "status", value: "{status}") {{
                success,
                errors
            }}
        }}
    '''

    try:
        response = SERVICES.query(service='telemetry-service', query=request)
    except e:
        print('Something went wrong: ' + str(e), file=sys.stderr)
        sys.exit(1)

    data = response['insert']
    success = data['success']
    errors = data['errors']

    if not success:
        print('Telemetry insert contained errors: ' + str(errors), file=sys.stderr)
        sys.exit(1)
    else:
        print('Telemetry insert completed successfully:')
        pprint(data)
