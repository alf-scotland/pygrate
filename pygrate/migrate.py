import os
import argparse
import logging
import shutil
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet, Cell

from pygrate.common import SourceAction


LOG = logging.getLogger(__name__)


def read_migration_sheet(path, sheet_name=None):
    """ Simple reader to ingest migration sheets """
    wb = load_workbook(path)
    sheet = wb[sheet_name] if sheet_name else wb.active
    return sheet


class Action:
    def __init__(
        self,
        action,
        priority,
        source,
        target
    ):
        if not action:
            raise ValueError('Action cannot be none')

        self.action = SourceAction(action)
        self.priority = priority
        self.source = source

        if self.action in (SourceAction.COPY, SourceAction.MOVE) and not target:
            raise ValueError(f'Target needs to be specified for {self.action}')

        self.target = target

    def __repr__(self):
        res = f'{self.action} {self.source}'
        if self.action.lower() in (SourceAction.COPY, SourceAction.MOVE):
            res += f' -> {self.target}'
        return res

    def _delete(self):
        if self.source.is_file():
            self.source.unlink()
        else:
            shutil.rmtree(str(self.source))

    def _copy(self):
        # check if target exists to reverse copy things from source
        if self.target.exists() and self.source.is_dir() and self.target.is_dir():
            for s_source in self.source.iterdir():
                Action(
                    SourceAction.COPY,
                    -1,
                    s_source,
                    self.target / s_source.name
                ).perform()
        else:
            shutil.copytree(str(self.source), str(self.target))

    def _move(self):
        shutil.move(str(self.source), str(self.target))

    def perform(self):
        if self.action == SourceAction.DELETE:
            self._delete()
        elif self.action == SourceAction.COPY:
            self._copy()
        elif self.action == SourceAction.MOVE:
            self._move()
        elif self.action == SourceAction.NOT_DEFINED:
            raise ValueError('Action not defined')
        else:
            raise ValueError(f'Unknown action: {self.action}')

    __str__ = __repr__


def sheet_to_actions(sheet: Worksheet):
    iter_ = sheet.iter_rows()
    next(iter_)  # skip header

    # collect actions and paths
    actions = {}
    paths = []
    for row in iter_:
        path, _, _, _, action, target, *_ = map(lambda x: x.value, row)

        path = Path(path)
        target = Path(target) if target else None

        if action:
            action_cls = Action(action, len(path.parents), path, target)
            LOG.info(f'Found action: {action_cls}')
            actions[path] = action_cls
        else:
            paths.append(path)

    # check if all paths are addressed
    for path in paths:
        has_parent_action = any(p in actions for p in path.parents)

        if not has_parent_action:
            LOG.warning(f'{path} has no action')

    return actions


def _prioritize_actions(actions):
    return sorted(actions.values(), key=lambda a: a.priority, reverse=True)


def perform_actions(actions):
    """ Perform actions """
    for action in _prioritize_actions(actions):
        LOG.info(f'About to perform: {action}')
        action.perform()
        LOG.info(f'Action performed: {action}')


def dry_run_actions(actions):
    for action in _prioritize_actions(actions):
        LOG.info(f'Would perform action: {action}')


def migrate(workbook_path, sheet_name, dry_run=False):
    sheet = read_migration_sheet(workbook_path, sheet_name)
    actions = sheet_to_actions(sheet)
    if dry_run:
        dry_run_actions(actions)
    else:
        perform_actions(actions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workbook')
    parser.add_argument('--sheet')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    # configure logging
    logging.basicConfig(level=logging.INFO)

    migrate(args.workbook, args.sheet, args.dry_run)


if __name__ == '__main__':
    main()