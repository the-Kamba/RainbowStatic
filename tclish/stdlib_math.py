from .std_utils import *
def vm_number_question(vm, task, args):
    """
    ["number?"]=function(self, args)
    usage:
        number? <value>

    returns true if <value> is a valid number
    """
    if len(args)<1:
        return vm.ok("")
    if to_number(args[0]) is not None:
        return vm.ok("true")
    return vm.ok("")

def vm_integer_question(vm,task, args):
    if len(args)<1:
        return vm.ok("")
    n = to_number(args[0])
    if n is None:
        return vm.ok("")
    if isinstance(n,int):
        return vm.ok("true")
    if n.is_integer():
        return vm.ok("true")
    return vm.ok("")

def vm_gt(vm,task, args):
    """
    take two numbers and returns true if a is larger than b
    throws an error if either is not a valid number
    """
    if len(args)<1:
        return vm.ok("")
    sorted = True

    nPrev = to_number(args[0])
    if nPrev is None:
        return vm.error(task,"all arguments must be numbers, first is not", ">")

    for i in range(1, len(args)):
        n = to_number(args[i])
        if n is None:
            return vm.error(task,
                f"all arguments must be numbers, arg {i+1} is not", ">"
            )

        sorted = sorted and (nPrev > n)
        nPrev = n

        if not sorted:
            return vm.ok("")

    return vm.ok("true")

def vm_gte(vm,task, args):
    """
    take two numbers and returns true if a is larger or equal to b
    throws error if either is not a valid number
    """
    if len(args)<1:
        return vm.ok("")
    sorted = True

    nPrev = to_number(args[0])
    if nPrev is None:
        return vm.error(task,"all arguments must be numbers, first is not", ">=")

    for i in range(1, len(args)):
        n = to_number(args[i])
        if n is None:
            return vm.error(task,
                f"all arguments must be numbers, arg {i+1} is not", ">="
            )

        sorted = sorted and (nPrev >= n)
        nPrev = n

        if not sorted:
            return vm.ok("")

    return vm.ok("true")

def vm_eq(vm,task,args):
    """
    take two numbers and returns true if a is equal to b
    throws error if either is not a valid number
    """
    if len(args)<1:
        return vm.ok("")
    sorted = True

    nPrev = to_number(args[0])
    if nPrev is None:
        return vm.error(task,"all arguments must be numbers, first is not", "==")

    for i in range(1, len(args)):
        n = to_number(args[i])
        if n is None:
            return vm.error(task,
                f"all arguments must be numbers, arg {i+1} is not", "=="
            )

        sorted = sorted and (nPrev == n)
        nPrev = n

        if not sorted:
            return vm.ok("")

    return vm.ok("true")

def vm_le(vm,task, args):
    """
    take two numbers and returns true if a is less than or equal to b
    throws error if either is not a valid number
    """
    if len(args)<1:
        return vm.ok("")
    sorted = True

    nPrev = to_number(args[0])
    if nPrev is None:
        return vm.error(task,"all arguments must be numbers, first is not", "<")

    for i in range(1, len(args)):
        n = to_number(args[i])
        if n is None:
            return vm.error(task,
                f"all arguments must be numbers, arg {i+1} is not", "<"
            )

        sorted = sorted and (nPrev < n)
        nPrev = n

        if not sorted:
            return vm.ok("")

    return vm.ok("true")

def vm_lt(vm,task, args):
    """
    take two numbers and returns true if a is smaller than b
    throws error if either is not a valid number
    """
    if len(args)<1:
        return vm.ok("")
    sorted = True

    nPrev = to_number(args[0])
    if nPrev is None:
        return vm.error(task,"all arguments must be numbers, first is not", "<=")

    for i in range(1, len(args)):
        n = to_number(args[i])
        if n is None:
            return vm.error(task,
                f"all arguments must be numbers, arg {i+1} is not", "<="
            )

        sorted = sorted and (nPrev <= n)
        nPrev = n

        if not sorted:
            return vm.ok("")

    return vm.ok("true")

