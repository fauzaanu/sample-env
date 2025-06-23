# Sample Env

Sample Env is a utility to generate a sample `.env` file for Python projects by detecting environment variable references in the code. This tool helps developers quickly identify and document the environment variables their project uses.

## Features

- Detects environment variable references such as:
  - `os.getenv("VAR")`
  - `os.environ.get("VAR", ...)`
  - `from os import environ; environ.get("VAR", ...)`
  - `os.environ["VAR"]`
  - `from os import environ; environ["VAR"]`
- Generates a `.env.sample` file listing all detected environment variables.

## Installation

You can install Sample Env directly from the GitHub repository:

```bash
pip install git+https://github.com/fauzaanu/sample-env.git
```

## Usage

To generate a `.env.sample` file, run the following command in the root of your Python project:

```bash
python -m sample_env.main
```

This will create a `.env.sample` file in the current directory with all detected environment variables.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

Fauzaan Gasim - [hello@fauzaanu.com](mailto:hello@fauzaanu.com)
