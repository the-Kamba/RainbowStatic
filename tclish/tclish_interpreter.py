from .std_utils import *
#from stdlib import add_common,add_stdmath,add_regex
from .db import Tclish_DB
from .db_disk import Tclish_DB_disk

from .stdlib_math  import add_stdmath
from .stdlib_common import add_stdcommon
from .stdlib_string import add_stdstring
from .registries import tclish_command_registry,tclish_object_registry
from enum import Enum
import heapq
import time

class Tclish_task():
	"""docstring for tclish_task"""
	def __init__(self, code,args=None):
		self.states=[]
		self.stack_limit=64
		self.prog=code
		self.initial_args=args if args is not None else []
		self.state="ready"
		# ready | running | done
		self.push(self.initial_args)

	def args(self):
		if len(self.states)<1:
			return []
		return self.states[len(self.states)-1]["args"]

	def push(self,args=None,label=""):
		if len(self.states)>self.stack_limit:
			return False
		self.states.append({
			"args": args if args is not None else [],
			"values":{},
			"label":label,
		})
		return True

	def pop(self):
		if len(self.states)>0:
			self.states.pop()
			return True
		return False

	def get_value(self,key):
		for stackframe in reversed(self.states):
			if key in stackframe["values"]:
				return stackframe["values"][key]
		return None

	def set_value(self,key,value):
		if len(self.states)>0:
			self.states[len(self.states)-1]["values"][key]=value
			return True
		return False

	def update_value(self,key,value):
		for stackframe in reversed(self.states):
			if key in stackframe["values"]:
				stackframe["values"][key] = value
				return True
		return False

	def unset_value(self,key):
		if len(self.states)>0:
			if key in self.states[-1]["values"]:
				del self.states[-1]["values"][key]
			return









Tclish_response_flag = Enum("Tclish_response_flag",[
	"normal",
	"comment",
	"forced_return",
	"error"
])


