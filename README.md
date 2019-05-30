# PyREG
Linux in-line forensic parser for Windows registry files. Uses python-registry library.

usage: PyREG.py [-h] [-k KEY] [-d {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}] [--deleted] [path]

positional arguments:

  path               Registry Hive Path

optional arguments:

  -h, --help         show this help message and exit
  
  -k KEY, --key KEY  show key values and subkeys, overrides -d, use
                     'ROOT\Keyname\Keyname\...'
                     
  --d {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}, --depth {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
                     set the recursion depth for lookup of subkeys. If none 
                     is given - shows subkeys of a given key and their 
                     values (equal to 1)
                     
  --deleted          add deleted hive values to the end of the output. If 
                     -k is not given, shows all delited hive keys and values
