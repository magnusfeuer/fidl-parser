# (C) 2022 Magnus Feuer
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

#
# Type management
#
#  A namespace tree populated by types.
#  Each type hosts a dictionary of arbitrary data.
#
class Base:
    def __init__(self, name: str):
        self._parent = None
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def root(self):
        tmp = self
        while True:
            if tmp.parent == None:
                return tmp
            tmp = tmp.parent



    def path(self):
        res = []
        tmp = self
        while tmp != None:
            res.insert(0, tmp)
            tmp = tmp.parent

        return res

    def path_string(self, separator='.'):
        res = ''
        for path_elem in self.path():
            if res == '':
                res = path_elem.name
                continue

            res = f"{res}{separator}{path_elem.name}"

        return res

    def dump(self):
        pass

class NameSpace(Base):
    def __init__(self, name: str):
        super().__init__(name)
        self._namespaces = {}
        self._types = {}

    def add_namespace(self, namespace):
        namespace.parent = self
        if namespace.name not in self._namespaces:
            self._namespaces[namespace.name] = namespace
            return None

        #
        # Adopt child
        #
        new_child = self._namespaces[namespace.name]
        [ new_child.add_namespace(ns) for ns in namespace.namespaces]
        self._namespaces[namespace.name] = namespace

        #
        # Add types to child
        # Overwrite any existing types.
        #
        self._types.update(namespace.types)
        return None

    def add_type(self, type):
        self._types[type.name] = type
        type.parent = self
        return None

    def resolve_type_list(self, path_list):
        # Are we at the end of the path at a type?
        if len(path_list) == 1:
            if path_list[0] in self.types:
                return self.types[path_list[0]]

            return None

        # We are still traversing the namespace tree

        # Do we have the next element in the path list
        # as one of our hosted namespaces?
        #
        if not path_list[0] in self.namespaces:
            return None

        # Recurse into hosted namespace
        return self.namespaces[path_list[0]].resolve_type_list(path_list[1:])


    def resolve_type(self, sym_name, separator='.'):
        if self.parent is not None and sym_name[0] == separator:
            #
            # Check if we are not root and type name is absolute path
            #
            return self.root.resolve_type(sym_name[1:])

        return self.resolve_type_list(sym_name.split(separator))

    @property
    def types(self) -> dict:
        return self._types

    @property
    def namespaces(self) -> dict:
        return self._namespaces

    def dump(self):
        [ print(f"{self.path_string()}.{k} = {v.info}") for k,v in self.types.items() ]
        [ v.dump() for k,v in self.namespaces.items() ]

class Type(Base):
    def __init__(self, name: str, info: dict):
        super().__init__(name)
        self._info = info

    @property
    def info(self):
        return self._info

