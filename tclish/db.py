from .std_utils import *
from typing import List

def escape_delimiter(field: str, delimiter: str) -> str:
	# Escape occurrences of the delimiter in the field
	return field.replace(delimiter, f"\\{delimiter}")

def unescape_delimiter(field: str, delimiter: str) -> str:
	# Unescape occurrences of the escaped delimiter in the field
	return field.replace(f"\\{delimiter}", delimiter)

def pack_string(name: str, fields: List[str], value: str = None, delimiter: str = ":") -> str:
	# Escape the delimiter in each field
	escaped_fields = [escape_delimiter(field, delimiter) for field in fields]

	# Join escaped fields with the delimiter
	packed_fields = delimiter.join(escaped_fields)

	# If value is provided, escape and include it with appropriate delimiters
	if value is not None:
		escaped_value = escape_delimiter(value, delimiter)
		packed_value = f"{delimiter}{escaped_value}{delimiter}"
	else:
		packed_value = ""

	# Combine everything and return the packed string
	packed_string = f"{name}{delimiter}{packed_fields}{packed_value}"
	return packed_string

def unpack_string(packed_str: str, delimiter: str = ":"):
	# Split the packed string into components
	components = packed_str.split(delimiter)

	# Extract name, fields, and value
	name = components[0]
	fields = [unescape_delimiter(field, delimiter) for field in components[1:-1]]  # Exclude the first and last elements
	value = unescape_delimiter(components[-1], delimiter) if len(components) > 2 else None

	return name, fields, value









