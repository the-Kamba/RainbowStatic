The `Tclish_DB_disk` class is an extension of the base `Tclish_DB` class, introducing persistent disk storage capabilities and additional features for managing snapshots and reverting to previous states. This class is designed for scenarios where it's crucial to persistently store the state of a hierarchical key-value database on disk, allowing for recovery to specific points in time and facilitating long-term data management.

### Initialization:

```python
db = Tclish_DB_disk("my_database.db")
```

- **fname:** The `fname` parameter specifies the file name for the database storage.

### Key Features:

#### 1. **Snapshot Management:**

   - **Create Snapshot:**
     ```python
     db.create_snapshot("snapshot_name")
     ```
     Creates a snapshot of the current state of the database. If no name is provided, the snapshot is named based on the current state.

   - **Load Snapshot:**
     ```python
     db.load_snapshot(pos, size)
     ```
     Loads a snapshot from a specific position (`pos`) and size (`size`) in the file.

   - **Load Snapshot by Name:**
     ```python
     db.load_snapshot_by_name("snapshot_name")
     ```
     Loads the most recent snapshot with the specified name. Returns `True` if successful, `False` otherwise.

   - **Reload Latest Snapshot:**
     ```python
     db.reload_latest_snapshot()
     ```
     Reloads the most recent snapshot. Returns `True` if successful, `False` if no snapshot is found.

#### 2. **Reverting to Previous States:**

   - **Revert Operation:**
     ```python
     db.revert(days=1, hours=2)
     ```
     Reverts the database to a previous state based on the specified time duration. Supports various time units such as days, hours, minutes, etc.

#### 3. **Steps and Snapshots Files:**

   - **Steps File:**
     ```python
     db.steps_file()
     ```
     Returns the file name used for recording steps in the database.

   - **Snapshot File:**
     ```python
     db.snapshot_file()
     ```
     Returns the file name used for storing snapshots of the database.

#### 4. **List Snapshots:**

   - **List Snapshots:**
     ```python
     db.list_snapshots(count=10)
     ```
     Returns information about the most recent snapshots, including snapshot labels and timestamps.

### Usage:

1. **Basic Database Operations:**
   - Use `set`, `unset`, `prune`, `get`, etc., to manipulate the database as per the base `Tclish_DB` class.

2. **Snapshot and Revert Operations:**
   - Create snapshots using `create_snapshot`.
   - Load snapshots using `load_snapshot` or `load_snapshot_by_name`.
   - Revert to previous states using `revert`.

3. **Persistent Storage:**
   - The database state and snapshots are stored on disk in the specified file.

This class is suitable for scenarios where data persistence, snapshot management, and the ability to revert to specific points in time are crucial, such as in version-controlled databases or systems requiring periodic state capture.