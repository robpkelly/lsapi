#! /usr/bin/env python
"""Recursively list the public names exposed by a Python package, formatted as a readable tree"""

import importlib
import argparse
from colors import color
import inspect


# Unicode patterns for drawing trees to stdout
_tree_default = argparse.Namespace(
    line='│ ',
    fork='├─',
    stop='└─',
    open='  '
)
_tree_compat = argparse.Namespace(
    line='| ',
    fork='|-',
    stop='+-',
    open='  '
)
_tree_space = argparse.Namespace(
    line='  ',
    fork='  ',
    stop='  ',
    open='  '
)

# ANSI colors for use with the ansicolors package
colormap = dict(
    package=2,  # green
    module=10,  # light green
    type=11,  # yellow
    function=6,  # cyan
    method=14,  # light cyan
    kwarg=25,  # sea green
    arg=26,  # teal
    default=15,  # white
)

known_namespaces = {}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('package', type=str, help="package (or sub-package) to inspect")
parser.add_argument('-p', '--private', action='store_true', help="include private names")
parser.add_argument('-m', '--magic', action='store_true', help="include magic names")
parser.add_argument('-a', '--all', action='store_true', help="include all names (equivalent to `-pm')")
parser.add_argument('-c', '--canonical', action='store_true',
                    help="try to display names under the namespace where they are defined")
parser.add_argument('-x', '--external', action='store_true',
                    help="show names exposed by packages that are not under the given root package")
parser.add_argument('-s', '--signatures', action='store_true',
                    help="display signatures for callables (functions, methods, classes)")
parser.add_argument('-u', '--ugly', action='store_true',
                    help="use basic ASCII for tree drawing (for terminal emulators with spotty unicode support)")
parser.add_argument('-U', '--no-tree', action='store_true', help="do not draw trees")
parser.add_argument('-C', '--no-color', action='store_true', help="do not colorize output")
parser.add_argument('-D', '--max-depth', action='store', type=int,
                    help="do not show names nested beyond this depth from the given root package (which has depth 0)")
args = parser.parse_args()

package = importlib.import_module(args.package)

tree = _tree_default
if args.ugly:
    tree = _tree_compat
if args.no_tree:
    tree = _tree_space

if args.no_color:
    def color(s, fg=None, bg=None, style=None):  # noqa F811
        return s


def is_magic(name):
    return name.startswith('__') and name.endswith('__')


def is_private(name):
    return name.startswith('_') and not is_magic(name)


def is_package(value):
    return inspect.ismodule(value) and hasattr(value, '__path__')


def in_package(package, other):
    """Infer whether or not `other` is defined in `package`"""
    if hasattr(other, '__package__'):
        module_name = other.__package__
    elif hasattr(other, '__module__'):
        module_name = other.__module__
    else:
        return False
    return module_name.startswith(package.__name__)


def fmt_type(type_):
    if isinstance(type_, type):
        return type_.__name__
    else:
        return str(type_)


def fmt_parameter(parameter):
    # normalize type annotation if present
    if parameter.annotation is not inspect._empty:
        name = f"{parameter.name}::{fmt_type(parameter.annotation)}"
    else:
        name = parameter.name

    if parameter.name in ['cls', 'self']:
        # highlight special arguments
        return color(str(parameter), fg=colormap['default'], style='bold')
    elif parameter.kind == inspect._ParameterKind.VAR_POSITIONAL:
        # bold *args
        return f"*{color(name, fg=colormap['arg'], style='bold')}"
    elif parameter.kind == inspect._ParameterKind.VAR_KEYWORD:
        # bold **kwargs
        return f"**{color(name, fg=colormap['kwarg'], style='bold')}"
    elif parameter.kind == inspect._ParameterKind.POSITIONAL_OR_KEYWORD:
        if parameter.default is not inspect._empty:
            # format keyword arg
            default_str = f'"{parameter.default}"' if isinstance(parameter.default, str) else str(parameter.default)
            return f"{color(name, fg=colormap['kwarg'])}={color(default_str, fg=colormap['default'])}"
        else:
            # format positional argument
            return color(name, fg=colormap['arg'])
    else:
        # weird edge cases (/ or *)
        return color(str(parameter), fg=colormap['arg'])


def fmt_name(name, value, color_=None):
    type_ = 'package' if is_package(value) else fmt_type(type(value))
    color_ = color_ or colormap.get(type_, 'white')
    if args.signatures and callable(value):
        try:
            signature = inspect.signature(value)
            sig_str = ', '.join(
                [fmt_parameter(param) for param in inspect.signature(value).parameters.values()]
            )

            name = f"{name}({sig_str})"

            if signature.return_annotation is not inspect._empty:
                name = f"{name} -> {fmt_type(signature.return_annotation)}"
        except ValueError:
            name = f"{name}({color('???', fg='red', style='bold')})"

    return f"{color(name, fg=color_)}::{type_}"


