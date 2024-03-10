from typing import List,Optional,Tuple
from datetime import datetime,timedelta
import random
import string
import gzip
import io
import json
import os
from .db import Tclish_DB

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ESCAPES = [
	("\\","\\s"),
	("\n","\\n"),
	("[","\\l"),
	("]","\\r"),
	("|","\\b"),
]
def escape(string):
	for toreplace,replacement in ESCAPES:
		string=string.replace(toreplace,replacement)
	return string
def unescape(string):
	for toreplace,replacement in reversed(ESCAPES):
		string=string.replace(replacement,toreplace)
	return string



def pack_line(name: str, values: List[str], timestamp: Optional[str] = None) -> str:
	# Escape delimiter and values
	delimiter="|"
	escaped_name = escape(name)
	escaped_values = [escape(value) for value in values]
	if timestamp is None:
		escaped_timestamp = datetime.now().strftime(TIME_FORMAT)
	else:
		escaped_timestamp = timestamp
	
	escaped_timestamp = escape(escaped_timestamp)

	# Combine everything with the delimiter and return the packed Line
	packed_values = delimiter.join(escaped_values)
	packed_line = f"{escaped_name} [{packed_values}] {escaped_timestamp}\n"
	return packed_line

def unpack_line(line: str) -> Tuple[str, List[str], Optional[str]]:
	delimiter="|"
	start_bracket = line.find("[")
	end_bracket = line.find("]")

	if start_bracket == -1 or end_bracket == -1:

		raise ValueError(f"Invalid line format: [{line}]")

	# Extract name, values, and timestamp
	name = unescape(line[:start_bracket].strip())
	values_str = line[start_bracket + 1:end_bracket]
	values = [unescape(value) for value in values_str.split(delimiter)]
	if end_bracket + 1 < len(line):
		try:
			timestamp = datetime.strptime(unescape(line[end_bracket + 1:].strip()),TIME_FORMAT)
		except ValueError as e:
			timestamp = None
	else:
		timestamp = None

	return name, values, timestamp



def reverse_lines(filename):
	if os.path.exists(filename):
		with open(filename, 'r') as file:
			file.seek(0, 2)  # Move the file pointer to the end of the file
			file_size = file.tell()

			# Start reading lines from the end of the file
			while file_size > 0:
				file_size -= 1
				file.seek(file_size)
				char = file.read(1)
				
				# Check for newline character
				if char == '\n':
					line = file.readline().rstrip('\n')
					yield line

			# Read the first line (if any) since the loop doesn't cover the entire file
			file.seek(0)
			line = file.readline().rstrip('\n')
			yield line



def append_to_file(filename: str, data: str) -> Tuple[int, int]:
	"""
	Append a compressed string to a file and get the start position and number of bytes to read to get it back.

	Args:
		filename (str): The name of the file.
		data (str): The string to be appended to the file.

	Returns:
		Tuple[int, int]: The start position and number of bytes written.
	"""
	with open(filename, 'ab') as file:
		# Create a BytesIO buffer for compressing the data
		buffer = io.BytesIO()
		with gzip.GzipFile(fileobj=buffer, mode='wb') as gzip_file:
			gzip_file.write(data.encode('utf-8'))

		# Get the start position before writing
		start_position = file.tell()

		# Write the compressed data to the file
		buffer.seek(0)
		file.write(buffer.read())

		# Get the end position after writing
		end_position = file.tell()

	return start_position, end_position - start_position

def read_from_file(filename: str, position: Tuple[int, int]) -> str:
	"""
	Read a compressed chunk from a file starting at position[0] and spanning position[1] bytes.

	Args:
		filename (str): The name of the file.
		position (Tuple[int, int]): A tuple representing the start position and number of bytes to read.

	Returns:
		str: The decompressed read chunk of data.
	"""
	with open(filename, 'rb') as file:
		# Move to the specified start position
		file.seek(position[0])

		# Read the specified number of bytes into a BytesIO buffer
		buffer = io.BytesIO(file.read(position[1]))

		# Decompress the data from the buffer
		with gzip.GzipFile(fileobj=buffer, mode='rb') as gzip_file:
			data = gzip_file.read()

	return data.decode('utf-8')  # Decode the bytes to a string



