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
        source,
        target=None,
        priority=None
    ):
        if not action:
            raise ValueError('Action cannot be none')

        self.action = SourceAction(action)
        self.source = source

        if self.action in (SourceAction.COPY, SourceAction.MOVE) and not target:
            raise ValueError(f'Target needs to be specified for {self.action}')
        self.target = target

        self.priority = priority

    def __repr__(self):
        res = f'{self.action} {self.source}'
        if self.action in (SourceAction.COPY, SourceAction.MOVE):
            res += f' -> {self.target}'
        return res

    def _delete(self, dry_run):
        if dry_run:
            LOG.info('Would delete {self.source}')

        if self.source.is_file():
            self.source.unlink()
        else:
            shutil.rmtree(str(self.source))

    def _migrate_with_source_name(self, dry_run):
        Action(
            self.action,
            self.source,
            self.target / self.source.name,
            self.priority
        ).perform(dry_run=dry_run)

    def _migrate_elements(self, dry_run):
        for entry in self.source.iterdir():
            Action(
                self.action,
                entry,
                self.target / entry.name,
                self.priority
            ).perform(dry_run=dry_run)

    def _migrate(self, func, dry_run):
        if self.target.exists() and not self.target.is_dir():
            raise IOError(f'Target exists: {self.target}')

        target_is_file = bool(self.target.suffix)
        if self.source.is_dir() and target_is_file:
            raise IOError('Cannot migrate a directory to a file')

        # is the target an existing directory, change target to
        # target / source.name
        if self.source.is_dir() and self.target.is_dir():
            # migrate all elements in source if names are the same
            if self.source.name.lower() == self.target.name.lower():
                self._migrate_elements(dry_run)

                # clean up if moving things here
                if self.action == SourceAction.MOVE and not dry_run:
                    self.source.rmdir()
            else:
                self._migrate_with_source_name(dry_run)

        elif self.source.is_file() and not target_is_file:
            self._migrate_with_source_name(dry_run)

        else:
            target_parent = self.target.parent
            if not target_parent.exists():
                if dry_run:
                    LOG.info('Would create directory path: {target_parent}')
                else:
                    # parent does not exist, lets try and create it
                    target_parent.mkdir(parents=True)

            if dry_run:
                LOG.info(f'Would use {func} to migrate {self.source} -> {self.target}')
            else:
                func(str(self.source), str(self.target))

    def _copy(self, dry_run):
        func = shutil.copy2 if self.source.is_file() else shutil.copytree
        self._migrate(func, dry_run)

    def _move(self, dry_run):
        self._migrate(shutil.move, dry_run)

    def perform(self, dry_run=False):
        action_msg = 'dry-run' if dry_run else 'perform'
        LOG.info(f'About to {action_msg}: {self}')

        if self.action == SourceAction.DELETE:
            self._delete(dry_run)
        elif self.action == SourceAction.COPY:
            self._copy(dry_run)
        elif self.action == SourceAction.MOVE:
            self._move(dry_run)
        elif self.action == SourceAction.NOT_DEFINED:
            raise ValueError('Action not defined')
        else:
            raise ValueError(f'Unknown action: {self.action}')

        if not dry_run:
            LOG.info(f'Action performed: {self}')

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
            action_cls = Action(action, path, target, len(path.parents))
            LOG.debug(f'Found action: {action_cls}')
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
        action.perform()


def dry_run_actions(actions):
    for action in _prioritize_actions(actions):
        action.perform(dry_run=True)        


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
