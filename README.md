# pygrate

A simple thing to turn a directory tree into an Excel Workbook for migrating directories using the shell command [tree](http://mama.indstate.edu/users/ice/tree/) and the python package [xlsxwriter](https://xlsxwriter.readthedocs.io/) and a small script to execute the migration.

> **NOTE**: You will need at least `tree` version 1.7.0 to have the support of the JSON extract (option `-J`).

## Installation

```shell
pip install git+https://github.com/alf-scotland/pygrate.git@master#egg=pygrate
```

## Create migration sheet

To turn a directory `<directory>` into a Excel Workbook `<workbook.xlsx>` call
```shell
pygrate-create <directory> <workbook.xlsx>
```

## Fill out migration sheet

All files within the generated migration sheets should be addressed with an action. The action has to be one of `Ignore`, `Copy`, `Move`, or `Delete`. If `Copy` or `Move` were specified a valid target directory needs to be specified.

If the source and target paths are both directories with the same name (ignoring case differences) and the action is either `Copy` or `Move`, the migration will attempt to copy or move all elements in the source directory to the target directory, respectively.

The migration will not overwrite files and fail when executed.

## Perform migration

Once the migration sheet is filled out the migration can be performed calling
```shell
pygrate-migrate <workbook.xlsx>
```

To test if the migration is performed as desired the migration can be executed in a dry run modus that simply loggs the actions that would be performed:
```shell
pygrate-migrate --dry-run <workbook.xlsx>
```

The argument `--sheet <sheet-name>` allows to point to a specific sheet inside the provided workbook, should it contain more than one migration plan.

## Development

To install the dependencies for development of this package you will need to have `pipenv` installed (see [Installing Pipenv](https://docs.pipenv.org/en/latest/install/#installing-pipenv)).
