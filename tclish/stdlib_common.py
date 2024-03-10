##=================================================================##
##  STANDARD LIBRARY                                               ##
##=================================================================##
import random
from .std_utils import *

def choose_async(switch,async_f,f):
    if switch:
        return async_f
    else:
        return f


def vmprint(vm,task,args):
    #print(args)
    s=" ".join(args)
    print(s)
    return vm.ok("")

def vmputs(vm,task,args):
    #print(args)
    s="".join(args)
    print(s,end="",flush=True)
    return vm.ok("")

def vmlist(vm,task,args):
    return vm.ok(pack_strings(vm,args))

def vmtake(vm,task,args):
    if len(args)<2:
        return vm.error(task,"take require a list and a number","take")
    ok,l=vm.unpack_strings(args[0])
    if not ok:
        return vm.error(task,"error unpacking list","take")
    n=to_number(args[1])
    if n is None:
        return vm.error(task,f"take require a valid number, {args[1]} is not a valid number.","take")
    res=[getl(l,i,"") for i in range(0,n)]
    return vm.ok(vm.pack_strings(res))


def vmlindex(vm,task,args):
    if len(args)<2:
        return vm.error(task,"lindex require a list and a number","lindex")
    ok,l=vm.unpack_strings(args[0])
    n=to_number(args[1])
    if not ok:
        return vm.error(task,"error unpacking list","lindex")
    if n is None:
        return vm.error(task,f"lindex require a valid number, {args[1]} is not a valid number.","lindex")
    return vm.ok(getl(l,n-1,""))

def vmlcount(vm,task,args):
    if len(args)<1:
        return vm.error(task,"lcount require a list","lcount")
    ok,l=vm.unpack_strings(args[0])
    if not ok:
        return vm.error(task,"error unpacking list","lindex")
    n=len(l)
    return vm.ok(to_string(n))
# {
#     proc lcount {l} {
#         eval "args count" {*} l
#     }
# }

def vmljoin(vm,task,args):
    if len(args)<1:
        return vm.error(task,"expected list")
    l=args[0]
    if len(args)>1:
        sep=args[1]
    else:
        sep=""
    ok,l=vm.unpack_strings(l)
    if not ok:
        return vm.error(task,l)
    return vm.ok(sep.join(l))

def vmlappend(vm,task,args):
    if len(args)<1:
        return vm.error(task,"expected list")
    l=args[0]
    ok,l=vm.unpack_strings(l)
    if not ok:
        return vm.error(task,l,"lappend")
    for item in args[1:]:
        l.append(item)
    return vm.ok(vm.pack_strings(l))

def vmlzip(vm,task,args):
    everything=[]
    maxlen=0
    for l in args:
        ok,unpacked=vm.unpack_strings(l)
        if not ok:
            return vm.error(task,f"argument {l} is not a valid list")
        everything.append(unpacked)
        if len(unpacked)>maxlen:
            maxlen=len(unpacked)
    output=[]
    for i in range(0,maxlen):
        for l in everything:
            output.append(getl(l,i,""))

    return vm.ok(vm.pack_strings(output))

def vmlzipmin(vm,task,args):
    everything=[]
    minlen=-1
    for l in args:
        ok,unpacked=vm.unpack_strings(l)
        if not ok:
            return vm.error(task,f"argument {l} is not a valid list")
        everything.append(unpacked)
        if minlen<0:
            minlen=len(unpacked)
        if len(unpacked)<minlen:
            minlen=len(unpacked)

    output=[]
    for i in range(0,minlen):
        for l in everything:
            output.append(getl(l,i,""))

    return vm.ok(vm.pack_strings(output))

async def vmgather(vm,task,args):
    ok,expected=vm.unpack_strings(args[0])
    
    pos=1
    def done():
        return pos>=len(args)
    def consume():
        nonlocal pos
        r=getl(args,pos,"")
        pos+=1
        return r

    data={}
    while not done():
        pass



