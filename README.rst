======================
DeepLog
======================
.. image:: https://img.shields.io/pypi/v/deep-log.svg?style=flat
      :target: https://pypi.python.org/pypi/deep-log

.. image:: https://readthedocs.org/projects/deep-log/badge/?version=latest
    :target: http://deep-log.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

DeepLog is lightweight standalone but powerful log analysis command line tool. 

Installation
--------------------

install deep-log using pip::

    $ pip install deep-log

Main Features
--------------------

* search from target logs by keyword or filter condition which is written in python
* subscribe target log changes which match user-defined condition
* integrate with `pandas`_,which can used to do data analysis based on the log content.
* customized ETL processing
* support multiple data type in filters and data analysis

.. _pandas: https://pandas.pydata.org/

Basic Usage
--------------------
* search keyword

.. code-block:: text

    $ dl hello --target /tmp/ # search all lines in the files under folder /tmp which contain the word hello

* search with filters

.. code-block:: text

    $dl  --target /tmp --filter="'hello' not in _record " #search all lines in the files under folder /tmp which not contain the word hello

* subscribe log change with keyword

.. code-block:: text

    $dl hello -- target /tmp --subscribe #subscribe incoming change which contain keyword hello under /tmp folder

* data analysis

.. code-block:: text

    $dl hello --target /tmp/ --analyze="df.groupby(['_record']).size()" # find all lines which contain hello then groupby by line content

    hello Jack\n     2
    hello James\n    2
    hello Jim\n      2
    hello Joe\n      4
    hello Rain\n     4
    hello World\n    2


Documentation
--------------------
the official documentation is hosted in https://deep-log.readthedocs.io/en/latest/


Further Steps
---------------------

* add index engine to accelerate query efficiency
* integrate plot functionalities
* enhance analysis engine by introducing decision engine
* rule-based analysis template engine
* package management to deliver bundled ETL && Analysis
* machine learning integration
* support more data sources
* distributed log collections


















