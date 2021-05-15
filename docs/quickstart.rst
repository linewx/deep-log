======================
Quickstart
======================

A minimal example
------------------
suppose we'd like to analyze  `Apache Log
<https://raw.githubusercontent.com/logpai/loghub/e293fb24b5d64f97c3277c0ca6ca63ef1008d721/Apache/Apache_2k.log>`_. like following::
  
[Sun Dec 04 04:52:05 2005] [notice] jk2_init() Found child 6737 in scoreboard slot 8
[Sun Dec 04 04:52:12 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
[Sun Dec 04 04:52:12 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
[Sun Dec 04 04:52:12 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
[Sun Dec 04 04:52:15 2005] [error] mod_jk child workerEnv in error state 6
[Sun Dec 04 04:52:15 2005] [error] mod_jk child workerEnv in error state 7
[Sun Dec 04 04:52:15 2005] [error] mod_jk child workerEnv in error state 7

How to work like grep
----------------------

search all error message::

$ grep error apache_v2.log # using grep
$ dl error --target apache_v2.log # using DeepLog
  
search all error message and with state 6::

$ grep error apache_v2.log | grep 'state 6' # using grep
$ dl --filter="'error' in _record and 'state 6' in _record" --target apache_v2.log # using DeepLog

Not Just grep - groupby function
---------------------------------
how to get the log count groupby log level?

grep not fully support such case, but with DeepLog we can do like with following steps:


1. setup a config file named `config.yaml`__. under ~/.deep_log, with content::

    root:
      parser:
        name: DefaultLogParser
        params:
          pattern: \[(?P<time>.*?)\] \[(?P<level>.*?)\] (?P<message>.*)
      handlers:
      - name: TypeLogHandler
        params:
          definitions:
            - field: time
              format: '%a %b %d %H:%M:%S %Y'
              type: datetime
      path: /
    loggers:



  within root section, there are two components :ref:`parser<dl_parser>` and :ref:`handlers<dl_handlers>`.

.. __: https://raw.githubusercontent.com/linewx/deep-log/master/samples/sample1/config.yaml

2. then analyze with groupby function

.. code-block::text

    $ dl --target /tmp/loghub/Apache/ --analyze="df.groupby(['level']).size()"
    error      595
    notice    1405
    dtype: int64

How about more than one type of logs?
--------------------------------------
we define the etl processing function in root logger in above. how about one more type of logs? let's say we have another `proxifier log`_ with different log format to analyze.how to define parser in config file?

.. __: https://raw.githubusercontent.com/logpai/loghub/master/Proxifier/proxifier_2k.log

we can define more loggers under loggers section in `config.yaml`_.

.. __: https://raw.githubusercontent.com/linewx/deep-log/master/samples/multi-loggers/config.yaml

.. code-block::

loggers:
  - name: apache
    path: '{loghub_root}/Apache'
    modules:
      - apache
    parser:
        ...
  - name: proxifier
    path: '{loghub_root}/Proxifier'
    modules:
      - proxifier
    ...


then we can use different logger to analyze different type of logs.

share configuration between loggers
--------------------------------------
sometimes, we process logs within different folders in the same way. to share the configuration, we can define the processors as :ref:`template<dl_templates>`:

.. code-block::

templates:
  - name: apache
    path: '{loghub_root}/Apache'
    modules:
      - apache
    parser:
      name: DefaultLogParser
      params:
        pattern: \[(?P<time>.*?)\] \[(?P<level>.*?)\] (?P<message>.*)
    ...
  - name: proxifier
    path: '{loghub_root}/Proxifier'
    modules:
      - proxifier
    parser:
      name: DefaultLogParser
      params:
      pattern: \[(?P<time>.*?)\] (?P<process>[^\ ]+) - (?P<message>.*)
    ...

loggers:
  - name: apache
    path: '{loghub_root}/Apache'
    modules:
      - apache
    template: apache
  - name: proxifier
    path: '{loghub_root}/Proxifier'
    modules:
      - proxifier
    template: proxifier

as shown above, loggers can reference the template definitions in templates section by template name. for advanced usage, you can also define template in `template repo<dl_template_repo>`


how to process unbounded data
------------------------------
logs are always increased by time, how to monitor the log changes?

DeepLog provide a option ``--subscribe`` to do this, which is quite powerful that it can subscribe the log changes and treat them a data stream to process.

.. code-block::

$ dl --subscribe --filter="'error' == level"

it will print out the error message incoming logs, like `tail -f <filename>| grep error`

what I can do next?
--------------------------
as a log analysis system, the main problems are always two parts:

how to find what i want
^^^^^^^^^^^^^^^^^^^^^^^^^^
DeepLog provide rich functionalities help user to find what they want

* ``--filter``, DeepLog can use  :ref:`python dsl expression<dl_dsl_expression>`  as a filter to get what users really want to.
* ``--name-filter``, DeepLog provided name filter which can filter file name directly. you can refer to :ref:`NameFilter<dl_name_filter>` for the pattern definitions.
* ``--meta-filter``, DeepLog provided a more powerful file filter which can filter log file by file metadata. you can refer to :ref:`DslMetaFilter<dl_meta_filter>` for the pattern definitions.

how to analyze what i found
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DeepLog also provide lots of functions to support data analysis:

* ``--analyze``, the most powerful part in DeepLog is the integration with `pandas`_. you can leverage pandas analysis function in analyze options.

.. __: https://pandas.pydata.org/

* ``--order-by``, user can order by parsed log items by specific columns.
* ``--distinct``, user can remove duplicated log items with same value with user specified columns.
* ``--subscribe``, with subscribe mode, user can process unbounded log data like streaming processing.



one more thing
---------------------
how to speed up log processing if met too much logs to handle?

DeepLog support multiple processing, user specific the processors to run in parallel by the option ``--workers``.

.. code-block::

    $ dl error --target /logs --workers=8

it will launch 8 processes to work in parallel for log analysis.



   




