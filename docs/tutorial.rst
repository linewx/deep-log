======================
Tutorial
======================

Configuration
--------------
DeepLog can be executed without config file. however, without config file, the functionalities of DeepLog is very limited, every log item can only be treated as a string. but with pre-defined loggers in config file, DeepLog can know more about logs, not just a string line by line, but also the log time, the log level, error etc.
in general, config file is a yaml file named ``config.yaml`` under config root ``~/.deep_log/``.

**example**
this is what config file look like:

.. code-block:: yaml

    variables:
      loghub_root: /tmp/loghub
    root:
      parser:
        name: DefaultLogParser
        params:
          pattern: (?P<content>.*?)
      path: /
    loggers:
      - name: apache
        path: '{loghub_root}/Apache'
        modules:
          - apache
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


components
^^^^^^^^^^^

* ``loggers``, logger definitions, the attributes is exactly the same as root. following attributes can be used in this component:
    =================================   =============================================
    modules                             description
    =================================   =============================================
    :ref:`path<dl_logger_path>`          where the logger used, always '/' for root
    :ref:`parser<dl_parser>`             define how to parse the log item
    :ref:`handlers<dl_handlers>`         define how to handle the parsed log items
    :ref:`filters<dl_filters>`           define how to filter parsed log items
    :ref:`template<dl_templates>`        define which template to refer
    =================================   =============================================

* ``root``, root is specific logger which define the default logger action, it will be matched if no any other loggers matched.
* ``variables``, define variables which can be used in logger definitions.
* ``templates``, define templates which can be reused in loggers. see :ref:`templates<dl_templates>` for detail.


.. _dl_logger_path:

logger path hierarchy
^^^^^^^^^^^^^^^^^
logger hierarchy is very like file system structure with inheritance. take following as an example:

.. code-block:: text
    /tmp/loghub
    ├── /tmp/loghub/Apache
    │  └── /tmp/loghub/Apache/Apache_2k.log
    ├── /tmp/loghub/Proxifier
    │  └── /tmp/loghub/Proxifier/Proxifier_2k.log
    ├── /tmp/loghub/Spark
    │  └── /tmp/loghub/Spark/Spark_2k.log
    └── /tmp/loghub/templates

