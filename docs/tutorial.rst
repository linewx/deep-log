======================
Tutorial
======================

Configuration
--------------
config file

.. _dl_parser:

Parser
--------------

.. class:: DefaultLogParser()

    + params
        - pattern

.. _dl_handlers:

handlers
-------------
handlers 

.. _dl_filters:

Filters
--------------
filters

.. _dl_meta_filters:

MetaFilters
--------------
metaFilters

.. _dl_templates:

Templates
--------------
templates

.. _dl_dsl:

DslExpression
--------------
dsl expression


Meta Object
--------------
meta object

- built-in items

  - *_name*: filename
  - *_writable*: file is writable or not
  - *_readable*: file is readable or not
  - *_executable*': file is executable or not
  - *_ctime*: file creaction time
  - *_mtime*: file modified time
  - *_actime*: file access time
  - *_size*: file size
  - *_basename*: file base name
   

Record Object
--------------

* built-in items

  - *all meta object*
  - *_record*, file line   

* user-defined items
  
  - parsed result by parser
  - transformed by handlers

* examples

following is the examples returned by DeepLog.

::

    {
        '_name': '/tmp/apache_v2.log' # meta object property, filename
        '_size': 10000, # meta object property, file size
        'time': Datetime(2025, 12, 04, 4, 52, 5) # user parsed property, parsed by from string 'Sun Dec 04 04:52:05 2005'
    }










