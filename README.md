# Smart checksum

A python script wrapping tools like md5sum, sha256sum for a bit more convenience in handling 
and keeping track of checksums.
Checksums will be stored in a JSON "DB" for checking. Checks will also be recorded to keep
track of file "health" 

# Installation & Requirements

1. simply clone & make *smart_checksum.py* executable
2. check & adjust dictionary in *smart_checksum.py* to point to correct binaries:

```
checksum_tools = {
    'md5': 'md5sum',
    'sha256': 'sha256sum'
}
```


Requires only >python3.6.7 (tested with 3.6.7 on Ubuntu, might work with older py3 as well) and of course
the tools / binaries to calculate the checksums (at least md5 / md5sum)

# Usage

The script will work recursivly through target folder and calculates all checksum that are not
already in the DB.
Run with --check to check against DB file (should be in target dir)

```
usage: smart_checksum.py [-h] [--checksum CHECKSUM] [--db DB] [--check]
                         [--max_age MAX_AGE] [--lastok] [--force]
                         [--save_often] [--verbose]
                         target

smart_checksum - python warpped checksum calc&check

positional arguments:
  target               base folder with files to be checked

optional arguments:
  -h, --help           show this help message and exit
  --checksum CHECKSUM  Checksum type to use - default md5 - possible options:
                       ['md5', 'sha256']
  --db DB              Filename for checksum database in json format - default
                       smart_sums_db.json
  --check              If given check sums in db
  --max_age MAX_AGE    Specify max age of last check to do recheck / recalc of
                       checksum - in combination with --check. Default: 1m -
                       iT i = integer and T = [d (days), w (weeks), m (month),
                       y (years)
  --lastok             Run this in case you get WRONG checksum to check for
                       last OK entries
  --force              If given all checksum will be recalculated
  --save_often         If given DB will be saved every time after a new
                       checksum was calculated
  --verbose            spams your screen
```
