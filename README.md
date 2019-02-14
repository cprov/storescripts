# storescripts

Snap store random collection of scripts

## Setup

```
$ python3 -mvenv storescripts
$ . storescripts/bin/activate
$ pip install -r requirements.txt
```

## `verify_deltas.py`

It verifies delta availability and performance for a given snap promotion.

```
$ ./verify_deltas.py -h
usage: verify_deltas.py [-h] [--version] [-v]
                        [-a {amd64,arm64,armhf,i386,ppc64el,s390x}]
                        [-c {candidate,beta,edge}]
                        SNAP_NAME

check snap delta availability

positional arguments:
  SNAP_NAME

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --debug           Prints request and response headers
  -a {amd64,arm64,armhf,i386,ppc64el,s390x}, --architecture {amd64,arm64,armhf,i386,ppc64el,s390x}
  -c {candidate,beta,edge}, --candidate {candidate,beta,edge}
```

By default, it evaluates the `candidate => stable promotion on amd64`, along with a collection of
known revisions released in past media (ubuntu relelases):

```
./verify_deltas.py core
Snap:      core (99T7MUlRhtI3U0QFgl5mXXESAiSwt776)
Promoting: candidate
Candidate: 6405 (91.0M)
Deltas:
  4486: 50.6M / saves 44 %
  4571: 50.6M / saves 44 %
  4650: 50.5M / saves 44 %
  4830: 50.3M / saves 45 %
  4917: 50.0M / saves 45 %
  5742: 44.8M / saves 51 %
  5897: 42.0M / saves 54 %
  6034: 35.8M / saves 61 %
  6130: 33.8M / saves 63 %
  6350: 15.4M / saves 83 %
```

A different promotion context and architecture can be specified:

```
$ ./verify_deltas.py nextcloud -c edge -a armhf
Snap:      nextcloud (njObIbGQEaVx1H4nyWxchk1i8opy4h54)
Promoting: edge
Candidate: 11558 (181.8M)
Deltas:
  11341: 102.0M / saves 44 %
```
