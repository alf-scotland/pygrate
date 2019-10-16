import pathlib
import os

import pytest

from pygrate.migrate import read_migration_sheet, sheet_to_actions, perform_actions


EXAMPLE_FILE = pathlib.Path(__file__).parent / '_resources' / 'example.xlsx'


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


def test_perform_actions(example_migration_sheet, fs):
    _mock_directory_structure(fs)
    actions = sheet_to_actions(example_migration_sheet)
    perform_actions(actions)

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
    fs.create_dir('/target-directory/c/d/d')

    actions = sheet_to_actions(example_migration_sheet)
    with pytest.raises(IOError):
        perform_actions(actions)


def test_perform_actions_copy_on_file(example_migration_sheet, fs):
    _mock_directory_structure(fs)
    fs.create_file('/target-directory/c/e/data')

    actions = sheet_to_actions(example_migration_sheet)
    with pytest.raises(IOError):
        perform_actions(actions)
