# (C) 2022 Magnus Feuer
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
import lark
import json
from . import type_manager

indent_level = 0
func_stack = []
def indent(func):
    def wrap(*args, **kwargs):
        global indent_level
        global current_func
        func_stack.append(func.__name__)
        indent_level = indent_level + 2
        res = func(*args, **kwargs)
        indent_level = indent_level - 2
        func_stack.pop()
        return res

    return wrap

def ind():
    global indent_level
    return f"{' '*indent_level}{func_stack[-1]}(): "

@indent
def get_lark_tree_entries_by_name(state, lark_tree, lark_entry):
    return [ child for child in lark_tree.children if isinstance(child, lark.Tree) and child.data == lark_entry ]

@indent
def get_lark_tree_token_by_type(state, lark_tree, lark_type):
    for child in lark_tree.children:
        if isinstance(child, lark.Token) and child.type == lark_type:
            return child

    return None

def process_lark_tree(state, lark_tree, parse_map):
    result = {}
    for (map_func, *arg) in parse_map:
        func_res = map_func(state, lark_tree, *arg)
        if not func_res:
            continue

        result.update(func_res)

    return result


@indent
def process_lark_tree_entry(state, lark_tree, lark_entry, parse_map):
    # Locate the dictionary entry we want to process
    print(f"{ind()}Called for {lark_tree.data}[{lark_entry}]")

    entries = get_lark_tree_entries_by_name(state, lark_tree, lark_entry)
    if entries == []:
        print(f"{ind()}No match for {lark_entry}. Return False.")
        return None

    if len(entries) > 1:
        print(f"{ind()}Too many matches, {len(entries)} in {lark_entry}. exit.")
        raise Exception(f"Too many matches for {lark_tree.data}[{lark_entry}]-> {len(entries)}")

    result = process_lark_tree(state, entries[0], parse_map)
    print(f"{ind()}Result: {type(result)} - {len(result)} elements")
    return result

@indent
def create_entry(state, lark_tree, lark_type, target_name, target_type=str):
    res = get_lark_tree_token_by_type(state, lark_tree, lark_type)
    if not res:
        print(f"{ind()}Not found: {lark_type}")
        return None

    print(f"{ind()}Found {lark_type} = {res} -> {target_name}")
    if target_type == int and res.value=="minInt":
        res.value = -9223372036854775808

    if target_type == int and res.value=="maxInt":
        res.value = 9223372036854775807

    return { target_name: target_type(res.value) }


@indent
def create_target_dictionary(state, lark_tree, lark_entry, target_entry, parse_map):
    print(f"{ind()}Called for {lark_tree.data}[{lark_entry}] -> {target_entry}")
    res = process_lark_tree_entry(state, lark_tree, lark_entry, parse_map)
    if not res:
        print(f"{ind()}Got None back. No action.")
        return None

    print(f"{ind()}Create new {target_entry} dictionary with: {type(res)} - {len(res)} elements.")
    return { target_entry: res }


@indent
def create_target_list(state, lark_tree, lark_entry, target_entry, parse_map):
    print(f"{ind()}Called for {lark_tree.data}[{lark_entry}] -> {target_entry}")
    entries = get_lark_tree_entries_by_name(state, lark_tree, lark_entry)
    if entries == []:
        return None

    res_list = []
    for entry in entries:
        res = process_lark_tree(state, entry, parse_map)
        if res is not None:
            res_list.append(res)

    return { target_entry: res_list }


@indent
def aggregate_list(state, lark_tree, element_name, parse_map):
    result = []

    for (map_func, *arg) in parse_map:
        res = map_func(state, lark_tree, *arg)
        if res and element_name in res:
            result.extend(res[element_name])

    print(f"{ind()}Will aggregate {len(result)} elements into {element_name}")
    return { element_name: result }