async def vmtry(vm,task,args):
    if len(args)<1:
        return vm.ok("")
    pos=0
    def done():
        return pos>=len(args)
    def consume():
        nonlocal pos
        r=getl(args,pos,"")
        pos+=1
        return r

    program=consume()
    err_handle=None
    largs=[]


    while not done():
        match consume().lower():
            case "catch" | "except":
                err_handle=consume()
            case "args":
                largs=unpack_strings(consume())

    ok,res=await vm.eval(task,program,args=largs)
    if not vm.is_abort(ok):
        return ok,res
    if err_handle is not None:
        ok,res=await vm.eval(task,err_handle,args=[res,program]+largs)
    else:
        return vm.ok(res)

    return ok,res

async def vmeval(vm,task,args):
    if len(args)<1:
        return vm.ok("")
    if len(args)>1:
        return await vm.eval(task,args[0],args=args[1:])
    else:
        return await vm.eval(task,args[0])


async def vmforeach_new(vm,task,args):
    """
    foreach {a b} in [list 1 2 3 4] {
        print $a $b
    }
    """
    pos=0
    def consume():
        nonlocal pos
        r=getl(args,pos,"")
        pos+=1
        return r
    def peek():
        return getl(args,pos,"")
    def done():
        return pos>=len(args)

    #for
    packed_names=consume()
    #print(f"packed_names : {packed_names}")
    keyword=consume()
    #print(f"keyword : {keyword}")
    input_list=consume()
    #print(f"input_list : {input_list}")
    
    body=consume()

    if keyword.lower() != "in":
        #keyword not present
        input_list,body=keyword,input_list
    

    ok,names=vm.unpack_strings(packed_names)
    if not ok:
        return vm.error(task,f"{packed_names} is an invalid list of names","range")
    if len(names)<1:
        return vm.error(task,f"'{packed_names}' does not contain at least one name","range")

    ok,variable_list=vm.unpack_strings(input_list)
    if not ok:
        return vm.error(task,f"{input_list} is an invalid list of strings","range")


    pos_I=0
    def consume_I():
        nonlocal pos_I
        r=getl(variable_list,pos_I,"")
        pos_I+=1
        return r
    def done_I():
        return pos_I>=len(variable_list)
    result=""
    while not done_I():
        for name in names:
            task.set_value(name,consume_I())
        ok,res=await vm.simple_eval(task,body)
        if vm.is_abort(ok):
            return ok,res
        if vm.is_error(res):
            return ok,res
        result=res
    return vm.ok(result)




async def vmforeach(vm,task,args):
    if len(args)<3:
        return vm.error(task,"expected name, list and code")
    name=args[0]
    l=args[1]
    code=args[2]
    #print(f"{name}|{l}|{code}")
    ok,l=unpack_strings(vm,l)
    if not ok:
        return vm.error(task,l)
    # if len(l)<1:
    #     return vm.error(task,"one or more name must be provided","foreach")
    result=""
    for i,elem in enumerate(l):
        task.set_value(name,elem)
        task.set_value("i",str(i))
        task.set_value("ans",result)
        ok,res=await vm.simple_eval(task,code)
        if vm.is_abort(ok):
            return ok,res
        result=res
    return vm.ok(result)

async def vmlmap(vm,task,args):
    if len(args)<2:
        return vm.error(task,"expected list and code")
    l=args[0]
    code=args[1]
    ok,l=unpack_strings(vm,l)
    if not ok:
        return vm.error(task,l)
    result=[]
    res=""
    for i,elem in enumerate(l):
        ok,res=await vm.do_codebody(task,code,args=[elem,str(i),res])
        if vm.is_abort(ok):
            return ok,res
        result.append(res)
    
    return vm.ok(pack_strings(vm,result))

async def vmlreduce(vm,task,args):
    if len(args)<2:
        return vm.error(task,"expected list and code")
    l=args[0]
    code=args[1]
    ok,l=unpack_strings(vm,l)
    if not ok:
        return vm.error(task,l)
    result=getl(args,2,"")
    for i,elem in enumerate(l):
        ok,res=await vm.do_codebody(task,code,args=[elem,str(i),result])
        if vm.is_abort(ok):
            return ok,res
        result=res
    return vm.ok(result)