async def vmif(vm,task,args):
	"""
	Executes an 'if' statement in the tclish interpreter.

	Parameters:
	- args (List[str]): A list of strings representing the components of the 'if' statement. It should follow the pattern:
		["if", condition_1, body_1, "elseif" | "elif", condition_2, body_2, ..., "else", else_body]

	Returns:
	Tuple[bool, str]: A tuple indicating the success of the operation and the result or error message.
		- If success is True, the result contains the outcome of the executed 'if' statement.
		- If success is False, the result contains an error message.

	The 'if' statement is evaluated sequentially, and the first condition that is true triggers the execution of the corresponding body. If no conditions are true, the 'else' branch (if provided) is executed.

	Example:
	```python
	vmif(self, ["if", "cond_1", "body_1", "elif", "cond_2", "body_2", "else", "else_body"])
	```

	Note:
	- The 'elif' and 'elseif' keywords are interchangeable.
	- Conditions and bodies are evaluated sequentially, and only the first true condition's body is executed.
	- Conditions and bodies are provided as strings and are evaluated using the tclish interpreter.

	Raises:
	- If the 'if' statement is not properly formatted (e.g., missing conditions or bodies), an error is returned.
	- If there is an error during the evaluation of a condition or body, the error message is returned.

	See Also:
	- The 'if' statement in tclish follows the structure:
		if {condition_1} {
			body_1
		} elif {condition_2} {
			body_2
		} else {
			else_body
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

	cond=consume()
	body=consume()
	ok,res=await vm.simple_eval(task,cond)
	if is_abort(ok):
		return ok,res
	if isTrue(res):
		return await vm.simple_eval(task,body)

	while not done():
		match consume().lower():
			case "else":
				return await vm.simple_eval(task,consume())
			case "elseif" | "elif":
				cond=consume()
				body=consume()
				ok,res=await vm.simple_eval(task,cond)
				if is_abort(ok):
					return ok,res
				if isTrue(res):
					return await vm.simple_eval(task,body)
	return vm.ok("")

def vmhelp(vm,task,args):
	if len(args)<1:
		return vm.ok(directive_helps["help"])
	if len(args)>=2 and (
			(args[0].lower()=="list" and args[1].lower()=="topics")
			or (args[0].lower()=="topics" and args[1].lower()=="list")):
		return vm.ok(pack_strings(vm,
					list( vm.helps.keys()      )
					+list(vm.directives.keys() )
					+list(vm.commands.keys()   )
					+list(vm.handles.keys()    )
					+list(vm.definitions.keys())))

	elif args[0].lower()=="topics":
		return vm.ok("" +
			"general topics:\n  "  +"\n  ".join(list(vm.helps.keys())      ) +
			"\ndirectives:\n  "    +"\n  ".join(     vm.directives.keys()  ) +
			"\ncommands:\n  "      +"\n  ".join(     vm.commands.keys()    ) +
			"\nhandles:\n  "       +"\n  ".join(     vm.handles.keys()     ) +
			"\ndefinitions:\n  "   +"\n  ".join(list(vm.definitions.keys())))

	elif args[0] in vm.handles:#(handle:=self.handles.get(args[0],None)) is not None:
		handle = vm.handles[args[0]]
		if isinstance(handle["help"],str):
			return vm.ok(handle["help"])
		elif callable(handle["help"]):
			return (handle["help"](vm,task,args[1:]))
		else:
			return vm.error(task,f"error in help for handle\n"+str(vm.handles[args[0]]["help"]),"help")

	elif (helps:=vm.directive_helps.get(args[0])) is not None:
		return vm.ok(helps)
	elif (helps:=vm.definitions.get(args[0])) is not None:
		return vm.ok(helps["help"])
	elif vm.objects.is_object(args[0]):
		instance=vm.objects.get_instance(args[0])
		return vm.ok(vm.objects.get_help(instance))
	elif (helps:=vm.commands.help(args[0])) is not None:
		return vm.ok(helps)
	elif (helps:=vm.definitions.get(args[0])) is not None:
		return vm.ok(helps["help"])
	return vm.ok(f"helpstring for topic '{args[0]}' doesn't exist")

def vmreturn(vm,task,args):
	if len(args)<1:
		return vm.forced_return("")
	return vm.forced_return(args[0])

def vmerror(vm,task,args):
	if len(args)<1:
		return vm.error(task,"error","error")
	if len(args)<2:
		return vm.error(task,args[0],"error")
	if len(args)==2:
		return vm.error(task,args[0],args[1])
	return vm.error(task," ".join(args[:-1]),args[-1])
def vmget(vm,task,args):
	if len(args)<1:
		return vm.error(task,"get requires a variable name")
	val=vm.get_value(args[0],task=task)
	#print(val)
	if val is None:
		return vm.ok("")
	return vm.ok(str(val))
def vmset(vm,task,args):
	if len(args)<1:
		return vm.error(task,"set requires a variable name")
	if len(args)==1:
		task.unset_value(args[0])
		return vm.ok("")
	task.set_value(args[0],args[1])
	return vm.ok(args[1])
def vmargs(vm,task,args):
	sargs=task.args()
	if len(args)<1:
		return vm.error(task,"Args requires a directive or an index")

	if args[0].lower()=="count":
		return vm.ok(str(len(sargs)))

	elif args[0].lower()=="list":
		start=getl(args,1,"1")
		stop=getl(args,2,str(len(sargs)+1))
		startn = to_number(start)
		if startn is None:
			return vm.error(task,f"{start} is not a valid index")

		stopn=to_number(stop)
		if stopn is None:
			return vm.error(task,f"{stop} is not a valid index")
		return vm.ok(pack_strings(vm,sargs[(startn-1):(stopn-1)]))

	elif args[0].lower()=="map":
		succ=True
		missing=[]
		for i,name in enumerate(args[1:]):
			if i>=len(sargs):
				return vm.error(task,f"argument <{name}> at pos {i+1} is missing","args map")
			task.set_value(name,getl(sargs,i,""))
		return vm.ok("")
		
	else:
		index=to_number(args[0])
		if index is None:
			return vm.error(task,f"{args[0]} is not a valid index")
		return vm.ok(getl(sargs,index-1,""))

def vmdefproc(vm,task,args):
	if len(args)<2:
		return vm.error(task,"a procedure needs both a name and a body, and optinally a helpstring","defproc")
	ok,res=vm.add_definition(args[0],args[1],getl(args,2,""))
	if ok:
		return vm.ok(res)
	else:
		return vm.error(task,res)

def vmtrue(vm,task,args):
	return vm.ok("true")
def vmfalse(vm,task,args):
	return vm.ok("")

directive_helps={

"true":"""usage:
  true