@indent
def create_entry_from_type_token(state, lark_tree, target_entry):

    conversion_map = {
        'FIDL_INT8': 'int8',
        'FIDL_UINT8': 'uint8',
        'FIDL_INT16': 'int16',
        'FIDL_UINT16': 'uint16',
        'FIDL_INT32': 'int32',
        'FIDL_UINT32': 'uint32',
        'FIDL_INT64': 'int64',
        'FIDL_UINT64': 'uint64',
        'FIDL_FLOAT': 'float',
        'FIDL_DOUBLE': 'double',
        'FIDL_BOOLEAN': 'boolean',
        'FIDL_STRING': 'string',
        'FIDL_BYTEBUFFER': 'binary'
    }

    print(f"{ind()}Called for {lark_tree.data} -> {target_entry}")
    if len(lark_tree.children) == 0:
        print(f"{ind()}{lark_tree.data} has no tokens. No action")
        return None

    if len(lark_tree.children) > 1:
        return None

    if not isinstance(lark_tree.children[0], lark.Token):
        return None

    token_type = lark_tree.children[0].type
    return { target_entry: conversion_map.get(token_type, f'UNKNOWN: {token_type}') }


@indent
def process_one_of(state, lark_tree, options):
    print(f"{ind()}Called for {lark_tree.data}")
    for (map_func, *arg) in options:
        res = map_func(state, lark_tree, *arg)
        if res:
            return res

    return None


@indent
def create_static_entry(state, lark_elem, token_name, token_value):
    return { token_name: token_value }

def push_namespace(state, lark_elem, ns_type, parse_map):

    ns_name = get_lark_tree_token_by_type(state, lark_elem, ns_type)
    if ns_name is None:
        raise Exception(f"Could not find {ns_type}.")


    new_ns = type_manager.NameSpace(ns_name.value)
    state['ns'].add_namespace(new_ns)
    state['ns'] = new_ns

    res = process_lark_tree(state, lark_elem, parse_map)

    state['ns'] = state['ns'].parent

    if state['ns'] is None:
        raise Exception("Popped last element on namespace stack.")

    return res


def add_datatype(state, lark_elem, parse_map):
    res = process_lark_tree(state, lark_elem, parse_map)

    # Add datatype to symbol table for current
    # namestate

    print(f"{ind()}ADDING DATATYPE---------------- {res['name']}")

    state['ns'].add_type(type_manager.Type(res['name'], res))

    return res

@indent
def resolve_datatypes(state, lark_tree, parse_map):

    def _resolve_datatype(dict_tree):
        resolved_result = None
        for k, v in dict_tree.items():
            print(f"{ind()} Checking {k}")

            # Is this the already resolved datatype?
            if k == '_resolved_datatype':
                continue

            if k == 'datatype':
                # Is this a native type?
                if v in [ 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32',
                          'int64', 'uint64', 'float', 'double','boolean','string', 'binary' ]:
                    resolved_result = v
                    continue

                # Resolve type as local name
                res_dt = state['ns'].resolve_type(v)

                if not res_dt:
                    # Resolve type as fully qualified name
                    res_dt = state['ns'].resolve_type(f".{v}")
                    if not res_dt:
                        raise Exception(f"Could not resolve type name {v}")

                resolved_result = res_dt.info
                continue

            if isinstance(v, dict):
                _resolve_datatype(v)
                continue

            if isinstance(v, list):
                [ _resolve_datatype(v_elem) for v_elem in v ]
                continue

        if resolved_result is not None:
            dict_tree['_resolved_datatype'] = resolved_result

    if len(parse_map) != 1:
        raise Exception(f"resolve_datatypes need a parse map with lenght one. Got {len(parse_map)}")

    (map_func, *arg) = parse_map[0]
    res = map_func(state, lark_tree, *arg)
    _resolve_datatype(res)
    return res

