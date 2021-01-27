# **crawler**

[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/mit)

A simple web crawler.

Usage
```console
$ crawler [--options] URL
```

Example:
```console
$ crawler --nthreads 10 --output endpoints.json https://monzo.com/
```

You can use `--help` to print help message.
```console
$ python3 crawler.py --help
Usage: crawler.py [OPTIONS] URL

  Web crawler starts from URL to all found links under the same netloc.

Options:
  --nthreads INTEGER  Number of threads.  [default: 5]
  --output TEXT       Output path.  [default: (endpoints.json)]
  --all-links         Include all resources.
  --help              Show this message and exit.
```

# Installation
Install the cli tool using the following command:

```console
$ python3 setup.py install
```

# Development

For development of this tool, you need to install the required dependencies. (Use of virtual environments are strongly suggested)

```console
$ python3 -m virtualenv venv
$ source ./venv/bin/activate
# pip install -r requirements.txt
```

For running the unit tests:
```console
(venv) $ python3 -m unittest tests -v
```

# To do
- Handle redirects better.
- Write better tests.

***

Tested with Python 3.8.7 on macOS 10.15.7