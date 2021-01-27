# **crawler**

[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/mit)

A simple web crawler. Output is printed and also written to path given in `--output` option.
```console
$ python3 crawler.py http://monzo.com/
```

You can use --help to print help message.
```console
$ python3 crawler.py --help
Usage: crawler.py [OPTIONS] URL

  Web crawler starts from URL to all found links under the same netloc.

Options:
  --nthreads INTEGER  Number of threads.  [default: 5]
  --output TEXT       Output path.  [default: (endpoints.txt)]
  --all-links         Include all resources.
  --help              Show this message and exit.
```

You can setup your virtual python environment with `virtualenv`:
```console
$ python3 -m virtualenv venv
$ source ./venv/bin/activate
# pip install -r requirements.txt
```

To run tests:
```console
$ python3 test_crawler -v
```

To do:
- Handle redirects better.
- Write better tests.
- Create `setup.py`.


Tested with Python 3.8.7 on macOS 10.15.7