# FrancaIDL parser.

This repo contains a FrancaIDL parser that reads `.fidl` files 
and produces a parse tree.

The system parses test cases from:
https://github.com/franca/franca/tree/master/tests/org.franca.connectors.idl.tests/testcases/model
https://github.com/franca/franca/tree/master/tests/org.franca.core.dsl.tests/model/testcases


# INSTALL

    pip3 install .
    
    
# RUN

    fidl_tool.py <franca-idl-file> ...

The parse tree for the specified FrancaIDL file will be printed

# RUN ALL TEST CASES

    fidl_tool.py $(find testcases -name '*.fidl')

All parse trees for all test files wll be printed


# TODO

## Resolve issues found in spec and test code.
(From `fidl_parser/francaidl.lark`)

### Issue in section 5.3.3 - Comparison operators
The actual symbols of the comparison operators are not specified.
However, C operators are used in `testcases/core_tests/evaluation/IntegerExpressions.fidl`
We'll use C operators for now.

### Issue in section 5.3.4 - Constant arithmetic operations
The actual symbols of the arithmetic operators are not specified.
We'll use C operators for now.


### Issue in section 5.3.5 - Boolean operators
The actual symbols of the arithmetic operators are not specified.
Not currently implemented

### Issue in section 5.6.3 - Contract transition actions
* `on set` transitions are in tests but not documented.
* `on respond` transitions are in tests but not documented.
* `on error` transitions are in tests but not documented.

### Issue in section 5.6.4 - Contract state variables
In `vars {...}` blocks we suddenly use `;` to terminate declarations according to the specs.

In `testcases/core_tests/contracts/ValidUsageOfErrorKeyWords.fidl` semicolons are used in the `vars {...}` block.

In `testcases/core_tests/Integertypes/70-IntegerTypes.fidl` they are not used.

We make semicolon opional for now.

### Issue in `testcases/core_tests/evaluation/IntegerExpressions.fidl`
The test file has the following code snippet:

	const Boolean r30 = s1->e1
	const UInt32 r31 = s1->e2
	const Boolean r40 = s2->f1->e1
	const UInt32 r41 = s2->f1->e2

The specification does not mention dereferencing struct members.

This is currently implemented.

## Resolve references

References to base classes, const variables, etc needs to be resolved
for easy access when traversing the parser tree.

## Implement deployment file parser


## Build a bridge to Service Catalog YAML tree.


