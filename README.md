DeepLog
======================
DeepLog is lightweight standalone but powerful log analysis command line tool. 


Installation
--------------------
```bash
 pip install deep-log
```


Main Features
--------------------
* 

Basic Usage
--------------------
* **search keyword** 
```bash
dl hello --target /tmp/ # search all lines in the files under folder /tmp which contain the word hello  
```
* **seach with filters**
```bash
dl  --target /tmp --filter="'hello' not in _record " #search all lines in the files under folder /tmp which not contain the word hello 
```
* **subscribe log change with keyword** 
```bash
dl hello -- target /tmp --subscribe #subscribe incoming change which contain keyword hello under /tmp folder
```

* **data analysis**
```bash
dl hello --target /tmp/ --analyze="df.groupby(['_record']).size()" # find all lines which contain hello then groupby by line content

hello Jack\n     2
hello James\n    2
hello Jim\n      2
hello Joe\n      4
hello Rain\n     4
hello World\n    2 
```

Documentation
--------------------
the office documents is hosted in 

License
--------------------
[BSD 3](LICENSE)












