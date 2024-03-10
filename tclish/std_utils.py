import asyncio
import inspect



whitespace = set("\x09\x0A\x0B\x0C\x0D\x20")
special_chars = set("[]{}'\"")
escapes_chars = {
	"n" : "\n",
	"t" : "\t",
	"b" : "\b",
	"r" : "\r",
}
hex_set = set("0123456789abcdefABCDEF")



def is_command_name(name):
	contains_whitespace = any(char in whitespace for char in name)
	contains_special_chars = any(char in special_chars for char in name)

	return not (contains_whitespace or contains_special_chars)


def is_async_function(func):
	return inspect.iscoroutinefunction(func)

async def call_async(f,*args,**kvargs):
	if is_async_function(f):
		return await f(*args,**kvargs)
	elif callable(f):
		return f(*args,**kvargs)
	else:
		raise ValueError(f"{f} <{type(f)}> is neither callable, nor coroutine.")

def async_callable(f):
	if is_async_function(f):
		return True
	elif callable(f):
		return True
	else:
		return False

def getl(a,i,d):
	if i<0:
		return d
	if len(a)>i:
		return a[i]
	return d

def isTrue(s):
	if s=="":
		return False
	return True

is_true=isTrue

def escape_length(s,pos):
	if s[pos] != "\\":
		return 1
	if pos+1 >= len(s):
		return 1
	if s[pos+1].lower()=="x":
		return 3
	if s[pos+1].lower()=="u":
		l=2
		while (pos+l)<len(s) and s[pos+l] in hex_set:
			l+=1
		return l
	return 1

def encode_char(s,pos):
	if pos >= len(s):
		return ""
	e=s[pos+1].encode("unicode_escape")
	return e

def escape_string(s):
	r=""
	for char in s:
		if char in special_chars:
			r+="\\"+char
		elif char=="\\":
			r+="\\\\"
		else:
			r+=char
	return r

def unescape_string(s):
	if False:
		return s.encode().decode("unicode_escape")
	pos=0
	r=""
	while pos<len(s):
		if s[pos]=="\\":
			l=escape_length(s,pos)
			#print(s[pos:pos+l])
			if l==1:
				if s[pos+1] in escapes_chars:
					r+=escapes_chars[s[pos+1]]
				else:
					r+=s[pos+1]
			else:
				r+=s[pos:pos+l+1].encode("utf-8").decode("unicode_escape")
			pos+=l+1
			# if pos+2<len(s) and (s[pos+1] in hex_set) and (s[pos+1] in hex_set):
			# 	r+=chr(int(s[pos+1:pos+3],16))
			# 	pos+=3
			# elif pos+1<len(s):
			# 	r+=s[pos+1]
			# 	pos+=2
			# else:
			# 	r+="\\"
			# 	pos+=1
		else:
			r+=s[pos]
			pos+=1
	return r

def skip_whitespace(s, pos):
	newline = False
	while pos < len(s) and s[pos] in whitespace:
		newline = newline or s[pos] == "\n"
		pos += 1
	return pos, newline

def skip_non_whitespace(s, pos):
	while pos < len(s) and ((s[pos] not in whitespace) and (s[pos] not in special_chars)):
		pos += 1
	return pos


def skip_whitespace(s, pos):
	newline = False
	while pos < len(s) and s[pos] in whitespace:
		newline = newline or s[pos] == "\n"
		pos += 1
	return pos, newline

def skip_non_whitespace(s, pos):
	while pos < len(s) and ((s[pos] not in whitespace) and (s[pos] not in special_chars)):
		pos += 1
	return pos

def skip_string(vm, s, pos):
	if pos >= len(s):
		return False,"skipping beyond the end of the string"

	if stops.get(s[pos]):
		return True, pos

	return_pos = None
	success = True

	if skips.get(s[pos]):
		success, return_pos = skips[s[pos]](vm, s, pos)
		if not success:
			return False, return_pos
	else:
		if s[pos] == "}":
			return False,"error trailing '}'"
		return_pos = skip_non_whitespace(s, pos)

	return True, return_pos

