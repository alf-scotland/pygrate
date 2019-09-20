# pygrate

A simple thing to turn a directory tree into an excel spreadsheet for migrating directories using the shell command [tree](http://mama.indstate.edu/users/ice/tree/) and the python package [xlsxwriter](https://xlsxwriter.readthedocs.io/) and a small script to execute the migration.

> **NOTE**: You will need at least `tree` version 1.7.0 to have the support of the JSON extract (option `-J`).

## Installation

```shell
pip install git+https://github.com/alf-scotland/pygrate.git@master#egg=pygrate
```

## Create migration sheet

To turn a directory `<a>` into a spreadsheet `<b.xlsx>` call
```shell
pygrate-create <a> <b.xlsx>
```

## Perform migration

Once the migration sheet is filled out the migration can be performed calling
```shell
pygrate-migrate <b.xlsx>
```

## Development

To install the dependencies for development of this package you will need to have `pipenv` installed (see [Installing Pipenv](https://docs.pipenv.org/en/latest/install/#installing-pipenv)).
