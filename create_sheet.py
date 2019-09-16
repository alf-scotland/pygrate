import re
import subprocess
import json
import argparse
import logging
from distutils.version import LooseVersion

import xlsxwriter

LOG = logging.getLogger(__name__)


def _get_tree_version():
    raw = subprocess.check_output(['tree', '--version'])
    return LooseVersion(raw.decode('utf-8').split(' ')[1])


def _read_tree_output(path, levels, file_limit):
    args = [
        'tree',
        '-ugfhJ',
        '-L', str(levels),
        '--filelimit', str(file_limit),
        '--du',
        path
    ]
    LOG.info('Calling: %s', ' '.join(args))
    raw = subprocess.check_output(args)
    return raw.decode('utf-8')


def _fix_trailing_commas(json_raw):
    LOG.info('Fixing trailing commas for tree version below 1.8.0')
    json_raw = re.sub('[\n\r]+', '', json_raw)
    json_raw = re.sub(r',\s*\]', ']', json_raw)
    return json_raw


def _fix_error_messages(json_raw):
    return re.sub(r',"error":"[^"]*"', '', json_raw)


def read_directory(path, levels, file_limit):
    """ Get the JSON representation of the provided path. """
    LOG.info(f'Reading directory using tree with {levels} '
             f'level(s) and {file_limit} file-limit: {path}')

    tree_version = _get_tree_version()
    LOG.info(f'Using tree version: {tree_version}')

    if tree_version < LooseVersion('v1.7'):
        raise Exception(
            'tree version too low to support json output. Please upgrade.')

    json_raw = _read_tree_output(path, levels, file_limit)

    # need to fix trailing , in JSON for tree version < 1.8.0
    if tree_version < LooseVersion('v1.8'):
        json_raw = _fix_trailing_commas(json_raw)

    # need to fix wrong tree error message
    json_raw = _fix_error_messages(json_raw)

    res = json.loads(json_raw)

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
    parser.add_argument('--file-limit', type=int, default=50)
    args = parser.parse_args()

    # configure logging
    logging.basicConfig(level=logging.INFO)

    # process directories
    data = read_directory(args.directory, args.levels, args.file_limit)
    wb, ws = create_excel(args.output)
    populate_sheet(ws, data)
    wb.close()


if __name__ == '__main__':
    main()