def skip_big_string(vm, s, pos):
	# Step into the string
	pos = pos + 1
	if pos >= len(s):
		#return False, "unterminated big string"
		return True, pos
	if s[pos] == "\"":
		# Terminate early if an empty string
		return True, pos + 1

	escape = False
	success = True

	while pos < len(s) and s[pos] != "\"":
		escape = (s[pos] == "\\")

		if escape:
			pos+=escape_length(s,pos)+1
		else:
			if s[pos] == "[":
				start_pos = pos

				success, pos = skip_command_string(vm, s, pos)
				if not success:
					return False, pos
				if pos == start_pos:
					return False,"error progressing skip_big_string"
			else:
				pos += 1

	return True, pos + 1

def skip_small_string(vm, s, pos):
	escape = False

	escape = s[pos] == "\\" and (not escape)
	pos += 1
	while pos < len(s) and (escape or s[pos] != "'"):
		escape = s[pos] == "\\" and (not escape)
		pos += 1

	return True, pos + 1

def skip_command_string(vm, s, pos):
	# Commands string is balanced around [str], everything can be embedded
	if not s[pos] == "[":
		return False,"invalid command string"

	success = True
	newline = False
	pos += 1

	while pos < len(s) and s[pos] != "]":
		pos, newline = skip_whitespace(s, pos)
		start_pos = pos

		success, pos = skip_string(vm, s, pos)
		if not success:
			return success, pos

		# Hack, please fix. Did not fix all problems
		if pos>=len(s):
			return False,"<skip_command_string> skipping past end of string"
		if s[pos] == "}":
			print("Trailing curly brackets '{}'".format(s[pos - 4:pos + 5]))
			pos += 1

		if pos == start_pos and s[pos] != "]":
			pos += 1
			return False,"error progressing skip_command '{}'".format(s[pos - 4:pos + 5])

	return True, pos + 1

def skip_very_big_string(self,s, pos):
	# Very big string is balanced around {str}, nothing can be embedded
	count = 1

	while count > 0 and (pos+1) < len(s):
		pos += 1
		if s[pos] == "{":
			count += 1
		elif s[pos] == "}":
			count -= 1

	return True, pos + 1

skips = {
	"\"": skip_big_string,
	"'": skip_small_string,
	"[": skip_command_string,
	"{": skip_very_big_string
}

stops = {
	"]": skip_command_string,
	"}": skip_very_big_string
}
async def clean_big_string(vm,task, s, e):
	tmp = s[1:]
	temp_result = []
	escape = False
	pos = 0
	success = True

	while pos < len(tmp) and tmp[pos] != "\"":
		escape = (tmp[pos] == "\\")

		if escape:
			l=escape_length(s,pos)
			temp_result.append(unescape_string(tmp[pos:pos+l+1]))
			pos+=l+1
		elif tmp[pos] == "$":
			word,npos=read_word(tmp,pos+1)
			#print(f"WORD [{word}] {pos}:{npos}")
			if word is not None:
				val=task.get_value(s[1:])
				if val is None:
					val=vm.get_value(s[1:])
				if val is None:
					val=""
				#print(value)
				temp_result.append(val)
				pos=npos
			else:
				temp_result.append("$")
				pos+=1

		elif tmp[pos] == "[":
			start = pos
			success, pos = skip_command_string(vm,tmp, pos)
			if not success:
				return vm.error(task,pos)
			if pos == start:
				return vm.error(task,"error cleaning big string", "clean_string")
			if async_callable(e):
				success, r = await call_async(e,vm,task, tmp[start + 1:pos - 1])
			else:
				success, r = await vm.simple_eval(task,tmp[start + 1:pos - 1])
			if vm.is_abort(success):
				return success,r
			temp_result.append(r)
		else:
			temp_result.append(tmp[pos])
			pos += 1

	return vm.ok(''.join(temp_result))

async def clean_small_string(vm,task, s, e):
	return vm.ok(unescape_string(s[1:-1]))

async def clean_command_string(vm,task, s, e):
	if async_callable(e):
		return await call_async(e, vm, task, s[1:-1])
	else:
		return await vm.simple_eval(task,s[1:-1])

async def clean_very_big_string(vm,task, s, e):
	return vm.ok(s[1:-1])