def vm_eq(vm,task, args):
    """
    take two or more strings and return true if they are all equal
    """
    if len(args) < 2:
        return vm.error(task,"= requires at least two arguments", "=")

    equals = all(arg == args[0] for arg in args[1:])
    return vm.ok("true" if equals else "")

def vm_neq(vm,task, args):
    """
    returns true if none of the provided strings are equal
    """
    if len(args) < 2:
        return vm.error(task,"!= requires at least two arguments", "!=")

    unique_values = set(args)
    return vm.ok("true" if len(unique_values) == len(args) else "")

def vm_not(vm,task, args):
    """
    returns true if input is false (empty string)
    """
    if len(args)<1:
        return vm.error(task,"! requires at least one argument", "!")
    if vm.is_true(args[0]):
        return vm.ok("true")
    else:
        return vm.ok("")


def vm_round(vm,task, args):
    """
    rounds the given input to the nearest integer
    non-number are considered 0
    """
    if len(args)<1:
        return vm.error(task,"round requires at least one argument", "round")

    n = to_number(args[0])
    if n is None:
        return vm.error(task,"Invalid input, must be a number", "round")
    if isinstance(n,float):
        return vm.ok(to_string(round(rounded_value)))
    return vm.ok(to_string(n))

def vm_and(vm,task, args):
    """
    returns true if all given arguments are true (non-empty strings)
    """
    for value in args:
        if not vm.is_true(value):
            return vm.ok("")
    return vm.ok("true")

def vm_or(vm,task, args):
    """
    returns true if at least one given argument is true (non-empty strings)
    """
    for value in args:
        if vm.is_true(value):
            return vm.ok("true")
    return vm.ok("")

def vm_add(vm,task, args):
    """
    returns a sum of all the inputs
    non-numbers are ignored
    """
    total_sum = 0
    for value in args:
        n = to_number(value)
        if n is not None:
            total_sum += n

    return vm.ok(to_string(total_sum))

def vm_multiply(vm,task, args):
    """
    returns a product of all the inputs
    non-numbers are ignored
    """
    total_product = 1
    for value in args:
        n = to_number(value)
        if n is not None:
            total_product *= n

    return vm.ok(to_string(total_product))

def vm_divide(vm,task, args):
    """
    returns the first number divided by the subsequent valid numbers
    throws an error if the first number is invalid
    subsequent non-numbers are ignored
    """
    if len(args)<1:
        return vm.error(task,"/ needs at least one number to divide", "/")
    first_number = to_number(args[0])
    if first_number is None:
        return vm.error(task,"/ needs at least one number to divide", "/")

    for value in args[1:]:
        n = to_number(value)
        if n is not None:
            first_number /= n

    return vm.ok(to_string(first_number))

def vm_subtract(vm, task, args):
    """
    (1) negates the numeric value of the input.
    (2) subtracts the subsequent numbers from the first number.

    non-numbers are treated as 0
    """
    if len(args)<1:
        return vm.error(task,"- must be given at least 1 number","-")
    n = to_number(args[0])
    if n is None:
        return vm.error(task,"cannot negate non-numbers","-")

    if len(args) == 1:
        return vm.ok(to_string(-n))

    first_number = n
    for value in args[1:]:
        n = to_number(value)
        if n is not None:
            first_number -= n

    return vm.ok(to_string(first_number))

def vm_modulo(vm,task, args):
    """
    usage:
      % a b

    performs the modulo operation on the two given numbers.
    throws an error if either is a non-number
    """
    if len(args) < 2:
        return vm.error(task,"must be provided with two numbers", "%")

    a, b = to_number(args[0]), to_number(args[1])
    if a is None:
        return vm.error(task,"a must be a number", "%")
    if b is None:
        return vm.error(task,"b must be a number", "%")

    return vm.ok(to_string(a % b))

