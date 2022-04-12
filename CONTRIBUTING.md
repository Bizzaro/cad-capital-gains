# Contributing
Below is a small guide for getting your environment set up and running/testing the tool. We use [poetry](https://python-poetry.org/docs/) to manage dependencies.

## Getting started and getting the latest dependencies
```bash
python3 -m venv virtual-env 
source virtual-env/bin/activate
pip3 install poetry codecov
poetry install
```

## Unit tests
```
poetry run pytest --cov-report term --cov=capgains
```
```
Run the test suite against all the supported python versions and the linter in an isolated environment. You will need to have the supported python versions installed otherwise you will get a `InterpreterNotFoundError`

poetry run tox
```

## Autoformatter
```
# modifies files in place
poetry run autopep8 -i **/*.py 

# linter
poetry run flake8 
```

## Running the tool manually
```
poetry run capgains ...
poetry run capgains calc eggs.csv 2021
```

## Creating a release
TBD