and there three loggers and root defined:
    * ``apache``, with path */tmp/loghub/Apache/*
    * ``proxifier``, with path */tmp/loghub/Proxifier/*
    * ``loghub`` with path */tmp/loghub/*

when analyzing logs:
    * if target logs under folder /tmp/loghub/Apache/ , DeepLog will match ``apache`` logger definition, and will parse logs as apache log.
    * if target logs under folder /tmp/loghub/Proxifier/ , DeepLog will match ``proxifier`` logger definition, and will parse logs as apache log.
    * if target logs under folder /tmp/loghub/Spark/ , there is no specific loggers defined for Spark log, DeepLog will try to match its parent node, in this case, `loghub` logger will be used.
    * if target logs under folder /opt/, there is no any logger matching the path, the default ``root`` logger will be used.

.. _dl_command:

Command line Options
---------------------

* ``-c``, ``--config`` config root dir
* ``-l``, ``--filter`` log filter
* ``-t``, ``--meta-filter`` filter by meta object extracted from file meta information
* ``-n``, ``--file-name`` filter by file name
* ``-m``, ``--format`` print format
* ``-s``, ``--subscribe`` subscribe data change, processing unbouned change
* ``-o``, ``--order-by`` field to order by
* ``-r``, ``--reverse`` reverse order, only work with order-by
* ``--limit`` limit query count
* ``--window`` processing window size
* ``--workers`` workers count run in parallel
* ``--recent`` query by time to now, for example,
* ``-y``, ``--analyze`` dsl expression for analysis, integrate with pandas
* ``--tags`` query by tags
* ``--modules`` query by modules
* ``--template`` logger template
* ``--distinct`` remove duplicated records by specified fields separated by comma
* ``--template_dir`` logger template dir
* ``--name-only`` show only file name
* ``--full`` display full
* ``--include-history`` subscribe history or not, only work with subscribe mode
* ``--pass-on-exception`` default value if met exception
* ``-D``, ``append`` definitions
* ``--target`` log dirs to analyze
* ``pattern`` default string pattern to match

.. _dl_parser:

Parser
--------------

parser is used to parse log line from string to structured data. in DeepLog, currently, there is only one parser named **DefaultLogParser**.

DefaultLogParser
^^^^^^^^^^^^^^^^

DefaultLogParser use `python regular expression named groups`__ to parse log line as a object. with following attributes:

.. __: https://docs.python.org/3/library/re.html

* **pattern**, pattern is named groups regular expression match pattern.


**examples**:

the log line::

[Sun Dec 04 04:52:15 2005] [error] mod_jk child workerEnv in error state 7


with parser config

.. code-block:: yaml

  parser:
    name: DefaultLogParser
    params:
      pattern: \[(?P<time>.*?)\] \[(?P<level>.*?)\] (?P<message>.*)

the parsed result will be

.. code-block:: json
    {
        'time': 'Sun Dec 04 04:52:15 2005',
        'level': 'error',
        'message': 'mod_jk child workerEnv in error state 7'
    }


.. _dl_handlers:

handlers
-------------
handler is used to transfer data which is parsed from parser.DeepLog provide several following handlers:

.. note::
    handler can be defined more than one, and executed in sequence.

TypeLogHandler
^^^^^^^^^^^^^^
the type of value in parsed object from parser is always string, TypeLogHandler is always used to convert the value to suitable type. and with following attributes:

* **definitions**, define a serial of type definitions, one type definition has three sub fields:
    + field, the field name which will be transferred.
    + type, the type to transfer.
    + format, only used when type is datetime, which define the string `time format`__ used by strftime function.

.. __: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior


**examples**:

with above parser, we have parsed result

.. code-block:: json

    {
        'time': 'Sun Dec 04 04:52:15 2005',
        'level': 'error',
        'message': 'mod_jk child workerEnv in error state 7'
    }


with handler configuration:

.. code-block:: yaml

  handlers:
  - name: TypeLogHandler
    params:
      definitions:
        - field: time
          format: '%a %b %d %H:%M:%S %Y'
          type: datetime
  path: /

the above handler will transfer the field *time* in parsed result to datetime object with format ``%a %b %d %H:%M:%S %Y``, the result will be ``{'time': Datetime.Datetime(2005, 12, 4, 4, 52, 15), ...}``


TagLogHandler
^^^^^^^^^^^^^^^
TagLogHandler is used to tag log line with specified condition. with following attributes:

* ``definitions``, define a serial of tag condition definitions, one tag condition has two sub fields:
    + name, tag name.
    + condition, define the match condition if tag the name.

**examples**

the handler configuration is:

.. code-block:: yaml

    handlers:
      - name: TagLogHandler
        params:
          definitions:
            - name: error
            - condition: "'error' == level or 'error' in message"

the above handler will tag log line as error when level is 'error' or 'error' in message. with above parsed result, the handler output will {tags: Set('error'), ...}, which can be

StripLogHandler
^^^^^^^^^^^^^^^
StripLogHandler is a simple handler, which is used to strip all the string values。there is one attribute:

* ``fields``, define the string fields to strip. if no fields provided, all the string fields will be stripped.


RegLogHandler
^^^^^^^^^^^^^^^
RegLogHandler is used to extract values from specific field, which work very likely what DefaultLogParser do. attributes:

* ``pattern``, pattern is `named groups regular expression`__ match pattern.

.. __: https://docs.python.org/3/library/re.html

**examples**

.. code-block:: yaml

    handlers:
      - name: TypeLogHandler
        params:
          definitions:
            - field: time
              format: '%m-%d-%Y %H:%M:%S.%f'
              type: datetime
      - name: RegLogHandler
        params:
          pattern: "\n(?P<exception>.*?Exception):(?P<exception_message>.*)"
          field: "_record"



the above example show using RegLogHandler to parse exception name and messages.

.. _TransformLogHandler_:

TransformLogHandler
^^^^^^^^^^^^^^^^^^^
TransformLogHandler use dsl expression to transform record object with new fields. which has attributes:

* **definitions**, define a serial of type definitions, one type definition has three sub fields:
    + name, the field to be created
    + value, the value expression.

**examples**

.. code-block:: yaml

    handlers:
      - name: TransformLogHandler
        params:
          name: is_today
          value: "time.date() == datetime.datetime.today().date()"


the above show using TransformLogHandler to create new field to identify the log date is today or not.


.. _dl_filters:

Filters
--------------
filter is used to filter the log item in the log files.

.. _dsl_filter:

DslFilter
^^^^^^^^^^
DslFilter is a filter which accept a python expression as a filter condition. with attributes:

* ``filter``, a `dsl expression<dl_dsl>'_, which evaluate filter condition.
* ``pass_on_exception``, bool type, mark the  condition as True or False if met condition


.. _dl_meta_filters:

MetaFilters
--------------
metaFilters basically is used to filter by log file meta info not log file content.there two kind of meta filters:

NameFilter
^^^^^^^^^^
NameFilter is used to filter file name based on `Unix filename pattern matching`_ syntax. which take two arguments:

.. _Unix filename pattern matching:  https://docs.python.org/3/library/fnmatch.html

* ``patterns``, define the file name match patterns, which split by comma ``,``.
* ``exclude_patterns``, define excluded file name match patterns, which split by comma ``,``.

**examples**

.. code-block:: yaml

    meta_filters:
      - name: NameFilter
        params:
          patterns: '*.log'
          exclude_patterns: '*audit.log'


the above means we analyze all the files with extetion name is .log but exclude audit log.


DslMetaFilter
^^^^^^^^^^^^^
DslMetaFilter is a more powerful filer than name filer, which can use python expression the filter file based file meta info. which can take one argument:

* ``filter``, which is :ref:`dsl expression<dl_dsl>`

**example**

.. code-block:: yaml

    meta_filters:
      - name: NameFilter
        params:
          filter: _size > 0


the above means all empty files will be ignored


.. _dl_templates:

Template System
------------------
logs with the same type always have the same log format. to parse/handle/filter log with the same patterns, user can define those configurations as template.which can be shared by multiple loggers or command line.
there are two ways to define templates:

.. _dl_template_config:

templates in config
^^^^^^^^^^^^^^^^^^^^^^^^^
templates can be defined directly in `config.yaml`_, see following snippet:

.. _config.yaml: https://raw.githubusercontent.com/linewx/deep-log/master/samples/template/config.yaml

.. code-block:: yaml

    templates:
      - name: apache
        path: '{loghub_root}/Apache'
        modules:
          - apache
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
    loggers:
      - name: apache
        path: '{loghub_root}/Apache'
        modules:
          - apache
        template: apache

we define template under ``templates`` section, and then can be referenced in loggers with template name.


.. _dl_template_repo:

Template Repo
^^^^^^^^^^^^^^^^^^

besides :ref:`templates config<_dl_template_config>`, templates can also be defined in template repo. we can define all templates under ``templates`` folder under ``config root``.
see following apache template for example, you can find full example `here`__:

.. __: https://github.com/linewx/deep-log/tree/master/samples/template-repo

.. code-block:: yaml

    name: apache
    path: '{loghub_root}/Apache'
    modules:
      - apache
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

the above example define apache log template, which can be referenced in loggers.

.. _dl_dsl:

Dsl Expressions
---------------
dsl expression in DeepLog in a python expression for different usage with different context, there are four usages in general:

* ``filter``, is used to filter log content, which can be ``--filter`` option value, or filter params in :ref:`dsl_filter` definitions. :ref:`record_object` and :ref:`_module_object` are included in context.

* ``handler``, is advanced usage in :ref:`TransformLogHandler`, both :ref:`record_object` and :ref:`_module_object` are included in context.

* ``meta filer``, is only applied on meta filer, which can be ``--meta-filer`` option value or filter param in :ref:`DslMetaFilter` definitions. :ref:`meta_object` and :ref:`_module_object` are included in context.

* ``analyze``, is dedicated for analysis function. which can be set in ``--analyze`` command line option.  both :ref:`record_object` and :ref:`_module_object` are included in context. besides, user can manipulate the df(DataFrame) property in this situation.


.. _meta_object:

Meta Object
--------------
meta object

- built-in meta properties

============= ==========================
property      description
============= ==========================
_name         filename
_writable     file is writable or not
_readable     file is readable or not
_executable   file is executable or not
_ctime        file creaction time
_mtime        file modified time
_actime       file access time
_size         file size
_basename     file base name
============= ==========================


.. _record_object:

Record Object
--------------

built-in properties
^^^^^^^^^^^^^^^^^^^^
* :ref:`meta_object`
* ``_record``, file line
* ``df``, log items data frame

.. note::
    property ``df`` can only be invoked in analysis function.


user-defined items
^^^^^^^^^^^^^^^^^^^

* parsed result by parser, for example, parsed time property.
* generate by by :ref:`TransformLogHandler`

**examples**

following is the examples returned by DeepLog:

.. code-block:: json

    {
        '_name': '/tmp/apache_v2.log' # meta object property, filename
        '_size': 10000, # meta object property, file size
        'time': Datetime(2025, 12, 04, 4, 52, 5) # user parsed property, parsed by from string 'Sun Dec 04 04:52:05 2005'
    }

.. _module_object:

Built-in Modules
-------------------
there are kinds of python modules exposed which can be invoked in dsl Expressions:

=================================   =============================================
modules                             description
=================================   =============================================
`re`_                                Regular expression operations
`path`_                              Common pathname manipulations
`datetime`_                          Basic date and time types
=================================   =============================================


.. _re: https://docs.python.org/3/library/re.html
.. _path: https://docs.python.org/3/library/os.path.html
.. _datetime: https://docs.python.org/3/library/datetime.html




