# NoMus

Project for providing services to the population.

## Structure

The project follows the `src` layout structure:

```text
NoMus/
├── src/
│   └── nomus/          # Main package
│       ├── main.py     # Entry point
│       └── ...
├── pyproject.toml
└── ...
```

## Clone

```bash
git clone https://github.com/imchrm/NoMus.git
cd NoMus
```

## Install Poetry

Official installation [guide](https://python-poetry.org/docs/#installation).

## Setup Dependencies of Project

1. Make sure you're inside your "NoMus" project.
2. To install the virtual environment specifically within your project, rather than in a single location for all project environments, run the following command:

```bash
poetry config virtualenvs.in-project true
```
, and then install dependencies:
```bash
poetry install
```

## Activate Enviroment

1. Windows:
```bash
.venv\Scripts\activate
```
2. Linux/MacOS:
```bash
source .venv/bin/activate
```

## Usage

To run the application:

```bash
poetry run python -m nomus.main
```

Or if you are in the virtual environment:

```bash
nomus
```

## Development

The source code is located in `src/nomus`.