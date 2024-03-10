from .std_utils import getl,unpack_strings,escape_string
class tclish_command_registry():
	"""docstring for tclish_command_registry"""
	def __init__(self,parent=None):
		self.commands={}
		self.parent=None

	def remove(self,name):
		if name in self.commands:
			del self.commands[name]

	def add(self,name,func,helps):
		#name=name.encode("utf-8")
		if name in self.commands:
			return False,f"'{name}' is already defined"

		self.commands[name]={
			"function" : func,
			"help" : helps,
		}
		return True,""

	def get(self,name):
		if name in self.commands:
			return self.commands[name]["function"]
		if self.parent is not None:
			return self.parent.get(name)
		return None

	def help(self,name):
		if name in self.commands:
			return self.commands[name]["help"]
		if self.parent is not None:
			return self.parent.help(name)
		return None

	def keys(self):
		return list(self.commands.keys())

class tclish_object_registry():
	"""Docstrign"""
	def __init__(self):
		self.object_id=0
		self.objects={}
		self.named_objects={}
		self.classes={}
		self.names={}

	def tojson(self):
		return {
			"named_objects":self.named_objects,
			"object_id":self.object_id,
			"classes":self.classes,
			"names":self.names,
			"objects":self.objects,
		}
	def fromjson(self,data):
		#print("VM fromjson")
		if "named_objects" in data:
			for k,v in data["named_objects"].items():
				self.named_objects[k]=v
		if "object_id" in data:
			self.object_id=data["object_id"]
		if "classes" in data:
			for k,v in data["classes"].items():
				self.classes[k]=v
		if "names" in data:
			for k,v in data["names"].items():
				self.names[k]=v
		if "objects" in data:
			for k,v in data["objects"].items():
				self.objects[k]=v
		
	# this needs async
	def get_handle(self,instance):
		async def hand(vm,task,args):
			return await self.instance_command(instance,vm,task,args)
		return hand
	def get_help(self,instance):
		return str(instance)
	def is_object(self,object_id):
		if object_id in self.objects:
			return True
		elif object_id in self.named_objects:
			object_name=object_id
			object_id=self.named_objects[object_name]
			if object_id in self.objects:
				return True
			else:
				return False
		else:
			return False

	def show_object(self,object_id):
		instance = self.get_instance(object_id)
		if instance is None:
			return None
		text=[
			"id ",instance["id"],
			"\nclass ",instance["class"],
		]
		if ("name" in instance) and (instance["name"] is not None):
			text.append("\nname ")
			text.append(instance["name"])
		text.append("\nvars")
		for key,value in instance["vars"].items():
			text.append("\n  ")
			text.append(key)
			text.append(" ")
			text.append(value)
		return "".join(text)

	def show_class(self,vm,class_name):

		if class_name not in self.classes:
			return None
		class_prototype=self.classes[class_name]
		text=[
			"class ",class_name,
		]
		if ("constructor" in class_prototype) and (class_prototype["constructor"] is not None) and (class_prototype["constructor"]!=""):
			head=vm.extract_header(class_prototype["constructor"])
			if head is not None:
				text.append(" { ")
				text.append(" ".join(head))
				text.append(" }")
			else:
				text.append(" <args...>")


		text.append("\nvars")
		for key,value in class_prototype["vars"].items():
			text.append("\n  ")
			text.append(key)
			text.append(" ")
			text.append(value["type"])
			text.append(" ")
			text.append(value["value"])
		text.append("\nmethods")
		for key,value in class_prototype["methods"].items():
			text.append("\n  ")
			text.append(key)
			head=vm.extract_header(value)
			if head is not None:
				text.append(" { ")
				text.append(" ".join(head))
				text.append(" }")
		return "".join(text)


	def get_instance(self,object_id):
		if object_id in self.objects:
			return self.objects[object_id]
		elif object_id in self.named_objects:
			object_name=object_id
			object_id=self.named_objects[object_name]
			if object_id in self.objects:
				return self.objects[object_id]
			else:
				return None
		else:
			return None

	# this needs async
	async def instance_command(self,instance,vm,task,args):

		if not instance["class"] in self.classes:
			i=instance["class"]
			return vm.error(task,f"object is of class {i} which doesn't exist.","object")

		prototype=self.classes[instance["class"]]
		method = getl(args,0,None)
		object_id=instance["id"]
		if method is None:
			return vm.error(task,f"object needs a directive","object")

		if method=="get":
			varname = getl(args,1,None)
			if varname is None:
				return vm.error(task,f"object get needs a varname","object")
			if not varname in instance["vars"]:
				return vm.error(task,f"object {object_id} has not member variable {varname}","object")
			return vm.ok(instance["vars"][varname])
		
		elif method=="set":
			varname = getl(args,1,None)
			if varname is None:
				return vm.error(task,f"object set needs a varname","object")
			varvalue = getl(args,2,None)
			if varname is None:
				return vm.error(task,f"object set needs a value","object")

			if varname in prototype["vars"]:
				splat="{*}"
				type_validator=prototype["vars"][varname]["type"]
				ok,res=await vm.eval(task,f"{type_validator} {splat} [args list]",args=[varvalue])
				if not ok:
					return vm.error(task,f"error in type validator {varname} <{type_validator}> = {varvalue}.\n{res}","object")
				if res=="":
					return vm.error(task,f"value is not valid for type {varname} <{type_validator}> = {varvalue}.","object")
				instance["vars"][varname]=varvalue
				return vm.ok("")
			else:
				instance["vars"][varname]=varvalue
				return vm.ok("")

		elif method == "id":
			return vm.ok(instance["id"])
		elif method == "show":
			text=self.show_object(object_id)
			if text is None:
				return vm.error(task,"instance is None. how?","instance show")
			return vm.ok(text)
		elif method == "show-class":
			text=self.show_class(vm,prototype["name"])
			if text is None:
				return vm.error(task,"class is None. how?","instance show")
			return vm.ok(text)
		elif method == "class":
			return vm.ok(instance["class"])
		elif method == "delete":
			if instance["name"] in self.named_objects:
				del self.named_objects[instance["name"]]
			del self.objects[instance["id"]]
			return vm.ok("")

		elif method in prototype["methods"]:
			method_body=prototype["methods"][method]
			vm.add_handle("self",self.get_handle(instance),self.get_help(instance))

			ok,res=await vm.eval(task,method_body,args=args[1:])

			vm.remove_handle("self")
			return ok,res

		elif method in instance["vars"]:
			return vm.ok(instance["vars"][method])


		return vm.error(task,f"directive {method} is undefined","object")


	def object_type_command(self,vm,task,args):
		if len(args)<1:
			return vm.error(task,"","object-type")
		instance=self.get_instance(args[0])
		if instance is None:
			return vm.ok("")
		return vm.ok(instance["class"])


	# this needs async
	async def object_command(self,vm,task,args):
		"""
		object <instance-car-10> method-name <args...>
		object instance-name method-name <args...>

		object instance-name set varname value
		object instance-name get varname

		object instance-name varname

		object instance-name id
		object instance-name class

		"""
		object_id = getl(args,0,None)

		if object_id is None:
			return vm.error(task,"object command needs an id","object")

		if object_id in self.objects:
			instance = self.objects[object_id]
		elif object_id in self.named_objects:
			object_name=object_id
			object_id=self.named_objects[object_name]
			if object_id in self.objects:
				instance=self.objects[object_id]
			else:
				return vm.error(task,f"object with name {object_name} is broken","object")
		else:
			return vm.error(task,f"object {object_id} doesn't exist","object")

		if not instance["class"] in self.classes:
			instance_name=instance["class"]
			return vm.error(task,f"object is of class {instance_name} which doesn't exist.","object")

		prototype=self.classes[instance["class"]]

		return await self.instance_command(instance,vm,task,args[2:])


	def get_id(self,class_name="object"):
		self.object_id+=1
		return f"<instance-{class_name}-{self.object_id}>"

	# this needs async
	async def instantiate_class(self,vm,task,args):
		if len(args)<1:
			return vm.error(task,f"a class name is needed","new")
		class_name=args[0]
		instance_name=getl(args,1,None)
		if not class_name in self.classes:
			return vm.error(task,f"class {class_name} does not exist","new")
		instance={
			"id":self.get_id(class_name),
			"name":instance_name,
			"class":class_name,
			"vars":{}
		}
		for name,things in self.classes[class_name]["vars"].items():
			instance["vars"][name]=things["value"]

		if self.classes[class_name]["constructor"] != "":
			vm.add_handle("self",self.get_handle(instance),self.get_help(instance))

			ok,res=await vm.eval(task,self.classes[class_name]["constructor"],args=args[2:])

			vm.remove_handle("self")

			if vm.is_abort(ok):
				return ok,res

			self.objects[instance["id"]]=instance
			if instance_name is not None:
				self.named_objects[instance_name]=instance["id"]
			return vm.ok(res)
		else:
			pos=2
			
			def done():
				nonlocal pos
				return pos >= len(args)
			def consume(s=None):
				nonlocal pos
				r=getl(args,pos,s)
				pos+=1
				return r

			while not done():
				varname = consume()
				if varname in self.classes[class_name]["vars"]:
					splat="{*}"
					varvalue=consume("")
					type_validator = self.classes[class_name]["vars"][varname]["type"]
					ok,res=await vm.eval(task,f"{type_validator} {splat} [args list]",args=[varvalue])
					if vm.is_abort(ok):
						return vm.error(task,f"error in type validator {varname} <{type_validator}> = {varvalue}.\n{res}",f"new {class_name}")
					if res=="":
						return vm.error(task,f"value is not valid for type {varname} <{type_validator}> = {varvalue}.",f"new {class_name}")
					instance["vars"][varname]=varvalue


		self.objects[instance["id"]]=instance
		if instance_name is not None:
			self.named_objects[instance_name]=instance["id"]
		
		return vm.ok(instance["id"])

	def make_class(self,vm,task,args):

		pos=0
		def done():
			return pos>=len(args)
		def consume(default=None):
			nonlocal pos
			r=getl(args,pos,default)
			pos+=1
			return r

		class_name=consume()

		if class_name is None:
			return vm.error(task,"class needs a name","class")

		prototype={
			"methods":{},
			"name":class_name,
			"vars":{},
			"constructor":""
		}

		while not done():
			match consume("").lower():
				case "var":
					name=consume()
					if name is None:
						return vm.error(task,"var needs a name","class var")
					
					prefix=consume()
					if prefix is None:
						return vm.error(task,"var needs a type in the form of a preposition","class var")
					
					initial_value=consume()
					if initial_value is None:
						return vm.error(task,"var needs an initial value","class var")
					
					prototype["vars"][name] = {
						"type":prefix,
						"value":initial_value,
					}

				case "method":
					name=consume()
					if name is None:
						return vm.error(task,"method needs a name","class method")
					
					body=consume()
					if body is None:
						return vm.error(task,"method needs a body","class method")
					
					prototype["methods"][name] = body

				case "proc":
					name=consume()
					if name is None:
						return vm.error(task,"method needs a name","class proc")

					parameters=consume()
					if parameters is None:
						return vm.error(task,"method needs a parameter list","class proc")

					ok,proc_args=unpack_strings(self,parameters)
					
					if not ok:
						return vm.error(task,f"error with args \n{proc_args}","class proc")
					
					body=consume()
					if body is None:
						return vm.error(task,"method needs a body","class proc")
					
					proc_args="'"+"' '".join([escape_string(arg) for arg in proc_args])+"'"
					
					prototype["methods"][name] = f"args map {proc_args}\n{body}"
				
				case "constructor":
					body=consume()
					if body is None:
						return vm.error(task,"constructor needs a body","class constructor")
					prototype["constructor"] = body

				case "helps":
					text=consume()
					if text is None:
						return vm.error(task,"helps need a helpstring","class helps")

		self.classes[class_name]=prototype
		return vm.ok("")


	class_helpstring=r"""usage:
  class <class-name> \
    [var <var-name> <type> <initial-value>] \
    [method <method-name> <method-body>]... \
    [proc <method-name> <arguments> <method-body>]... \
    [constructor <constructor-body>] \
    [helps <help-text>]

Define a new class with the specified name. A class may have variables, methods, and a constructor. Each component is specified using keywords like 'var', 'method', 'constructor', and 'helps'.

Variables:
  Specify class variables with the 'var' keyword. Provide the variable name, type, and initial value.
  The type comes in the form of a validator function that takes the new value as the sole argument and returns and empty string if the value is invalid.

Methods:
  Define class methods using the 'method' keyword. Include the method name and its body.

Procedures:
  Define class methods using the 'proc' keyword. Same regular methods, but explicitly sprecify the arguments it takes.

Constructor:
  The 'constructor' keyword is used to define the constructor method for the class.

Helps:
  Include a 'helps' section to provide additional information about the class.

Example:
  class counter \
    var counter integer? 0 \
    var data any? "lol" \
    constructor {
      self set counter [args 1]
    } \
    method increment {
      self set counter [+ 1 [self get counter]]
      self get counter
    } \
    method add {
      args map a
      self set counter [+ $a [self get counter]]
      self get counter
    } \
    helps {
      text
    }

Create an instance of the class:
  new counter instance-name args-to-constructor...

Access instance variables:
  object $object-reference get counter
  instance-name get counter

  object $object-reference set counter 1
  instance-name set counter 1

Run instance methods
  object $object-reference method-name args...
  instance-name method-name args...

"""
	new_helpstring=r"""usage:
	new <class name> [<instance name>] [<args...>]

create a new instance if <class name>. 
if <instance name> is provided, the instance is boud to that name.
if the class does not have a constructor, the object-id is returned.
if it does have a constructor, <args> is passed to it, and the new command returns whatever the constructor returns.
"""
	def add_commands(self,vm):
		async def local_object_command(vm,task,a):
			return await self.object_command(vm,task,a)
		vm.add_command("object",local_object_command,"""usage:
	object <object-id> [<args...>]

Equivalent to [object-name <args...>]
""")
		vm.add_command("object-type",lambda vm,task,a:self.object_type_command(vm,task,a),"""usage:
	object-type <object-id>

Returns the class of the object. 
""")
		vm.add_command("named-objects",lambda vm,task,a:vm.ok(str(self.named_objects)),"")
		vm.add_command("objects",lambda vm,task,a:vm.ok(str(self.objects)),"")
		vm.add_command("classes",lambda vm,task,a:vm.ok(vm.pack_strings(self.classes.keys())),"")
		def local_class_command(vm,task,a):
			return self.make_class(vm,task,a)
		vm.add_command("class",local_class_command,self.class_helpstring)
		async def local_instantiate_class(vm,task,a):
			return await self.instantiate_class(vm,task,a)
		vm.add_command("new",local_instantiate_class,self.new_helpstring)