async def clean_variable_string(vm,task, s, e):
	val=vm.get_value(s[1:],task=task)
	# val=task.get_value(s[1:])
	# if val is None:
	# 	val=vm.get_value(s[1:])
	if val is None:
		val=""
	return vm.ok(val)


clean_strings_lookup = {
	"\"": clean_big_string,
	"'": clean_small_string,
	"[": clean_command_string,
	"{": clean_very_big_string,
	"$": clean_variable_string
}


async def clean_simple_string(vm,task, s, e):
	return vm.ok(s)

async def clean_strings(vm, task, s, e=None):
	if len(s)<1:
		return vm.ok(s)
	f = clean_strings_lookup.get(s[0], clean_simple_string)
	return await f(vm, task, s, e)


def pack_strings(self,strings):
	r="{"
	for s in strings:
		r+="'"+escape_string(s)+"'"
	return r+"}"

def split_string_internal(self,s):
	pos,newline=skip_whitespace(s,0)
	success, endpos = skip_string(self, s, pos)
	if not success:
		return False, endpos, None

	if endpos==pos:
		#force a minimum length of 1
		endpos+=1

	substr = s[pos:endpos]
	reststr = s[endpos:]

	return True, substr,reststr

def unpack_strings(self, s):
	if s.startswith("{") and s.endswith("}"):
		s=s[1:-1]

	strings=[]

	while len(s)>1:
		ok,substr,temp_s=split_string_internal(self,s)
		#print(f"[{ok}|{substr}|{temp_s}]")
		if ok:
			s=temp_s
			if substr.startswith("'") and substr.endswith("'"):
				substr=unescape_string(substr[1:-1])
			#ok,substr=clean_strings(self,substr,e=lambda _,s:s)
			strings.append(substr)
		else:
			break
	if len(s)>0:
		strings.append(s)
	return True,strings



def to_number(s):
	try:
		return int(s)
	except ValueError:
		pass
	try:
		i=float(s)
		# if i.is_integer():
		# 	return int(i)
		# return None
		return i
	except ValueError:
		pass
	return None
def to_integer(s):
	try:
		return int(s)
	except ValueError:
		pass

	try:
		i=float(s)
		if i.is_integer():
			return int(i)
		return None
	except ValueError:
		pass
	return None

def to_string(n):
	if n is None:
		return ""
	if isinstance(n,bool):
		if n:
			return "true"
		else:
			return ""
	if isinstance(n,float) and n.is_integer():
		return str(int(n))
	return str(n)

def extract_header(vm,task, s):
	startpos,newline=skip_whitespace(s,0)
	ok,pos,sentence=vm.read_sentence(task,s,startpos)
	if not ok:
		return None
	if sentence is None:
		return None
	if len(sentence)<2:
		return None
	if sentence[0]=="args" and sentence[1]=="map":
		return sentence [2:]
	return None

def read_word(s,pos):
	if pos>=len(s)-1:
		return None,pos
	startpos=pos
	if s[pos]=="{":
		pos+=1
		invalid_letters=set("\\{}")
		while pos<len(s) and (s[pos] not in invalid_letters):
			pos+=1
		if pos>=len(s):
			pos=len(s)-1

		if s[pos]=="}":
			return s[startpos+1:pos],pos+1
		else:
			return s[startpos:pos],pos
	else:
		valid_letters=set("_-")
		while pos<len(s) and (s[pos].isalnum() or (s[pos] in valid_letters)):
			pos+=1
		return s[startpos:pos],pos

def nested_help_function(name, description, subs):
	def helper(vm, task, args):
		keys = sorted(subs.keys())
		options = " | ".join(map(str, keys))

		if (not args) or (len(args)<1):
			return vm.ok("\n".join([
				f"usage:",
				f"  help {name} <switch> [args...]",
				"",
				"specify a switch to access the specific function",
				f"do [help {name} <switch>] to get more specific options",
				"",
				"options are:",
				f"  {options}",
				"",
				str(description),
			]))

		switch = args[0]
		s = subs.get(switch)

		if not s:
			return vm.ok("\n".join([
				f"{name} does not specify help for {switch}",
				"options are:",
				options
			]))

		if callable(s):
			return s(vm, task,args[1:])
		else:
			return vm.ok(str(s))

	return helper