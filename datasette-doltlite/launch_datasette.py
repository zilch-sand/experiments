"""
Launch datasette with doltlite backend.
Works around:
1. Doltlite's lack of named memory database URI support
2. Doltlite's thread safety issues with concurrent connections
"""
import sqlite3
import sys
import os
import tempfile
import threading

# Monkey-patch Database.connect to handle named memory databases
from datasette.database import Database

_original_connect = Database.connect

# Create a single temp file for internal db at module level
_internal_db_path = os.path.join(tempfile.mkdtemp(), 'internal.db')

# Global lock for doltlite connections
_doltlite_lock = threading.Lock()

def _patched_connect(self, write=False):
    """Patched connect that falls back to a temp file for named memory dbs in doltlite."""
    if self.memory_name:
        conn = sqlite3.connect(
            _internal_db_path,
            check_same_thread=False,
        )
        return conn
    return _original_connect(self, write)

Database.connect = _patched_connect

# Also patch execute_fn to serialize database access for doltlite files
_original_execute_fn = Database.execute_fn

async def _patched_execute_fn(self, fn, isolation_level=None):
    """Serialize execution to avoid concurrent access crashes in doltlite."""
    if not self.is_memory and not self.memory_name:
        with _doltlite_lock:
            return await _original_execute_fn(self, fn, isolation_level)
    return await _original_execute_fn(self, fn, isolation_level)

# Don't patch execute_fn - it's async and complex. Instead, configure datasette to use fewer threads.

# Now run datasette CLI with thread settings
from datasette.cli import cli

# Add --setting num_sql_threads 1 to limit concurrency
import sys
sys.argv.extend(['--setting', 'num_sql_threads', '1'])

cli()