return a value that is considered true in a boolean context.
""",

"false":"""usage:
  false
return a value that is considered false in a boolean context.
""",

"if":"""usage:
  if <conditon> <body> [elif <condition> <body>]... [else <body>]

if followed by a condition and a body. if the condition evaluates to true, then the body is evaluated.
otherwise it will look for elif or else directive.
when it encounters the elif keyword, it takes the next arguments as a condition and the one after as a body. if the condition evaluates to true, the body is evaluated.
when it encounters the else keyword, it evaluates the following argument as a body and termiates the if statement, regardless if more is following.

Example:
  if {> $x 0} {
	print "x is positive"
  } elif {< $x 0} {
	print "x is negative"
  } else {
	print "x is zero"
  }

""",

"defproc":"""usage:
  defproc <name> <body> [<helpstring>]

Example:
  defroc add {
	+ [args 1] [args 2]
  } "usage:
	add <a> <b>

  returns the sum of <a> and <b>
  "
""",

"args":"""usage:
(1) args <index>
(2) args count
(3) args map <varname>...
(4) args list [start] [stop]

args is used to get the arguments given to the command
  within the body of the definition
  arguments are numbered 1 to n

(1) args <index>
	returns the argument of the given index
	index must be number and invalid indexes returns empty string.

	example 1:
	  defproc ex1 {
		print [args 1]
	  }
	  ex1 a
	outputs:
	  a

(2) args count
	returns the number of arguments passed to the command
	
	example 2:
	  defproc ex2 {
		print "got [args count] arguments"
	  }
	  ex2 1 2 3 4
	outputs:
	  got 4 arguments

(3) args map <varnames>...
	the arguments to the given names
	throws an error if fewer arguments are present than varnames provided
	
	example 3:
	  defproc ex3 {
		args map a b c
		print $c $b $a
	  }
	  ex3 k l m
	outputs:
	  m l k

(4) args list [start] [stop]
	returns all arguments encoded as a list, starting at [start] and stopping at [stop]
	start defaults to 1, and stop defaults to [args count]
	
	example 4:
	  defproc ex4 {
		foreach arg [args list 2]{
			print $arg
		}
	  }
	  ex4 a b c
	outputs:
	  b
	  c
""",

"error":"""
Usage:
  error <message>

Raises an error with the specified error message.

Example:
  error "This is an error message"
""",

"return":"""usage:
  return [<value>]

returns a value, ending the execution in scope early.""",

"set":"""usage:
  set <name> <value>

set the value associated with <name> in the current scope""",

"get":"""usage:
  get <name>

return the value associated with <name> in the current scope.
if it's not definid in the current scope, it'll traverses up the stack until a definition is found.
failing that, it'll get the global value or an empty string.
""",

"help":"""usage:
help <topic>

returns the helpstring for the specified topic
""",
}


def is_abort(flag):
	return (flag is Tclish_response_flag.error or
		flag is Tclish_response_flag.forced_return)



class Tclish_interpreter:
	directives={
		"if": vmif,
		"return": vmreturn,
		"error": vmerror,
		"get": vmget,
		"set": vmset,
		"args": vmargs,
		"defproc": vmdefproc,
		"true": vmtrue,
		"false": vmfalse,
	}
	directive_helps=directive_helps
	def __init__(self,/,*,db_filename=None):
		self.event_queue=[]#priority queue
		self.commands=tclish_command_registry()
		self.handles={}
		self.helps={}
		self.definitions={}
		if db_filename:
			self.db=Tclish_DB_disk(db_filename)
			self.db.load()
		else:
			self.db=Tclish_DB()
		self.objects=tclish_object_registry()
		self.commands.add(*self.db.vm_command())
		self.commands.add("help",lambda vm,task,a:vmhelp(vm,task,a),directive_helps["help"])
		self.objects.add_commands(self)

		def local_schedule_event(vm,task,args):
			if len(args)<2:
				return vm.error(task,"timeout and event needed")
			time=to_number(args[0])
			if time is None:
				return vm.error(task,"time must be a valid number of seconds")
			vm.push_event(task,time,args[1],args=args[2:])
			return vm.ok()
		def local_push_event(vm,task,args):
			if len(args)<1:
				return vm.error(task,"event needed")
			vm.push_event(task,0,args[0],args=args[1:])
			return vm.ok()

		self.add_command("schedule-event",local_schedule_event,"""Usage:
  schedule-event <timeout> <command> <args>...

