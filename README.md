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

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
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