async def vmlfilter(vm,task, args):
    if len(args) < 2:
        return vm.error(task,"expected list and code")
    l = args[0]
    code = args[1]
    ok, l = unpack_strings(vm, l)
    if not ok:
        return vm.error(task,l)
    result = []
    res=""
    for i, elem in enumerate(l):
        ok, res = await vm.do_codebody(task,code, args=[elem, str(i),res])
        if not ok:
            return ok, res
        if istrue(res):
            result.append(elem)
    return vm.ok(pack_strings(vm, result))

def vmproc(vm,task,args):
    #lambda vm,a:vm.state.add_definition(getl(a,0,""),getl(a,1,""),getl(a,2,""))
    if len(args)<3:
        return vm.error(task,"a procedure needs a name, an argument list and a body, and optinally a helpstring","proc")
    
    ok,proc_args=unpack_strings(vm,args[1])
    
    if not ok:
        return vm.error(task,f"error with args \n{proc_args}")
    proc_args="".join(["'"+escape_string(arg)+"'" for arg in proc_args])
    if len(proc_args)>0:
        ok,res=vm.add_definition(args[0],f"args map {proc_args}\n{args[2]}",getl(args,3,""))
    else:
        ok,res=vm.add_definition(args[0],f"args map \n{args[2]}",getl(args,3,""))
    if ok:
        return vm.ok("")
    else:
        return vm.error(task,"error adding definition")

def vmchoose(vm,task,args):
    #lambda vm,a:vm.state.add_definition(getl(a,0,""),getl(a,1,""),getl(a,2,""))
    
    if len(args)<1:
        return vm.ok("")
    
    return vm.ok(random.choice(args))

def vmrange(vm,task,args):
    if len(args)>=3:
        start=to_number(args[0])
        if start is None: return vm.error(task,"start must be a number","range")
        step=to_number(args[1])
        if step is None: return vm.error(task,"step must be a number","range")
        stop=to_number(args[2])
        if stop is None: return vm.error(task,"stop must be a number","range")
        if step<0: #because python range is not inclusive on stop
            stop-=1
        else:
            stop+=1
    elif len(args)>=2:
        start=to_number(args[0])
        if start is None: return vm.error(task,"start must be a number","range")
        stop=to_number(args[1])
        if stop is None: return vm.error(task,"stop must be a number","range")
        if start>stop:
            step=-1
            stop-=1
        else:
            stop+=1
            step=1
    elif len(args)>=1:
        stop=to_number(args[0])
        if stop is None: return vm.error(task,"stop must be a number","range")
        if stop<0:
            start=-1
            step=-1
            stop-=1
        else:
            start=1
            step=1
            stop+=1
    else:
        return vm.error(task,"please specify a range","range")

    return vm.ok(vm.pack_strings([str(n) for n in range(start,stop,step)]))