Schedule an event to happen <timeout> seconds in the future.
""")

		self.add_command("push-event",local_push_event,"""Usage:
  push-event <command> <args>...

equivalent to schedule-event 0 <command> {*} <args>
""")
		def list_events(vm,task,args):
			events=[]
			for (event_time, task, command, args, handles) in self.event_queue:
				events.append(command)
				events.append(str(event_time))
			return vm.ok(vm.pack_strings(events))
		self.add_command("list-events",list_events,"list-events ")
		def vmtime_time(vm,task,args):
			return vm.ok(str(time.time()))
		self.add_command("time",vmtime_time,"""usage: time ; returns current time in seconds since 1970""")

	def push_event(self,task,timeout,command,args=None,handles=None):
		"""add the event to the event queue at the current time plus timeout"""
		event_time = time.time() + timeout
		event = (event_time, task, command, args, handles)
		heapq.heappush(self.event_queue, event)

	async def process_events(self,count=1):
		"""process up to count events from the event queue"""
		current_time = time.time()

		# Process events until count is reached or the queue is empty
		while self.event_queue and count > 0:
			# Get the next event
			event_time, task, command, args, handles = heapq.heappop(self.event_queue)

			# Check if the event time has passed
			if event_time > current_time:
				# Push the event back to the queue (it's not time to process it yet)
				heapq.heappush(self.event_queue, (event_time, task, command, args, handles))
				break
			prev_handles={}
			if handles is not None:
				for name,func,helps in handles:
					prev_handles[name]=self.add_handle(name,func,helps)
			# Execute the event
			ok,result = await self.do_codebody(task, command, args)
			
			for name,prev in prev_handles.items():
				self.remove_handle(name,prev)

			if self.is_error(ok) and command != "on-event-error":
				self.push_event(task,0,"on-event-error",args=[command,result]+args,handles=handles)

			count -= 1

	def tojson(self):
		return {
			"helps":self.helps,
			"definitions":self.definitions,
			"db":self.db.tojson(),
			"objects":self.objects.tojson(),
		}
	def fromjson(self,data):
		if "helps" in data:
			for k,v in data["helps"].items():
				self.helps[k]=v
		if "definitions" in data:
			for k,v in data["definitions"].items():
				self.definitions[k]=v
		if "db" in data:
			if isinstance(self.db,Tclish_DB):
				self.db.fromjson(data["db"])
			else:
				self.db.fromjson({"db":data["db"]})
		if "objects" in data:
			self.objects.fromjson(data["objects"])

	def get_method_names(self):
		l=set(self.commands.keys())
		for item in self.objects.named_objects.keys():
			l.add(item)
		for item in self.objects.objects.keys():
			l.add(item)
		for item in self.definitions.keys():
			l.add(item)
		for item in self.handles.keys():
			l.add(item)
		for item in self.directives.keys():
			l.add(item)
		# for item in self.state.global_state.keys():
		# 	l.add("$"+item)
		return l



	def add_definition(self,name,func,helps):
		# if name in self.definitions:
		# 	return self.format_error(f"'{name}' is already defined",label="add_definition")

		self.definitions[name]={
			"function" : func,
			"help" : helps,
		}
		return True,""

	def add_handle(self,name,handle,helps):
		prev=self.handles.get(name,None)
		self.handles[name]={
			"handle":handle,
			"help":helps,
		}
		return prev

	def remove_handle(self,name,prev=None):
		if name in self.handles:
			del self.handles[name]
		if prev is not None:
			self.handles[name]=prev


	def add_command(self,name,func,helps):
		return self.commands.add(name,func,helps)
	def pack_strings(self,strings):
		return pack_strings(self,strings)
	def unpack_strings(self,strings):
		return unpack_strings(self,strings)
	def add_stdlibs(self):
		add_stdmath(self.commands)
		add_stdcommon(self.commands)
		add_stdstring(self.commands)
	def is_true(self,thing):
		if thing=="":
			return False
		return True
	def is_abort(self,flag):
		return is_abort(flag)
	def is_error(self,flag):
		return flag is Tclish_response_flag.error
	def is_return(self,flag):
		return flag is Tclish_response_flag.forced_return
	def is_comment(self,flag):
		return flag is Tclish_response_flag.comment
	def is_ok(self,flag):
		return flag is Tclish_response_flag.normal

	def get_value(self,key,task=None):
		#for later, when I reintroduce global state.
		# possibly with the db
		val = None
		if task is not None:
			val = task.get_value(key)
		if val is None:
			val=self.db.get([key])
		return val

	def ok(self,text=""):
		return (Tclish_response_flag.normal,text)

	def error(self,task=None,message="undefined error",label="unspecified"):
		msg=[f"<{label}> {message}"]
		if task is not None:
			if len(task.states)>0:
				msg.append("while evaluating:{"+str(task.states[-1]["label"])+"}")
				msg.append("stack:")
				for i,v in enumerate(reversed(task.states)):
					msg.append(str(i).rjust(4)+": {"+str(v["label"])+"}")

		return (Tclish_response_flag.error,"\n".join(msg))

	def forced_return(self,value=""):
		return (Tclish_response_flag.forced_return,value)

	def comment(self,value=""):
		return (Tclish_response_flag.comment,value)

	def extract_header(self,s):
		return extract_header(self,None,s)


	def read_sentence(self,task, s, pos):
		#this function is fucked
		newline = False
		strings = []
		strcount = 0
		endpos = pos

		pos, newline = skip_whitespace(s, pos)
		#print(pos,newline)
		while (not newline) and (pos < len(s)):
			success, endpos = skip_string(self, s, pos)

			if not success:
				ok, s=self.error(task,endpos)
				return ok, s, None

			current_str = s[pos:endpos]
			
			#if current_str is ";" break the line
			if current_str == ";":
				pos=endpos
				break
			
			strings.append(current_str)

			if endpos == pos:
				ok,s=self.error(task,"trailing bracket '{}' near <{}>".format(s[pos], s[max(pos - 3, 0):min(pos + 3, len(s))]), "read_sentence")
				return ok,s,None

			pos = endpos
			pos, newline = skip_whitespace(s, pos)

			if current_str == "\\":
				newline = False
				strings.pop()

		return Tclish_response_flag.normal, pos, strings

	def split_sentences(self,task,prog,pos=0):
		sentences=[]
		sentence=[]
		while pos<len(prog):
			success,pos,sentence=self.read_sentence(task,prog,pos)
			if success is Tclish_response_flag.error:
				return success,pos
			if len(sentence)>0:
				if len(sentence[0])>=0 and sentence[0][0]=="#":
					#skip comments
					pass
				else:
					sentences.append(sentence)

		return self.ok(sentences)

	async def do_string(self,prog):
		return await self.do_task(Tclish_task(prog))

	async def do_task(self,task):
		ok,res=await self.eval(task,task.prog)
		return ok ,res

	async def do_codebody(self,task,code_body,args=None,label=None):
		if is_command_name(code_body):
			code_body=code_body+" {*} [args list]"
		return await self.eval(task,code_body,args,label)

	async def eval(self,task,prog,args=None,label=None):
		# if (args is not None) or (label is not None):
		# 	if not task.push(
		# 		args=args if args is not None else [],
		# 		label=label if label is not None else prog):
		if not task.push(
			args=args if args is not None else [],
			label=label if label is not None else prog):
			return self.error(task,"stack limit exceeded","eval")
		ok,result=await self.simple_eval(task,prog)
		# if (args is not None) or (label is not None):
		# 	task.pop()
		task.pop()
		if ok is Tclish_response_flag.forced_return:
			ok=Tclish_response_flag.normal
		return ok,result

	async def simple_eval(self,task,prog):
		ok,sentences=self.split_sentences(task,prog)
		if ok is Tclish_response_flag.error:
			return ok,sentences

		result=""
		for sentence in sentences:
			tsuccess,tresult=await self.eval_sentence(task,sentence)
			match tsuccess:
				case Tclish_response_flag.normal:
					#normal behaviour
					result=tresult
				case Tclish_response_flag.error:
					#propagate error
					return tsuccess,tresult
				case Tclish_response_flag.comment:
					#do nothing
					pass
				case Tclish_response_flag.forced_return:
					#return early
					return tsuccess,tresult
				case X:
					return self.error(task,f"unknown directive {X}","simple_eval")
		return self.ok(result)
	def is_modifier(self,command):
		if len(command)<2:
			return False
		return command[-1]=="=" and command[-2]!="="
	async def eval_sentence(self,task,sentence):
		if len(sentence)<=0:
			return self.comment("")
		if len(sentence[0])<=0 or sentence[0][0]=="#":
			return self.comment("")

		success=True
		command=None

		success,command=await clean_strings(self,task,sentence[0])

		# end with a single "="
		modifier=len(command)>=2 and command[-1]=="=" and command[-2]!="="

		args=[]
		result=""
		outpos=0
		inpos=1
		unpack_next=False
		unpack_command="{*}"

		while inpos<len(sentence) and not is_abort(success):
			if sentence[inpos]==unpack_command:
				if command=="help" and inpos==1:
					sentence[inpos]="{"+sentence[inpos]+"}"
				else:
					unpack_next=True
					inpos+=1
					if inpos>=len(sentence):
						inpos=len(sentence)-1
					# do helpcheck here

			tempresult=None
			success,tempresult=await clean_strings(self,task,sentence[inpos])
			if is_abort(success):
				return success,tempresult

			if unpack_next:
				valid,subsentence=unpack_strings(self,tempresult)
				if is_abort(valid):
					subsentence=[tempresult]

				for word in subsentence:
					args.append(word)
					outpos+=1
				inpos+=1
				unpack_next=False
			else:
				args.append(tempresult)
				inpos+=1
				outpos+=1


		if is_abort(success) or (success is Tclish_response_flag.comment):
			return success,result

		field=None
		if modifier:
			if len(args)<1:
				return self.error(task,"Modifiers requires a field name",command)
			field=args[0]
			val=task.get_value(field)
			if val is None:
				args[0]=""
			else:
				args[0]=val
			command=command[:-1]

		if (func := self.directives.get(command)) is not None:
			success,result = await call_async(func,self,task,args)

		elif (func := self.commands.get(command)) is not None:

			success,result = await call_async(func,self,task,args)
			if isinstance(success,bool):
				raise ValueError(f"Error in {command}.\nsuccess flag from command has been changed to Tclish_response_flag enum. use vm.ok(value), vm.error(task,value), vm.comment(value) or vm.forced_return(value)")
				if success:
					success=Tclish_response_flag.normal
				else:
					success=Tclish_response_flag.error
			elif not isinstance(success,Tclish_response_flag):
				return self.error(task,f"{command} returned {str(success)} <{type(success)}> with the result: {str(result)}",command)

		elif self.objects.is_object(command):
			instance=self.objects.get_instance(command)
			success,result = await self.objects.instance_command(instance,self,task,args)


		elif command in self.handles:
			success,result = await call_async(self.handles[command]["handle"],self,task,args)

		elif (func := self.definitions.get(command,None)) is not None:
			success,result = await self.eval(task,func["function"],args=args)
		else:
			success,result = self.error(task,"unknown command",command)

		if result is None:
			success,result = self.error(task,"something went horribly wrong","evalSentence")
		if is_abort(success):
			return success,result

		if modifier:
			if not task.update_value(field,result):
				task.set_value(field,result)

		return success,result

	def with_handle(self,name,handle,helps):
		return Tclish_handle(self,name,handle,helps)

class Tclish_handle():
	"""docstring for msgHandle"""
	def __init__(self, vm, name, handle, helps):
		self.vm=vm
		self.handle=handle
		self.name=name
		self.helps=helps
		self.prev=None

	def __enter__(self):
		self.prev=self.vm.add_handle(self.name,self.handle,self.helps)
		return self
			
	def __exit__(self,*args):
		self.vm.remove_handle(self.name,self.prev)


def main():
	vm=Tclish_interpreter()
	stdlib_math.add_stdmath(vm.commands)
	stdlib_common.add_stdcommon(vm.commands)
	task=Tclish_task("""
		defproc cake {
			args map a b
			return [+ $a $b]
		}
		cake "lol" "thing"
		foreach item [list 1 2 3] {
			print $item
			if {== $item 2} {
				return "a banana"
			}
		}
		return cake
	""")

	ok,res=asyncio.run(vm.eval(task,task.prog))
	print(ok)
	print(res)

	with open("test.tcl","r") as f:
		task=tclish_task(f.read())
	ok,res=asyncio.run(vm.eval(task,task.prog))
	print(ok)
	print(res)

if __name__ == '__main__':
	main()