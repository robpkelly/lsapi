# lsapi

A quick script to display the public names exposed by a Python package as a tree.

## setup

```console
$ sudo pip install -r requirements.txt
$ ln -s $PWD/lsapi.py ~/bin/lsapi
```

## usage

```console
$ lsapi -h
usage: lsapi [-h] [-p] [-m] [-a] [-c] [-x] [-s] [-u] [-U] [-C] package

Recursively list the public names exposed by a package, formatted as a
readable tree

positional arguments:
  package           package (or sub-package) to inspect

optional arguments:
  -h, --help        show this help message and exit
  -p, --private     include private names
  -m, --magic       include magic names
  -a, --all         include all names (equivalent to `-pm')
  -c, --canonical   try to display names under the namespace where they are
                    defined
  -x, --external    show names exposed by packages that are not under the
                    given root package
  -s, --signatures  display signatures for callables (functions, methods,
                    classes)
  -u, --ugly        use basic ASCII for tree drawing (for terminal emulators
                    with spotty unicode support)
  -U, --no-tree     do not draw trees
  -C, --no-color    do not colorize output
```

## notes

`lsapi` inspects packages by loading them through python's import mechanism and
inspecting the result, instead of compiling and inspecting the AST. This allows
for limited operability with packages distributed as wheels and C-language
extensions, but also means that names imported elsewhere will likely be listed
under the "wrong" namespace. In other words, this script tries to be _complete_
and _correct_, but may be _counterintuitive_. With the `-c` flag, `lsapi` will
attempt to show names where they were canonically defined, but it can't catch
everything.

If you see strange symbols in `lsapi`'s output, like �, ▯, or
[mojibake](https://en.wikipedia.org/wiki/Mojibake), it's probably because your
terminal emulator doesn't know how to render the glyphs `lsapi` uses to draw
trees. Use the `-u` or `-U` flags, but also consider switching to a modern
terminal emulator.