def add_stdcommon(registry):
    registry.add("choose",vmchoose,"""usage:
  choose <options>...

Returns one of the provided options at random.
""")
    registry.add("range",vmrange,"""usage:
(1) range <n>
(2) range <start> <stop>
(3) range <start> <step> <stop>


Returns a list of number in the specified range.

(1) returns a list from 1 to <n> if n is positive, if n i negative, it returns a list from -1 to n
(2) returns a list from start to stop
(3) returns a list of every <step> number from <start> to <stop>

""")
    registry.add("proc",vmproc,"""usage:
  proc <name> <arguments> <body> [<helpstring>]


Example:
  proc add {a b} {
    + $a $b
  } "adds a and b"

equivalent to:
  defproc add {
    args map a b
    + $a $b
  }
""")
    registry.add("print",vmprint,"""
Usage:
  print <value>...

Prints the specified values to the console.

Example:
  print "Hello, world!"
""")
    registry.add("puts",vmputs,"""
Usage:
  puts <value>...

Prints the specified values to the console without padding and newlines.

Example:
  puts "Hello, world!"
""")
    registry.add("try",vmtry,"""
Usage:
  try <code> [<catch>]

catches error generated by <code>
if <code> generates an error, <catch> is executed.
if <catch> generates an error, it throws that error

Example:
  try {
    #code
    error "errormsg"
  } {
    #catch
    log "
      code [args 1] 
      generated the error message [args 0]"
  }
""")
    registry.add("eval",vmeval,"""
Usage:
  eval <code> [<args>...]
evaluates <code>
if any <args> is provided, executes code in new scope

Example:
  eval {
    error "errormsg"
  }
""")
    registry.add("list",vmlist,"""Usage:
  list <element>...

Creates a list containing the specified elements.

Example:
  set myList [list 1 2 3 4]
""")
    registry.add("take",vmtake,"""Usage:
  take <list> <count>

Returns the first <count> items from <list>. If <list> is shorter than <count>, the return is padded to the specified length with empty strings.

Example:
  take [list 1 2 3] 2
returns:
  [list 1 2]
""")
    registry.add("lindex",vmlindex,"""Usage:
  take <list> <index>

Returns the item located at <index> in <list>. 

Example:
  lindex [list 1 2 3] 2
returns:
  2
""")
    registry.add("lcount",vmlcount,"""Usage:
  lcount <list>

Returns the number of entries in <list>

Example:
  lcount [list a b c]
returns:
  3
""")
    registry.add("ljoin",vmljoin,"""Usage:
  ljoin <list> [<sep>]

Concatenates all the values in <list>, optinally separated by <sep>

Example:
  set result [ljoin $list1 $list2]
""")
    registry.add("lappend",vmlappend,"""Usage:
  lappend <list> <items>...

Append <items> onto <list>

Example:
  lappend [list a b c] d e f
""")
    registry.add("lzip",vmlzip,"""Usage:
  lzip <lists>...

Zips all the list together such that the output is the interleaved elements from all the specified lists.
The length of the output list is the number of lists times the number of entries in the longest list. Missing elements are padded with empty strings.


Example:
  lzip [list 1 2 3] [list a b c d]
Returns:
  [list 1 a 2 b 3 c "" d]
""")
    registry.add("lzipmax",vmlzip,"""Usage:
  lzipmax <lists>...

Zips all the list together such that the output is the interleaved elements from all the specified lists.
The length of the output list is the number of lists times the number of entries in the longest list. Missing elements are padded with empty strings.

This is the default behaviour of lzip

Example:
  lzipmax [list 1 2 3] [list a b c d]
Returns:
  [list 1 a 2 b 3 c "" d]
""")
    registry.add("lzipmin",vmlzipmin,"""Usage:
  lzipmin <lists>...

Zips all the list together such that the output is the interleaved elements from all the specified lists.
The length of the output list is the number of lists times the number of entries in the shortest list. Excess elements are discarded.


Example:
  lzipmin [list 1 2 3] [list a b c d]
Returns:
  [list 1 a 2 b 3 c]
""")
    registry.add("lmap",vmlmap,"""Usage:
  lmap <list> <script>

Applies a script to each element of the list and returns the result as a list.

Example:
  set squaredList [lmap $numbers {expr {
    args map item intex prev-item
    * $item $item
  }}]
""")
    registry.add("lreduce",vmlreduce,"""Usage:
  lreduce <list> <script> [<initial_value>]

Reduces a list using a script and an optional initial value. The script is applied cumulatively to the items of the list, and the result is the accumulated value.

Example:
  set sum [lreduce $numbers {expr {
    args map item position accumulator
    + $accumulator $item
  }} 0]
""")
    registry.add("lfilter",vmlfilter,"""Usage:
  lfilter <list> <script>

Filters elements of the list based on a script and returns the filtered list.

Example:
  set evenNumbers [lfilter $numbers {expr {
    args item pos prev-item
    % $item 2 == 0
  }}]
""")

    registry.add("for",vmforeach,"""Usage:
  for <variable> <list> <script>

Iterates over elements in a list, assigning each element to the variable and executing the script.
Execution happens in the current scope and can be shorted with the return command

Example:
  set numbers {1 2 3 4}
  foreach i $numbers {
    print "Current value of \$i: $i"
  }
""")
    registry.add("foreach",vmforeach_new,"""Usage:
  foreach <var-names> [in] <list> <script>

Iterates over elements in a list, assigning each element to the variable and executing the script.
Execution happens in the current scope and can be shorted with the return command

Example:
  set numbers { a 1 b 2 c 3 d 4}
  foreach {letter number} $numbers {
    print "Current value of $letter: $number"
  }
""")
