"""
    dependencies
    ~~~~~~~~~~~~

    Dependency Injection for Humans.

    :copyright: (c) 2016 by Artem Malyshev.
    :license: LGPL-3, see LICENSE for more details.
"""

import inspect

import six

__all__ = ['Injector', 'DependencyError']


class InjectorBase(type):

    def __new__(cls, name, bases, namespace):

        new = super(InjectorBase, cls).__new__

        if len(bases) == 0:
            return new(cls, name, bases, namespace)

        if len(bases) > 1:
            raise DependencyError(
                'Multiple inheritance is not allowed')

        ns = {}

        for attr in ('__module__', '__doc__', '__weakref__', '__qualname__'):
            try:
                ns[attr] = namespace.pop(attr)
            except KeyError:
                pass

        if any((x for x in namespace
                if x.startswith('__') and x.endswith('__'))):
            raise DependencyError('Magic methods are not allowed')

        for attr in ('let', 'c'):
            if any((x for x in namespace if x == attr)):
                raise DependencyError(
                    '{0!r} redefinition is not allowed'.format(attr))

        for k, v in six.iteritems(namespace):
            if inspect.isclass(v) and not use_object_init(v):
                spec = inspect.getargspec(v.__init__)
                args = spec[0] + [spec[1], spec[2]]
                if k in args:
                    raise DependencyError(
                        '{0!r} is a circle dependency in the {1!r} '
                        'constructor')

        def __rawattr__(self, attrname):
            """Namespace based attribute lookup."""

            try:
                attribute = namespace[attrname]
            except KeyError:
                if Injector in self.__class__.__bases__:
                    raise AttributeError(
                        '{0!r} object has no attribute {1!r}'
                        .format(name, attrname))
                else:
                    parent = self.__class__.__bases__[0]
                    instance = parent()
                    attribute = parent.__rawattr__(instance, attrname)
            return attribute

        def __getattr__(self, attrname):
            """Injector attribute lookup.

            Constructor based Dependency Injection happens here.

            """

            attribute = self.__rawattr__(attrname)
            if inspect.isclass(attribute) and not attrname.endswith('_cls'):
                if use_object_init(attribute):
                    return attribute()
                init = attribute.__init__
                args, varargs, kwargs, defaults = inspect.getargspec(init)
                if defaults is not None:
                    have_defaults = len(args) - len(defaults)
                else:
                    have_defaults = len(args)
                arguments = []
                keywords = {}
                for n, a in enumerate(args[1:], 1):
                    try:
                        arguments.append(__getattr__(self, a))
                    except AttributeError:
                        if n < have_defaults:
                            raise
                        else:
                            arguments.append(defaults[n - have_defaults])
                if varargs is not None:
                    arguments.extend(__getattr__(self, varargs))
                if kwargs is not None:
                    keywords.update(__getattr__(self, kwargs))
                return attribute(*arguments, **keywords)
            else:
                return attribute

        @property
        def c(self):
            """Dependency Injector subclass alias."""

            return self.__class__

        ns['__rawattr__'] = __rawattr__
        ns['__getattr__'] = __getattr__
        ns['c'] = c

        klass = new(cls, name, bases, ns)
        return klass()


class Injector(six.with_metaclass(InjectorBase)):
    """Default dependencies specification DSL.

    Classes inherited from this class may inject dependencies into
    classes specified in it namespace.

    """

    @classmethod
    def let(cls, **kwargs):
        """Produce new Injector with some dependencies overwritten."""

        return type(cls.__name__, (cls,), kwargs)


class DependencyError(Exception):
    """Broken dependencies configuration error."""

    pass


def use_object_init(cls):
    """Check if cls.__init__ will get us object.__init__."""

    if '__init__' in cls.__dict__:
        return False
    else:
        if cls.__bases__ == (object,):
            return True
        else:
            for base in cls.__bases__:
                if not use_object_init(base):
                    return False
            else:
                return True