def vm_floor(vm,task, args):
    """
    usage:
      floor <a>

    truncates the number.
    throws an error if <a> is a non-number
    """

    if len(args)<1:
        return vm.error(task,"floor requires at least one argument", "floor")

    n = to_number(args[0])
    if n is None:
        return vm.error(task,"Invalid input, must be a number", "floor")
    if isinstance(n,float):
        return vm.ok(to_string(math.floor(n)))
    return vm.ok(to_string(n))

def vm_ceil(vm,task, args):
    """
    usage:
      ceil <a>

    truncates the number.
    throws an error if <a> is a non-number
    """
    if len(args)<1:
        return vm.error(task,"ceil requires at least one argument", "ceil")

    n = to_number(args[0])
    if n is None:
        return vm.error(task,"Invalid input, must be a number", "ceil")
    if isinstance(n,float):
        return vm.ok(to_string(math.ceil(n)))
    return vm.ok(to_string(n))


def add_stdmath(registry):
    registry.add(
        "floor",
        vm_floor,
    """usage:
  floor <a>

truncates the number.
throws an error if <a> is a non-number""")
    registry.add(
        "ceil",
        vm_ceil,
    """usage:
  ceil <a>

truncates the number.
throws an error if <a> is a non-number""")
    registry.add(
        "number?",
        vm_number_question,
    """usage:
  number? <value>

returns true if <value> is a valid number""")
    registry.add(
        "integer?",
        vm_integer_question,
    """
    usage:
      integer? <value>
    
    returns true if <value> is a valid integer
    """)
    registry.add(
        ">",
        vm_gt,
    """usage:
  > a b

take two numbers and returns true if a is larger than b
throws an error if either is not a valid number""")
    registry.add(
        ">=",
        vm_gte,
    """usage:
  >= a b

take two numbers and returns true if a is larger or equal to b
throws error if either is not a valid number""")
    registry.add(
        "==",
        vm_eq,
    """usage:
  == a b

take two numbers and returns true if a is equal to b
throws error if either is not a valid number""")
    registry.add(
        "<=",
        vm_le,
    """usage:
  <= <nums...>

take two numbers and returns true if a is less than or equal to b
throws error if either is not a valid number""")
    registry.add(
        "<",
        vm_lt,
    """usage:
  < a b

take two numbers and returns true if a is smaller than b
throws error if either is not a valid number""")
    registry.add(
        "=",
        vm_eq,
    """usage:
  = a b

take two or more strings and return true if they are all equal""")
    registry.add(
        "!=",
        vm_neq,
    """usage:
  != <strs...>

returns true if none of the provided strings are equal""")
    registry.add(
        "!",
        vm_not,
    """usage:
  ! <value>

returns true if input is false (empty string)""")
    registry.add(
        "round",
        vm_round,
    """usage:
  round <value>

rounds the given input to the nearest integer
non-number are considered 0""")
    registry.add(
        "and",
        vm_and,
    """usage:
  and <values>...

returns true if all given arguments are true (non-empty strings)""")
    registry.add(
        "or",
        vm_or,
    """usage:
  or <values>...

returns true if at least one given argument is true (non-empty strings)""")
    registry.add(
        "+",
        vm_add,
    """usage:
  + <values>...

returns a sum of all the inputs
non-numbers are ignored""")
    registry.add(
        "*",
        vm_multiply,
    """usage:
  * <values>...

returns a product of all the inputs
non-numbers are ignored""")
    registry.add(
        "/",
        vm_divide,
    """usage:
  / <number> <values>...

returns the first number divided by the subsequent valid numbers
throws an error if the first number is invalid
subsequent non-numbers are ignored""")
    registry.add(
        "-",
        vm_subtract,
    """usage:
(1) - <number>
(2) - <number> <numbers>...

(1) negates the numeric value of the input.
(2) subtracts the subsequent numbers from the first number.

non numbers are treated as 0""")
    registry.add(
        "%",
        vm_modulo,
    """usage:
  % a b

performs the modulo operation on the two given numbers.
throws an error if either is a non-number""")

