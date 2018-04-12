# storescripts

Snap store random collection of scripts


## `view_metrics.py`

`view_metrics.py [snap name]` collects *absolute* (depends on special permissions)
and *public* metrics and prints a comparision table like:

```
$ ./view_metrics.py surl
Using authorization from `store.auth` file ...
Collecting publisher metrics for surl ...
Collecting public metric for surl ...
Distro              Absolute  Log10 scale      Linear    Log10 from Linear
----------------  ----------  -------------  --------  -------------------
ubuntu/17.10              27  0.79              0.415                0.875
ubuntu/16.04              19  0.705             0.29                 0.82
ubuntu/18.04              10  0.55              0.155                0.73
ubuntu-core/16             3  0.265             0.045                0.55
ubuntu/17.04               2  0.165             0.03                 0.495
solus/3.999                1  -                 0.015                0.39
elementary/0.4.1           1  -                 0.015                0.39
parrot/3.11                1  -                 0.015                0.39
peppermint/8               1  -                 0.015                0.39

```