@indent
def evaluate_expression(state, lark_tree, expr_name, target_name):
    tree_map = {
        "expression": lambda expr_elem: eval_tree(expr_elem),
        "primitive_type": lambda expr_elem: eval_tree(expr_elem),
        "defined_typs": lambda expr_elem: eval_tree(expr_elem),
        "arithmetic_op": lambda expr_elem: eval_tree(expr_elem),
        "arit_add": lambda expr_elem: eval_expression(expr_elem, "lhs") + eval_expression(expr_elem, "rhs"),
        "arit_sub": lambda expr_elem: eval_expression(expr_elem, "lhs") - eval_expression(expr_elem, "rhs"),
        "arit_mul": lambda expr_elem: eval_expression(expr_elem, "lhs") * eval_expression(expr_elem, "rhs"),
        "arit_div": lambda expr_elem: eval_expression(expr_elem, "lhs") / eval_expression(expr_elem, "rhs"),
        "arit_div": lambda expr_elem: eval_expression(expr_elem, "lhs") / eval_expression(expr_elem, "rhs"),
    }

    token_map = {
        "FIDL_CONST_TRUE": lambda token: True,
        "FIDL_CONST_FALSE": lambda token: False,
        "FIDL_CONST_INT": lambda token: int(token),
        "FIDL_CONST_HEX": lambda token: int(token, 16),
        "FIDL_CONST_BIN": lambda token: int(token, 2),
        "FIDL_CONST_FLOAT": lambda token: float(token),
        "FIDL_CONST_DOUBLE": lambda token: float(token),
        "FIDL_CONST_STRING": lambda token: token.strip('"'),
        "FIDL_NAME": lambda token: print(f"WE DO NOT EVAL NAMES: {token.value}") + sys.exit(255)
    }

    @indent
    def eval_token(expr_token):
        print(f"{ind()}Evaluating {expr_token}")


    @indent
    def eval_tree(expr_tree):
        print(f"{ind()}Evaluting {expr_tree.data}")

        for expr in expr_tree.children:
            print(f"{ind()}Checking {expr}")
            if isinstance(expr, lark.Token):
                if expr.type in token_map:
                    print(f"{ind()}Evaluating token {expr.type} = {expr.value}")
                    return token_map[expr.type](expr.value)
                else:
                    print(f"{ind()}No token lambda available to evaluate {expr.type}")
                    continue
            else:
                if expr.data in tree_map:
                    print(f"{ind()}Evaluating tree {expr.data}")
                    return tree_map[expr.data](expr)
                else:
                    print(f"{ind()}No tree lambda available to evaluate {expr.data}")
                    continue

        print(f"{ind()}No hit")
        return None

    @indent
    def eval_expression(expr_tree, expr_name):
        print(f"{ind()}Searching for {expr_name} in {expr_tree.data}")

        for expr in expr_tree.children:
            print(f"{ind()}Checking {expr}")
            if not isinstance(expr, lark.Tree) or expr.data != expr_name:
                print(f"{ind()}Nope")
                continue

            return eval_tree(expr)

        print(f"{ind()}No hit")
        return None

    print(f"{ind()}Evaluating {lark_tree.data}/{expr_name}")
    return { target_name: tree_map[expr_name](lark_tree) }


non_array_type_map =  ( process_one_of, [
    ( process_lark_tree_entry, "primitive_type", [
        ( process_one_of, [
            ( process_lark_tree_entry, "fidl_integer", [
                ( create_target_dictionary, "integer_range", "range", [
                    (create_entry, "MIN_RANGE", "min_range", int),
                    (create_entry, "MAX_RANGE", "max_range", int)
                ])
            ]),
            ( create_entry_from_type_token, "datatype" ),
            ( create_static_entry, "datatype", "int64"), # Default the options above return None
        ])
    ]),
    ( process_lark_tree_entry, "defined_type", [
        ( create_entry, "FIDL_NAME", "datatype" ),
    ])
])


type_map = ( process_one_of, [
    non_array_type_map,
    ( process_lark_tree_entry, "implicit_array", [
        non_array_type_map,
        ( create_static_entry, "array_size", 0 ),
    ]),
    ( process_lark_tree_entry, "explicit_array", [
        non_array_type_map,
        ( create_static_entry, "array_size", 0 ),
    ])
])

