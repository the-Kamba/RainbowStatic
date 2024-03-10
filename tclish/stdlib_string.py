from .std_utils import *
import re
import fnmatch
import uuid


def vmchars(vm,task,args):
	if len(args)<1:
		return vm.error(task,"needs a string to split","char")
	return vm.ok(pack_strings(vm,[char for char in args[0]]))

def regex_match(vm,task, args):
	"""
	Matches a string against a regular expression and returns a list of matches.

	Usage:
	  regex_match <pattern> <string> ?<code_body>?

	Parameters:
	  - <pattern>: The regular expression pattern.
	  - <string>: The string to match against the pattern.
	  - ?<code_body>?: (Optional) A code body to process each match.

	Returns:
	  Tuple[bool, str]: A tuple indicating the success of the operation and the result or error message.
		- If success is True, the result contains a string representing the list of matches (or an empty string if no matches).
		- If success is False, the result contains an error message.

	Example:
	  regex_match "(\d{3}-\d{2}-\d{4})" "123-45-6789 and 987-65-4321" {
		print "Found SSN: $ans"
	  }
	"""
	if len(args)<2:
		return vm.error(task,"regex-match requires a pattern and at least a string","regex-match")

	pattern = args[0]
	input_string = args[1]
	code_body = None
	if len(args) == 3:
		code_body=args[2] 

	try:
		matches = re.findall(pattern, input_string)
		result = pack_strings(vm, matches)

		if code_body:
			processed_results = []
			for match in matches:
				task.set_value("match", match)
				ok, processed_result = vm.simple_eval(task,code_body)
				if vm.is_error(ok):
					return vm.error(processed_result)
				elif vm.is_return(ok) or vm.is_ok(ok):
					processed_results.append(processed_result)

			return vm.ok(pack_strings(vm, processed_results))

		return vm.ok(result)
	except re.error as e:
		return vm.error(f"Error in regular expression: {e}","regex-match")


def glob_test(vm,task, args):
	if len(args)<2:
		return vm.error(task,"glob-test requires a pattern and at least a string","glob-test")

	pattern = args[0]
	input_string = args[1]

	if fnmatch.fnmatch(input_string,pattern):
		return vm.ok("true")
	else:
		return vm.ok("")

def glob_match(vm,task, args):
	if len(args)<2:
		return vm.error(task,"glob-match requires a pattern and at least a string","glob-match")

	pattern = args[0]
	input_string = args[1]

	if fnmatch.fnmatch(input_string,pattern):
		return vm.ok(input_string)
	else:
		return vm.ok("")

def regex_test(vm, task, args):
	"""
	Tests if a string matches a regular expression pattern.

	Usage:
	  regex_test <pattern> <string>

	Parameters:
	  - <pattern>: The regular expression pattern.
	  - <string>: The string to test against the pattern.

	Returns:
	  Tuple[bool, str]: A tuple indicating the success of the operation and the result or error message.
		- If success is True, the result is "true" (string) if there is a match, or an empty string if there is no match.
		- If success is False, the result contains an error message.

	Example:
	  regex_test "^abc.*" "abcdef"
	"""
	if len(args) < 2:
		return vm.error(task, "regex-test requires a pattern and a string", "regex-test")

	pattern = args[0]
	input_string = args[1]

	try:
		if re.match(pattern, input_string):
			return vm.ok("true")
		else:
			return vm.ok("")
	except re.error as e:
		return vm.error(f"Error in regular expression: {e}", "regex-test")





def vmlen(vm,task,args):
	return vm.ok(to_string(len(getl(args,0,""))))
def vmstrip(vm,task,args):
	return vm.ok(getl(args,0,"").strip())
def vmlower(vm,task,args):
	return vm.ok(getl(args,0,"").lower())
def vmupper(vm,task,args):
	return vm.ok(getl(args,0,"").upper())
def vmsplit(vm,task,args):
	if len(args)<2:
		return vm.error(task,"split requires a string to split, and a string to split it by","split")
	return vm.ok(vm.pack_strings((args[0].split(args[1]))))
def vmjoin(vm,task,args):
	return vm.ok("".join(args))