class Tclish_DB():
	"""
	A hierarchical key-value database.

	This class represents a hierarchical key-value store where keys are organized in a tree-like structure.
	Each key can have a corresponding value, and keys at different levels are used to organize and structure the data.

	Example:
	set [key1] val1
	set [key1 key2] val2
	set [key1 key3] val3
	set [key1 key3 key8] val8
	set [key1 key9] val9
	set [key4] val4

	root
	* key1 -- val1
		* key2 -- val2
		* key3 -- val3
			* key8 -- val8
		* key9 -- val9
	* key4 -- val4
	"""

	def __init__(self):
		"""
		Initializes an instance of the TclishDB class.

		The constructor creates an empty hierarchical key-value store represented as a dictionary.
		"""
		self.db = {}

	def pack(self,item):
		if isinstance(item,str):
			return item
		packed={"values":{}}
		if 0 in item:
			packed["item"]=item[0]
		#count=0
		for k,v in item.items():
			if isinstance(k,str):
				#count+=1
				packed["values"][k]=self.pack(v)
		#if count==0:
		#	del packed["values"]
		return packed

	def tojson(self):
		return self.pack(self.db)

	def unpack(self,db_entry,item):
		if "item" in item:
			db_entry[0]=item["item"]
		if "values" in item:
			for k,v in item["values"].items():
				if not k in db_entry:
					db_entry[k]={}
				self.unpack(db_entry[k],v)
				
	def fromjson(self,items):
		return self.unpack(self.db,items)

	def set(self, keys, value):
		"""
		Sets a value in the hierarchical key-value store.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.
			value (str): The value to be associated with the specified keys.
		"""
		current_node = self.db
		for key in keys:
			current_node = current_node.setdefault(key, {})
		current_node[0] = value

	def unset(self, keys):
		"""
		Removes a value from the hierarchical key-value store.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.
		"""
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return  # Key not found, nothing to unset
		if 0 in current_node:
			del current_node[0]

	def get(self, keys):
		"""
		Gets a value from the hierarchical key-value store.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.

		Returns:
			str: The value associated with the specified keys, or an empty string if it is not present.
		"""
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return ""  # Key not found, return an empty string
		if 0 in current_node:
			return current_node[0]
		return ""

	def has(self, keys):
		"""
		Checks if the specified keys exist in the hierarchical key-value store.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.

		Returns:
			bool: True if the keys exist in the store, False otherwise.
		"""
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return False  # Key not found
		if 0 in current_node:
			return True
		return False

	def list(self, keys):
		"""
		Lists all the immediate child keys under the specified hierarchical keys.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.

		Returns:
			list[str]: A list of strings representing the immediate child keys.
		"""
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return []  # Key not found, return an empty list
		return [key for key in current_node.keys() if isinstance(key,str)]

	def prune(self, keys):
		"""
		Prunes the hierarchical key-value store by removing the specified keys and their subkeys.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys to be pruned.
		"""
		if len(keys)<1:
			print("cannot delete the entire database, do it for each primary key")
			return
		current_node = self.db
		for key in keys[:-1]:
			if key in current_node:
				current_node = current_node[key]
			else:
				return  # Key not found, nothing to prune
		if keys[-1] in current_node:
			del current_node[keys[-1]]

	def show(self, keys):
		"""
		Returns the structure of the specified subtree of the hierarchical key-value store as a string.

		Args:
			keys (list[str]): A list of strings representing the hierarchical keys.

		Returns:
			str: The string representation of the subtree structure.

		Example:
		If the database has the following structure:
		root
		* key1 -- val1
			* key2 -- val2
			* key3 -- val3
				* key8 -- val8
			* key9 -- val9
		* key4 -- val4

		Calling db.show(["key1", "key3"]) will return:
		"key3 -- val3\n    key8 -- val8\nkey9 -- val9\n"
		"""
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return ""

		return self._get_tree(keys, current_node, "")

	def _get_tree(self, keys, node, indent):
		subtree_str = ""
		for key, value in node.items():
			if isinstance(key, str):
				if 0 in value:
					val= f" -- {value[0]}"
				else:
					val=""
				subtree_str += f"{indent}* {key}{val}\n"
				if isinstance(value, dict):
					subtree_str += self._get_tree(keys + [key], value, indent + "  ")

		return subtree_str

	def show_keys(self, keys):
		current_node = self.db
		for key in keys:
			if key in current_node:
				current_node = current_node[key]
			else:
				return "Subtree not found."

		return self._get_tree_keys(keys, current_node, "")

	def _get_tree_keys(self, keys, node, indent):
		subtree_str = ""
		for key, value in node.items():
			if isinstance(key, str):
				if 0 in value:
					val= f" *"
				else:
					val=""
				subtree_str += f"{indent}* {key}{val}\n"
				if isinstance(value, dict):
					subtree_str += self._get_tree_keys(keys + [key], value, indent + "  ")

		return subtree_str

	def vm_command(self):
		def vm_db_command(vm,task, args):
			"""
			Database command for interacting with a key-value database.
			"""
			if not args:
				return vm.error(task,"Missing command for 'db'.","db")

			command = args[0].lower()
			#self = vm.db

			if command == "get":
				keys = args[1:]
				value = self.get(keys)
				return vm.ok(value)

			elif command == "set":
				keys = args[1:-1]
				value = args[-1]
				self.set(keys, value)
				return vm.ok(value)

			elif command == "unset":
				keys = args[1:]
				self.unset(keys)
				return vm.ok("")

			elif command == "has":
				keys = args[1:]
				result = self.has(keys)
				if result:
					return vm.ok("true")
				else:
					return vm.ok("")

			elif command == "list":
				keys = args[1:]
				key_list = self.list(keys)
				return vm.ok(vm.pack_strings(key_list))

			elif command == "prune":
				keys = args[1:]
				self.prune(keys)
				return vm.ok("")

			elif command == "show":
				keys = args[1:]
				prettystring=self.show(keys)
				return vm.ok(prettystring)

			elif command == "tree":
				keys = args[1:]
				prettystring=self.show_keys(keys)
				return vm.ok(prettystring)

			else:
				return vm.error(task,f"Error: Unknown 'db' command '{command}'.","db")
		helpstr="""usage:
(1) db get <fields...>
(2) db set <fields...> <value>
(3) db unset <fields...>
(4) db has <fields...>
(5) db list <fields...>
(6) db prune <fields...>
(7) db show <fields...>
(8) db tree <fields...>

The 'db' command provides a set of operations to interact with a key-value database within the Tclish interpreter. This command facilitates storing and retrieving data using a hierarchical key structure, allowing users to manage information efficiently. The supported operations include reading, setting, unsetting, checking the existence, listing keys, and pruning entries from the database.


(1) db get reads a value from the database
   Example:
   db get user profile name
   # Retrieves the value stored in 'user.profile.name'

(2) db set sets a value in the database
   Example:
   db set user profile name "John Doe"
   # Sets the value "John Doe" in 'user.profile.name'

(3) db unset unsets a value in the database
   Example:
   db unset user profile name
   # Unsets the value in 'user.profile.name'

(4) db has returns true if the db has a specified entry
   Example:
   db has user profile name
   # Returns true if 'user.profile.name' exists in the database

(5) db list returns a list of keys
   Example:
   db list user profile
   # Returns a list of keys under 'user.profile'

(6) db prune deletes specified entry, and all sub entries
   Example:
   db prune user profile
   # Deletes 'user.profile' and all its subentries

(7) db show prettyprints the specified subtree including the node values
   Example:

(8) db tree prettyprints the specified subtree excluding the node values
   Example:
"""
		return "db",vm_db_command,helpstr

