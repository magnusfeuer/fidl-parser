#!/usr/bin/env python3
# (C) 2022 Magnus Feuer
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import getopt
from lark import Lark, logger, Tree, Token
import sys
import os
from pkg_resources import resource_string as resource_bytes
import logging
import json
from fidl_parser import parse_tree

def usage(name):
    print(f"Usage: {name} <idl-file>")

def dump_tree(node, indent=0):
    if isinstance(node, Tree):
        print(f"{' '*indent*2}{node.data}")
        for subnode in node.children:
            dump_tree(subnode, indent + 1)
        if len(node.children) == 0:
            print(f"{' '*(indent*2+2)}[empty]")
        else:
            print(f"{' '*(indent*2)}--")

    elif isinstance(node, Token):
        print(f"{' '*indent*2}{node.type}: {node.value} - {type(node.value)}")
    else:
        print(f"{' '*indent*2}<unknown>{node}")

if __name__ == "__main__":
    try:
        options, remainder = getopt.getopt(
            sys.argv[1:],
            's:i:',
            ['server=', 'id='])
    except getopt.GetoptError as err:
        print(err)
        usage(sys.argv[0])
        sys.exit(1)

    for opt, arg in options:
        if opt in ('-s', '--server'):
            pass # Future options
        elif opt in ('-i', '--id'):
            pass # Future options
        else:
            print("Unknown option: {}".format(opt))
            usage(sys.argv[0])
            sys.exit(255)

    if len(remainder) < 1:
        print("\nMising filename")
        usage(sys.argv[0])
        sys.exit(255)

    logger.setLevel(logging.DEBUG)
    fidl_grammar = resource_bytes('fidl_parser', 'francaidl.lark').decode('utf-8')
    lark_parser = Lark(fidl_grammar, start="root", parser="lalr", debug=True)

    for fidl_file_name in remainder:
        with open(fidl_file_name) as f:
            fidl_text = f.read()

        print(f"----------------")
        print(f"FILE: {fidl_file_name}")
        print(f"----------------")
        tree = lark_parser.parse(fidl_text)
        dump_tree(tree)
#        dict_tree = parse_tree.lark_to_dict(tree)
#        print(f"{json.dumps(dict_tree, indent=2)}")
        print("-------------------------")
        svc_tree = parse_tree.convert_fidl_tree(tree)
        print(f"{json.dumps(svc_tree, indent=2)}")
        print("\n")
