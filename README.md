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
usage: lsapi [-h] [-p] [-m] [-a] [-c] [-x] [-s] [-A] [-u] [-U] [-C]
             [-D MAX_DEPTH]
             package

Recursively list the public names exposed by a Python package, formatted as a
readable tree

positional arguments:
  package               package (or sub-package) to inspect

optional arguments:
  -h, --help            show this help message and exit
  -p, --private         show private names
  -m, --magic           show magic names
  -a, --all             show all names (equivalent to `-pm')
  -c, --canonical       try to show names under the namespace where they are
                        defined
  -x, --external        show names exposed by packages that are not under the
                        given root package
  -s, --signatures      show signatures for callables (functions, methods,
                        classes)
  -A, --aliases         show aliased (imported) namespaces
  -u, --ugly            use basic ASCII for tree drawing (for terminal
                        emulators with spotty unicode support)
  -U, --no-tree         do not draw trees
  -C, --no-color        do not colorize output
  -D MAX_DEPTH, --max-depth MAX_DEPTH
                        do not show names nested beyond this depth from the
                        given root package (which has depth 0)
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