conversion_map = [
    ( create_entry, "FIDL_NAME", "name" ), # Package name
    ( create_target_dictionary, "type_collection", "types", [
        ( create_entry, "FIDL_NQ_NAME", "name"),
        ( push_namespace, "FIDL_NQ_NAME", [
            ( process_lark_tree_entry, "type_collection_body", [
                ( resolve_datatypes, [
                    ( aggregate_list, "datatypes", [
                        ( create_target_list, "base_enumeration", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "type", "enumeration"),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                ( create_target_list, "enumerator_member", "members", [
                                    ( create_entry, "FIDL_NQ_NAME", "name" ),
                                    ( evaluate_expression, "expression", "value" )
                                ])
                            ])
                        ]),
                        ( create_target_list, "base_union", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "type", "union" ),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                ( create_target_list, "member", "members", [
                                    ( create_entry, "FIDL_NQ_NAME", "name" ),
                                    ( evaluate_expression, "expression", "value" ),
                                    type_map
                                ])
                            ])
                        ]),
                        ( create_target_list, "base_struct", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "type", "struct" ),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                ( create_target_list, "member", "members", [
                                    ( create_entry, "FIDL_NQ_NAME", "name" ),
                                    ( evaluate_expression, "expression", "value" ),
                                    type_map
                                ])
                            ])
                        ]),
                        ( create_target_list, "typedef", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "type", "union" ),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map
                            ])
                        ]),
                        ( create_target_list, "explicit_array", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "array_size", 0 ),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map
                            ])
                        ]),
                        ( create_target_list, "implicit_array", "datatypes", [
                            ( add_datatype, [
                                ( create_static_entry, "array_size", 0 ),
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ]),
    ( create_target_dictionary, "interface", "interfaces", [
        ( create_entry, "FIDL_NQ_NAME", "name"),
        ( push_namespace, "FIDL_NQ_NAME", [
            ( resolve_datatypes, [
                ( process_lark_tree_entry, "interface_body", [
                    #
                    # Methods
                    #
                    ( create_target_list, "method", "methods", [
                        ( create_entry, "FIDL_NQ_NAME", "name"),
                        ( create_target_dictionary, "arg_in", "in", [
                            ( create_target_list, "member", "members", [
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map,
                            ])
                        ]),
                        ( create_target_dictionary, "arg_out", "out", [
                            ( create_target_list, "member", "members", [
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map,
                            ])
                        ])
                    ]),
                    #
                    # Broadcast
                    #
                    ( create_target_list, "broadcast", "events", [
                        ( create_entry, "FIDL_NQ_NAME", "name"),
                        ( create_target_dictionary, "arg_out", "out", [
                            ( create_target_list, "member", "members", [
                                ( create_entry, "FIDL_NQ_NAME", "name"),
                                type_map
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ])
]


@indent
def resolve_types(current_namespace, name, tree):


    if isinstance(tree, list):
        for elem in tree:
            resolve_types(current_namespace, name, elem)
        return None

    if not isinstance(tree, dict):
        return None

    print(f"{ind()}Resolving {name}")

    if 'datatype' in tree:
        print(f"{ind()}Found datatype")

        res = current_namespace.resolve_type(f"{tree['datatype']}")
        if not res:
            # Resolve type as fully qualified name
            res = current_namespace.resolve_type(f".{tree['datatype']}")
            if not res:
                raise Exception(f"Could not resolve type name {tree['datatype']}")

        tree['$resolved_datatype'] = res
        print(f"{ind()}Resolved to: {res}")

    # Traverse namespaces and recursively resolve
    if 'namespaces' in tree:
        for ns in tree['namespaces']:
            resolve_types(current_namespace[ns['name']], ns['name'], ns)

    # Check for any lists to traverse:
    for k, v in tree.items():
        print(f"{ind()}Checking {k}")
        # Filter out stuff we don't need
        if k == 'namespaces' or k =='datatype':
            continue

        resolve_types(current_namespace, k, v)

    return None


def convert_fidl_tree(lark_tree: lark.Tree):
    state = {
        'ns': type_manager.NameSpace('root')
    }
    res = process_lark_tree(state, lark_tree, conversion_map)
    state['ns'].dump()
    return res