def name_filter(name):
    # name-based filters
    if not args.all:
        if not args.private and is_private(name):
            return False
        if not args.magic and is_magic(name):
            return False
    return True


def get_source_file_nonesafe(value):
    try:
        return inspect.getsourcefile(value) or value.__dict__.get('__file__', '')
    except TypeError:
        return '__main__'


def is_canon(namespace, value):
    """Is the given value a canonical member of the namespace?

    Namespaces-value membership is not a one-to-one mapping so we create this
    idea of "canon" to build an intuitive map. This is needed because python's
    import mechanism does not make a distinction between a name being defined
    and a name being imported.

    Loosely, the "canonical" namespace of a value is the namespace to which the
    value "belongs"

    Specifically, a value is canon in a namespace if one of the following holds:

    1. The namespace is a package and one of the following holds:
      a. the value is a module defined in a file in the namespace's directory
      b. the value is a subpackage defined in a directory in the namespace's directory
      c. the value is defined in the namespace's __init__.py file
    2. The namespace is a module and the value was defined in the namespace's source file.
    3. The namespace is a class and the value is defined as a member of the namespace.

    Some of the above cases are impossible to determine with certainty through
    inspection, so we just make a calculated gamble.
    """
    if hasattr(namespace, '__wrapped__'):
        namespace = namespace.__wrapped__
    if hasattr(value, '__wrapped__'):
        value = value.__wrapped__

    # builtins can be ruled out automatically
    if inspect.isbuiltin(value):
        return False

    if inspect.ismodule(namespace):
        if hasattr(namespace, '__path__'):
            # package
            if inspect.ismodule(value):
                if hasattr(value, '__path__'):
                    # subpackage value
                    return value.__path__[0].startswith(namespace.__path__[0])
                else:
                    # module value
                    return get_source_file_nonesafe(value).startswith(namespace.__path__[0])
            else:
                # other value
                return get_source_file_nonesafe(value) == inspect.getsourcefile(namespace)
        else:
            # module
            return get_source_file_nonesafe(value) == inspect.getsourcefile(namespace)
    else:
        # class
        if inspect.ismethod(value):
            # Should this account for MRO?
            return value.__self__ is namespace
        elif inspect.ismethoddescriptor(value):
            return value.__objclass__ is namespace
        elif inspect.isfunction(value):
            return value.__qualname__.rsplit('.', 1)[0] == namespace.__name__
        elif isinstance(value, property):
            # this is pretty sketchy
            return any([
                getattr(value, attr).__qualname__.rsplit('.', 1)[0] == namespace.__name__
                for attr in ['fget', 'fset', 'fdel']
                if inspect.isfunction(getattr(value, attr))
            ])
        else:
            return True


def predicate_factory(namespace):
    if args.canonical:
        return lambda value: is_canon(namespace, value)
    else:
        return lambda value: True


def _handle_name(source_ns, name, value, depth, tab, subtab):
    line = tab + fmt_name(name, value)
    if inspect.ismodule(value) or inspect.isclass(value):
        if not (args.external or in_package(package, value)):
            note = color(f'[external {fmt_type(type(value))} {value.__name__}]', fg='red', style='bold')
            print(f"{line} {note}")
        elif value in known_namespaces:
            note = color(f'[see {known_namespaces[value]}]', fg='red', style='bold')
            print(f"{line} {note}")
        else:
            print(line)
            if args.max_depth is not None and depth >= args.max_depth:
                print(subtab + tree.stop + color('[...]', fg='red', style='bold'))
            else:
                known_namespaces[value] = f'{source_ns.__name__}.{name}'
                walk_names(value, depth + 1, subtab)
    else:
        print(line)


def walk_names(namespace, depth, tab=''):
    names = []
    classes = []
    modules = []

    # Organize all names by category
    for name, value in inspect.getmembers(namespace, predicate_factory(namespace)):
        if name_filter(name):
            if inspect.ismodule(value):
                modules.append((name, value))
            elif inspect.isclass(value):
                classes.append((name, value))
            else:
                names.append((name, value))

    all_names = names + classes + modules
    if len(all_names) > 0:
        for name, value in all_names[:-1]:
            _handle_name(namespace, name, value, depth, tab=tab + tree.fork, subtab=tab + tree.line)

        name, value = all_names[-1]
        _handle_name(namespace, name, value, depth, tab=tab + tree.stop, subtab=tab + tree.open)


print(fmt_name(args.package, package))
walk_names(package, depth=1)
