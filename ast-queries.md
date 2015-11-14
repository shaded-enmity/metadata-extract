Python AST Queries
==================

All queries below are in the XPath-like format for the `redhawk` program and are supposed to be executed like:
```bash
redhawk query 'QUERY' FILES
```

#### Lookup `license` definition inside `setup` function call
```
'**/CallFunction@{ n.function.name == "setup" }/**/DefineVariable@[name="license"]/*'
```

#### Lookup `License` definition inside `setup` function classifiers section
```
'**/CallFunction@{ n.function.name == "setup" }/**/DefineVariable@[name="classifiers"]/*/Constant@{ n.value[:7] == "License" }'
```

#### Find value of variable `LIC` defined in the global scope
```
'Assignment/**/ReferVariable@[name="LIC"]'
```

#### Find return value of function `get_license` defined in the global scope
```
'DefineFunction@{ n.name == "get_license" }/**/Return'
```

#### Find `install_requires` in `setup` function call
```
'**/CallFunction@{ n.function.name == "setup" }/**/DefineVariable@[name="install_requires"]/*'
```

#### Find `packages` information in `setup` function call
```
'**/CallFunction@{ n.function.name == "setup" }/**/DefineVariable@[name="packages"]/*'
```

#### Find out if `setup` calls `find_packages`
```
'**/CallFunction@{ n.function.name == "setup" }/**/DefineVariable@[name="packages"]/**/CallFunction@{ n.function.name == "find_packages" }'
```

#### Find `try-catch` checked imports
```
'**/TryCatch@{ any(x.type.name == "ImportError" for x in n.exception_handlers) }/*/ModuleAlias'
```

#### Find `class` definitions
```
'**/DefineClass'
```

#### Find methods definitions per class
```
'**/DefineClass/**/DefineFunction'
```

#### Find all member functions with `self` as first argument
```
'**/DefineClass/**/DefineFunction/FunctionArguments/@[name="self"][0, 0]'
```

#### Find all static functions
```
'**/DefineClass/**/DefineFunction/FunctionArguments@{ len(n.arguments) == 0 }'
```

#### Finding functions with `@staticmethod` decorator
```
'**/DefineClass/**/FunctionDecorator@{ n.decorator.name == "staticmethod"}'
```

#### Find all `exception` types thrown
```
'**/Raise/[0]'
```

#### Find all `assert` statements
```
'**/Assert/[0]'
```
