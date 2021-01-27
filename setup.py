from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

requirements = [
    'click',
    'requests',
    'bs4',
    'validator_collection'
]

test_requirements = [
]

setup(
    name='crawler',
    version='0.9',
    description="A simple web crawler",
    long_description=readme,
    author="Batuhan Ceylan",
    author_email='batuhan@batuhanceylan.com',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'crawler=crawler.crawler:crawler',
            ],
        },
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