def vmescape(vm,task,args):
	return vm.ok(escape_string(getl(args,0,"")))

def vmsubstring(vm, task, args):
	# Check if the required arguments are provided
	if len(args) < 1:
		return vm.error(task, "substring requires a string, start index, and end index", "substring")

	# Extract arguments
	input_string = args[0]
	if len(args)>1:
		start_index = to_integer(args[1])
	else:
		start_index = 1
	if start_index is None:
		return vm.error(task,"start index must be a valid integer","substring")

	if len(args)>2:
		stop_index = to_integer(args[2])
	else:
		stop_index = 1
	if stop_index is None:
		return vm.error(task,"stop index must be a valid integer","substring")
	# Perform substring operation
	substring_result = input_string[start_index-1 : stop_index]
	#print(f"{start_index}:{stop_index}:{substring_result}")

	return vm.ok(substring_result)

def vmuuid(vm,task,args):
	return vm.ok(str(uuid.uuidv4()))



def add_stdstring(register):
	register.add("uuid", vmuuid, """usage:
  uuid

Returns a uuid in string form.""")

	register.add("sub", vmsubstring, """usage:
  sub <string> <start> <end>

Returns a substring of the given string with both ends inclusive.""")

	register.add("len", vmlen, """usage:
  len <string>

Returns the length of the given string.""")

	register.add("strip", vmstrip, """usage:
  strip <string>

Returns a copy of the string with leading and trailing whitespace removed.""")

	register.add("lower", vmlower, """usage:
  lower <string>

Returns a lowercase version of the given string.""")

	register.add("upper", vmupper, """usage:
  upper <string>

Returns an uppercase version of the given string.""")

	register.add("split", vmsplit, """usage:
  split <string> <separator>

Splits the string into a list of substrings using the specified separator.""")

	register.add("join", vmjoin, """usage:
  join <string1> <string2> ...

Joins the given strings into a single string.""")


	register.add("chars",vmchars,"""usage:
  chars <string>

Returns a list of characters in the given string.""")

	register.add("escape",vmescape,"""usage:
  escape <string>

Escapes a string.""")
	register.add("regex-match", regex_match, r"""Usage:
  regex-match <pattern> <string> [<code_body>]

Matches a string against a regular expression and returns a list of matches.


Parameters:
  - <pattern>: The regular expression pattern.
  - <string>: The string to match against the pattern.
  - <code_body>: (Optional) A code body to process each match.

Returns:
  A string representing the list of matches, or the processed results if a code body is provided. If an error occurs during the regular expression matching or code body evaluation, an error is thrown.

Example:
  regex-match {(\d{3}-\d{2}-\d{4})} "123-45-6789 and 987-65-4321" {
	print "Found SSN: $ans"
  }

proc regex-gather {pattern text} {
	regex-match $patter $text {
		get match
	}
} {usage:
  regex-gather <pattern> <text>
	
return a list of matches
(same as [regex-match pattern text])
}
""")
	register.add("glob-match", glob_match, r"""Usage:
  glob-match <pattern> <string>

Matches a string against a glob-style pattern.

Parameters:
  - <pattern>: The glob-style pattern.
  - <string>: The string to match against the pattern.

Returns:
  A string indicating whether there is a match (returns the origina string) or not (returns an empty string).

Example:
  glob-match "abc*" "abcdef"
""")
	register.add("glob-test", glob_test, r"""Usage:
  glob-test <pattern> <string>

Matches a string against a glob-style pattern.


Parameters:
  - <pattern>: The glob-style pattern.
  - <string>: The string to match against the pattern.

Returns:
  A string indicating whether there is a match (returns "true") or not (returns an empty string).

Example:
  glob-test "abc*" "abcdef"
""")
	register.add("regex-test", regex_test, r"""Usage:
  regex-test <pattern> <string>

Tests if a string matches a regular expression pattern.

Parameters:
  - <pattern>: The regular expression pattern.
  - <string>: The string to test against the pattern.

Returns:
  A string indicating whether there is a match (returns "true") or not (returns an empty string). If an error occurs during the regular expression matching, an error is thrown.

Example:
  regex-test "^abc.*" "abcdef"
""")


