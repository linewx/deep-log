DeepLog
======================
DeepLog is lightweight standalone but powerful log analysis command line tool. 


Installation
--------------------
```bash
 pip install deep-log
```

Architecture
--------------------

Main Features
--------------------
* 

Examples
--------------------
* **search keyword** 
```bash
dl hello --target /tmp/ # search all lines in the files under folder /tmp which contain the word hello  
```
* **subscribe log change with keyword** 
```bash
dl hello -- target /tmp --subscribe #subscribe incoming change which contain keyword hello under /tmp folder
```

* **data analysis**
```bash
dl hello --target /tmp/ --analyze=df.groupby(['_content']).size() # 
```