class Tclish_DB_disk(Tclish_DB):
	"""docstring for db_disk"""
	def __init__(self, fname):
		super(Tclish_DB_disk, self).__init__()
		self.fname = fname
		self.state = "initialized"
		if not os.path.exists(self.snapshot_file()):
			with open(self.snapshot_file(),"w") as f:
				f.write("")
		if not os.path.exists(self.steps_file()):
			with open(self.steps_file(),"w") as f:
				f.write("")
		#db.load()#maybe add in future

	def snapshot_file(self):
		return self.fname+".snapshots"
	def steps_file(self):
		return self.fname+".steps"
	def tojson(self):
		return {
			"db" : self.pack(self.db),
			"fname" : self.fname,
		}
	def fromjson(self,items):
		if "db" in items:
			self.unpack(self.db,items["db"])
		if "fname" in items:
			self.fname=items["fname"]

	def set(self, keys, value):
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("set",keys + [value]))
		return super(Tclish_DB_disk, self).set(keys,value)

	def unset(self, keys):
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("unset",keys))
		return super(Tclish_DB_disk, self).unset(keys)

	def prune(self, keys):
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("prune",keys))
		return super(Tclish_DB_disk, self).prune(keys)

	def create_snapshot(self,name=None):
		if name is None:
			name = self.state
		s=json.dumps(self.tojson())
		pos,size=append_to_file(self.snapshot_file(),s)
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("snapshot",[str(pos),str(size),name]))

	def load_snapshot(self,pos,size,name="unnamed"):
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("snapshot",[str(pos),str(size),name]))
		data=read_from_file(self.snapshot_file(),(int(pos),int(size)))
		self.db={}
		self.fromjson(json.loads(data))

	def load_snapshot_by_name(self,snapshot_name):
		for line in reverse_lines(self.steps_file()):
			if line.strip()=="":continue
			name,args,time=unpack_line(line)
			if name=="snapshot":
				if len(args)>2 and args[2]==snapshot_name:
					self.load_snapshot(args[0],args[1],snapshot_name)
					return True
		#raise Exception(f"no snapshot of name {name} found")
		return False

	def reload_latest_snapshot(self):
		snapshot_dirs=None
		for line in reverse_lines(self.steps_file()):
			if line.strip()=="":continue
			name,args,time=unpack_line(line)
			if name=="snapshot":
				snapshot_dirs=args
				self.load_snapshot(args[0],args[1])
				break
		if snapshot_dirs is None:
			# no snapshot found
			return False
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("snapshot",snapshot_dirs))
		return True
	def load(self):
		to_replay=[]
		snapshot_dirs=None
		for line in reverse_lines(self.steps_file()):
			if line.strip()=="":continue
			name,args,time=unpack_line(line)
			if name=="snapshot": #differentiate create_snapshot and load_snapshot in the future
				snapshot_dirs=args
				self.load_snapshot(args[0],args[1])
				break
			else:
				to_replay.append((name,args))
		if snapshot_dirs is None:
			# no snapshot found
			return
		with open(self.steps_file(),"a") as f:
			f.write(pack_line("snapshot",snapshot_dirs))
		return self.replay_log(to_replay[::-1])

	def replay_log(self,to_replay):
		for name,args in to_replay:
			if name=="set":
				self.set(args[:-1],args[-1])
			elif name=="unset":
				self.unset(args)
			elif name=="prune":
				self.prune(args)
			elif name=="snapshot":
				self.load_snapshot(args[0],args[1])

	def revert(self, *args,**kvargs):
		target_time = datetime.now() - timedelta(*args,**kvargs)
		gathered_lines = []
		reached_target_time = False

		for line in reverse_lines(self.steps_file()):
			if line.strip() == "": 
				continue

			name, args, log_time = unpack_line(line)

			if (log_time is not None) and log_time <= target_time:
				reached_target_time = True

			if reached_target_time:
				gathered_lines.append((name,args))

			if name == "snapshot" and reached_target_time:
				snapshot_pos, snapshot_size = args[0], args[1]
				self.load_snapshot(snapshot_pos, snapshot_size)
				return self.replay_log(gathered_lines[::-1])

		# If no snapshot found, reset and replay gathered lines
		self.db={}
		return self.replay_log(gathered_lines[::-1])

	def list_snapshots(self,count=10):
		snapshots={}
		current_count=0
		for line in reverse_lines(self.steps_file()):
			if line.strip()=="":continue
			name,args,time=unpack_line(line)
			if name=="snapshot":
				label=f"{args[0]}:{args[1]}"
				if len(args)>2 and args[2] != None and args[2] != "unnamed":
					label=args[2]

				if label not in snapshots:
					snapshots[label]=(time,args)
					current_count+=1
				if current_count>=count:
					break
		return snapshots
				
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

			elif command == "create-snapshot":
				if len(args)<2:
					self.create_snapshot()
				else:
					self.create_snapshot(args[1])
				return vm.ok("")

			elif command == "load-snapshot":
				success=False
				if len(args)<2:
					success=self.reload_latest_snapshot()
				else:
					success=self.load_snapshot_by_name(args[1])
				if success:
					return vm.ok()
				else:
					return vm.error(task,f"failed to load snapshot {args[1]}","db load-snapshot")

			elif command == "list-snapshots":
				if len(args)<2:
					l=self.list_snapshots()
				else:
					num=vm.to_number(args[1])
					if num is None:
						return vm.error(task,f"{args[1]} is not a valid numerical limit","db list-snapshots")
					l=self.list_snapshots(num)
				ok,res=vm.pack_strings(list(l.keys()))
				return vm.ok(res)
			
			elif command == "revert":
				pos=0
				def consume():
					nonlocal pos
					pos+=1
					if len(args)>pos:
						s=args[pos]
						return s
					return ""
				def done():
					return pos>=len(args)

				days=0
				seconds=0
				minutes=0
				hours=0
				weeks=0

				while not done():
					match consume().lower():
						case "seconds" | "second":
							num_str=consume()
							num=vm.to_number(num_str)
							if num is None:
								return vm.error(task,f"number {num_str} (pos {pos}) is not a valid number of seconds","db revert")
							seconds+=num

						case "minutes" | "minute":
							num_str=consume()
							num=vm.to_number(num_str)
							if num is None:
								return vm.error(task,f"number {num_str} (pos {pos}) is not a valid number of minutes","db revert")
							minutes+=num

						case "hours" | "hour":
							num_str=consume()
							num=vm.to_number(num_str)
							if num is None:
								return vm.error(task,f"number {num_str} (pos {pos}) is not a valid number of hours","db revert")
							hours+=num
						case "days" | "day":
							num_str=consume()
							num=vm.to_number(num_str)
							if num is None:
								return vm.error(task,f"number {num_str} (pos {pos}) is not a valid number of days","db revert")
							days+=num

						case "weeks" | "week":
							num_str=consume()
							num=vm.to_number(num_str)
							if num is None:
								return vm.error(task,f"number {num_str} (pos {pos}) is not a valid number of weeks","db revert")
							weeks+=num
						case X:
							return vm.error(task,f"duration {X} is not a valid duration","db revert")
				ok=self.revert(
					days=days,
					seconds=seconds,
					minutes=minutes,
					hours=hours,
					weeks=weeks)
				if ok:
					return vm.ok()
				else:
					return vm.error(task,"failed to revert the db","db revert")

			else:
				return vm.error(task,f"Error: Unknown 'db' command '{command}'.","db")
		helpstr="""usage:
(1)  db get <fields...>
(2)  db set <fields...> <value>
(3)  db unset <fields...>
(4)  db has <fields...>
(5)  db list <fields...>
(6)  db prune <fields...>
(7)  db show <fields...>
(8)  db tree <fields...>
(9)  db create-snapshot <name>
(10)  db load-snapshot [<name>]
(11) db list-snapshots [<limit>]
(12) db revert [minutes <minutes>] [hours <hours>] [days <days>]

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

(7) db show prettyprints the specified subtree
   Example:

(8) db show prettyprints the specified subtree
   Example:

(9) db create-snapshot <name>
   create a snapshot of the current state of the database

(10)  db load-snapshot [<name>]
   load the most recent snapshot with the specified name
   if no name is specified, loads the most recent snapshot

(11) db list-snapshots [<limit>]
   returns a list of the <limit> most recent snapshots
   defaults to 10 if no limit is given

(12) db revert [minutes <minutes>] [hours <hours>] [days <days>]
   reverts the database the specified amount of time
   Examples:
   (11.1)  db revert minutes 10
     reverts 10 minutes
   (11.2)  db revert weeks 1 days 1
     reverts the database one week and one day
   (11.3)  db revert seconds 1 seconds 1
     reverts the database 2 seconds because it adds up all the specified durations

"""
		return "db",vm_db_command,helpstr

