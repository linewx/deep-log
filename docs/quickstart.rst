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

2.




   




