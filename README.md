# AITesterBlueprint3x

This repository contains a pytest automation framework for reservation API testing.
The actual project files live under the `Pytest-Automation-Framework/` folder.

## Python Virtual Environment

A Python virtual environment is an isolated Python environment used to keep project dependencies separate from the system Python. It is not part of pytest itself.

### Create the virtual environment

From the repository root:

```bash
cd /Users/kiranmaiwunnava/Pytest-Automation-Framework
python3 -m venv venv
```

This creates a local folder named `venv/` containing its own Python interpreter and site-packages.

### Activate the virtual environment

On macOS or Linux:

```bash
source venv/bin/activate
```

After activation, `python` and `pip` point to the environment inside `venv/`.

### Install dependencies

With the virtual environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -r Pytest-Automation-Framework/requirements.txt
```

### Run the tests

From the root of the repo, with the virtual environment active:

```bash
pytest Pytest-Automation-Framework/test_reservations.py -v
```

## Notes

- The tests are currently written to use mocked API responses via the `responses` library.
- The API configuration is loaded from `Pytest-Automation-Framework/config.py`, which reads `.env` values if present.
- If you want to run against a real API, update `API_BASE_URL` in `.env` and remove or adjust the mocking fixture in `Pytest-Automation-Framework/conftest.py`.
