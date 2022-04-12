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

# verbose, hints
poetry run flake8 
```

## Running the tool manually
```
poetry run capgains ...
poetry run capgains calc eggs.csv 2021
```

## Creating a release
Once you have all the changes you desire for a release, do the following. Note that
we follow [semantic versioning](https://semver.org/) for our projects.

1. Create a new branch
2. Bump up the release numbers in `pyproject.toml` and `capgains/__init__.py`
3. Push + create PR. Once PR is ready, merge it into the master branch.
4. Create a new release using the Github release tools. This will create a new tag and
kick off a CI build. The ensuing CI build will notice that this is a tagged commit and
will package the project and push it to PyPI.
