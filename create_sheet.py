import re
import subprocess
import json
import argparse
import logging

import xlsxwriter

LOG = logging.getLogger(__name__)


def read_directory(path, levels):
    """ Get the JSON representation of the provided path. """
    LOG.info(f'Reading directory using tree: {path} with {levels} level(s)')

    json_raw = subprocess.check_output(['tree', '-ugfJ', '-L', str(levels), '--du', path])
    json_decoded = json_raw.decode('utf-8')

    # need to fix trailing , in JSON for tree version < 1.8.0
    json_flattned = re.sub('[\n\r]+', '', json_decoded)
    json_wo_trailing = re.sub(r',\s*\]', ']', json_flattned)

    res = json.loads(json_wo_trailing)

    LOG.info(f'Completed reading directory: {path}')

    return res


def create_excel(path):
    """ Create the workbook and worksheet """
    LOG.info(f'Creating Excel workbook: {path}')

    ws_name = 'Files+Folders'
    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet(ws_name)
    return wb, ws


def _write_header(ws):
    LOG.info('Writing header into sheet')

    ws.write(0, 0, 'Folder/File')
    ws.write(0, 1, 'Owner: User')
    ws.write(0, 2, 'Owner: Group')
    ws.write(0, 3, 'Size')
    ws.write(0, 4, 'Action')
    ws.write(0, 5, 'Target Location')
    ws.write(0, 6, 'Comment')


# BAAAAAAD globals...
_OFFSET = 1


def _write_rows(ws, data, indent=0):
    global _OFFSET

    for entry in data:
        # skip the report part
        if entry['type'] == 'report':
            continue

        ws.write(_OFFSET, 0, entry['name'])
        if 'user' in entry:
            ws.write(_OFFSET, 1, entry['user'])
            ws.write(_OFFSET, 2, entry['group'])
            ws.write(_OFFSET, 3, entry['size'])

        # do we need to indent?
        if indent > 0:
            ws.set_row(_OFFSET, options={'level': indent})

        _OFFSET += 1

        # recursive call
        if 'contents' in entry:
            _write_rows(ws, entry['contents'], indent=indent + 1)


def _write_validations(ws):
    LOG.info('Writing validations...')

    ws.data_validation(1, 4, _OFFSET, 4, {
        'validate': 'list',
        'source': ['Not defined', 'Move', 'Delete']
    })


def populate_sheet(ws, data):
    """ Write the values into the sheet """
    _write_header(ws)
    _write_rows(ws, data)
    _write_validations(ws)


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('output')
    parser.add_argument('--levels', type=int, default=5)
    args = parser.parse_args()

    # configure logging
    logging.basicConfig(level=logging.INFO)

    # process directories
    data = read_directory(args.directory, args.levels)
    wb, ws = create_excel(args.output)
    populate_sheet(ws, data)
    wb.close()


if __name__ == '__main__':
    main()
