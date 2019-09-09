# directory-tree-excel

A simple script to turn a directory tree into an excel spreadsheet for migrating directories using the shell command [tree](http://mama.indstate.edu/users/ice/tree/) and the python package [xlsxwriter](https://xlsxwriter.readthedocs.io/).

> **NOTE**: You will need at least `tree` version 1.7.0 to have the support of the JSON extract (option `-J`).

## Installation

To install the dependencies of this script you will need to have `pipenv` installed (see [Installing Pipenv](https://docs.pipenv.org/en/latest/install/#installing-pipenv)).

```shell
pipenv install
```

## Execute script

To turn a directory `d` into a spreadsheet `b.xlsx` call
```shell
pipenv run python create_sheet.py d b.xlsx
```