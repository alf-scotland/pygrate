from pathlib import Path
import os
import logging

import pytest

from pygrate.common import SourceAction
from pygrate.migrate import read_migration_sheet, sheet_to_actions, perform_actions, Action


EXAMPLE_FILE = Path(__file__).parent / '_resources' / 'example.xlsx'


def test_action_delete_file(fs):
    path = Path('./from/to-be-removed/example.txt')
    fs.create_file(str(path))

    action = Action(SourceAction.DELETE, path)
    action.perform()

    assert not path.exists()


def test_action_delete_directory(fs):
    path = Path('./from/to-be-removed/example.txt')
    fs.create_file(str(path))

    action = Action(SourceAction.DELETE, path.parent)
    action.perform()

    assert not path.parent.exists()
    assert path.parent.parent.exists()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_file_to_file(fs, source_action):
    source = Path('/from/to-be-copied/example.txt')
    target = Path('/new/target/example.txt')
    fs.create_file(str(source))
    fs.create_dir('/new')

    # file does not exist
    action = Action(source_action, source, target)
    action.perform()
    assert target.exists()

    if source_action == SourceAction.MOVE:
        assert not source.exists()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_file_to_existing_file(fs, source_action):
    source = Path('/from/to-be-copied/example.txt')
    target = Path('/new/target/example.txt')
    fs.create_file(str(source))
    fs.create_file(str(target))

    # file does not exist
    action = Action(source_action, source, target)
    
    # file exists now and should lead to an error if performed again
    with pytest.raises(Exception):
        action.perform()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_file_to_directory(fs, source_action):
    source = Path('/from/to-be-copied/example.txt')
    target = Path('/to/target')
    fs.create_file(str(source))

    action = Action(source_action, source, target)
    action.perform()

    assert (target / 'example.txt').exists()

    if source_action == SourceAction.MOVE:
        assert not source.exists()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_directory_to_file(fs, source_action):
    source = Path('/from')
    target = Path('/to/example.txt')
    fs.create_dir(str(source))
    fs.create_file(str(target))

    action = Action(source_action, source, target)

    with pytest.raises(IOError):
        action.perform()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_directory_to_new_directory(fs, source_action):
    source = Path('/from/some-directory')
    target = Path('/to/some-directory')
    fs.create_dir(str(source))
    fs.create_file(str(source / 'example.txt'))
    fs.create_dir(str(target.parent))

    action = Action(source_action, source, target)
    action.perform()

    assert target.exists()

    # test also if moved
    if source_action == SourceAction.MOVE:
        assert not source.exists()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_copy_directory_to_existing_directory(fs, source_action):
    source = Path('/from/some-directory')
    target = Path('/to/another-directory')
    fs.create_dir(str(source))
    fs.create_file(str(source / 'example.txt'))
    fs.create_dir(str(target))

    action = Action(source_action, source, target)
    action.perform()

    assert (target / 'some-directory' / 'example.txt').exists()

    # test also if moved
    if source_action == SourceAction.MOVE:
        assert not source.exists()


@pytest.mark.parametrize('source_action', [SourceAction.COPY, SourceAction.MOVE])
def test_action_copy_directory_to_existing_directory_same_name(fs, source_action):
    source = Path('/from/some-directory')
    target = Path('/to/some-directory')
    fs.create_dir(str(source))
    fs.create_file(str(source / 'example.txt'))
    fs.create_dir(str(target))

    action = Action(source_action, source, target)
    action.perform()

    assert (target / 'example.txt').exists()

    # test also if moved
    if source_action == SourceAction.MOVE:
        assert not source.exists()


@pytest.fixture
def example_migration_sheet():
    return read_migration_sheet(EXAMPLE_FILE)


def _mock_directory_structure(fs):
    fs.create_dir('/source-directory/a/b')
    fs.create_file('/source-directory/c/d/Pipfile')
    fs.create_file('/source-directory/c/d/results/Thumbs.db')
    fs.create_file('/source-directory/c/d/scripts/example.py')
    fs.create_dir('/source-directory/c/e/data')
    fs.create_dir('/target-directory/c/e')


def test_read_migration_sheet(fs):
    fs.add_real_file(EXAMPLE_FILE)
    res = read_migration_sheet(EXAMPLE_FILE)

    assert res is not None


def test_read_migration_sheet_with_name(fs):
    fs.add_real_file(EXAMPLE_FILE)
    res = read_migration_sheet(EXAMPLE_FILE, 'NAME')
    assert res is not None


def test_read_migration_sheet_with_wrong_name(fs):
    fs.add_real_file(EXAMPLE_FILE)

    with pytest.raises(KeyError):
        read_migration_sheet(EXAMPLE_FILE, 'WRONG-NAME')


def test_sheet_to_actions(example_migration_sheet):
    actions = sheet_to_actions(example_migration_sheet)
    assert isinstance(actions, dict)
    assert len(actions) == 4


def test_perform_actions(example_migration_sheet, fs, caplog):
    _mock_directory_structure(fs)
    actions = sheet_to_actions(example_migration_sheet)

    with caplog.at_level(logging.WARNING):
        perform_actions(actions)

    # check if logged on missing actions
    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 2

    # check if deleted
    assert not os.path.exists('/source-directory/a')
    assert not os.path.exists('/target-directory/c/d/results/Thumbs.db')

    # check if moved
    assert os.path.exists('/target-directory/c/d')
    assert os.path.exists('/target-directory/c/d/scripts/example.py')

    # check if copied
    assert os.path.exists('/target-directory/c/e')
    assert os.path.exists('/target-directory/c/e/data')


def test_perform_actions_missing_source(example_migration_sheet, fs):
    fs.create_dir('/source-directory/a/b')
    fs.create_file('/source-directory/c/d/Pipfile')
    fs.create_file('/source-directory/c/d/results/Thumbs.db')
    fs.create_file('/source-directory/c/d/scripts/example.py')

    actions = sheet_to_actions(example_migration_sheet)
    with pytest.raises(IOError):
        perform_actions(actions)


def test_perform_actions_existing_target(example_migration_sheet, fs):
    _mock_directory_structure(fs)
    fs.create_file('/target-directory/c/d/Pipfile')

    actions = sheet_to_actions(example_migration_sheet)
    with pytest.raises(IOError):
        perform_actions(actions)


def test_perform_actions_copy_on_file(example_migration_sheet, fs):
    _mock_directory_structure(fs)
    fs.create_file('/target-directory/c/e/data')

    actions = sheet_to_actions(example_migration_sheet)
    with pytest.raises(IOError):
        perform_actions(actions)
