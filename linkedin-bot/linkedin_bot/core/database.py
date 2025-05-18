"""
Core database module that provides a unified interface for database operations.
"""
import os
import sqlite3
import threading
import time
from typing import List, Dict, Any, Tuple, Optional, Union

class Database:
    """
    Database class that handles connections and operations with SQLite.
    Uses thread-local storage for connections to ensure thread safety.
    """
    _local = threading.local()
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default path.
        """
        if db_path is None:
            # Default to user's home directory for desktop app
            home_dir = os.path.expanduser("~")
            db_dir = os.path.join(home_dir, ".linkedin_bot")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "linkedin_bot.db")
            
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local database connection.
        
        Returns:
            SQLite connection object
        """
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Configure connection to return rows as dictionaries
            self._local.connection.row_factory = lambda c, r: {
                col[0]: r[idx] for idx, col in enumerate(c.description)
            }
        
        return self._local.connection
    
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Setup tables with all necessary columns from the beginning
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_text TEXT NOT NULL,
            schedule_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            needs_review INTEGER DEFAULT 0,
            reviewed INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_repository (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_text TEXT NOT NULL,
            category TEXT,
            is_used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            posts_per_day INTEGER NOT NULL,
            duration_days INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            requires_review INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE
        )
        ''')
        
        # Add settings table for application configuration
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Add user credentials table (for desktop app)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(service, key)
        )
        ''')
        
        conn.commit()
    
    def execute(self, query: str, params: Tuple = (), max_retries: int = 5) -> sqlite3.Cursor:
        """
        Execute a query with retry logic for handling database locks.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            max_retries: Maximum number of retries for locked database
            
        Returns:
            Cursor object
        """
        conn = self._get_connection()
        retries = 0
        
        while retries < max_retries:
            try:
                return conn.execute(query, params)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retries < max_retries - 1:
                    retries += 1
                    # Exponential backoff
                    sleep_time = 0.1 * (2 ** retries)
                    time.sleep(sleep_time)
                else:
                    raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """
        Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Cursor object
        """
        conn = self._get_connection()
        return conn.executemany(query, params_list)
    
    def commit(self):
        """Commit the current transaction."""
        if hasattr(self._local, 'connection'):
            self._local.connection.commit()
    
    def rollback(self):
        """Rollback the current transaction."""
        if hasattr(self._local, 'connection'):
            self._local.connection.rollback()
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a row into the specified table.
        
        Args:
            table: Table name
            data: Dictionary of column:value pairs
            
        Returns:
            ID of the inserted row
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.execute(query, values)
        self.commit()
        
        return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Tuple) -> int:
        """
        Update rows in the specified table.
        
        Args:
            table: Table name
            data: Dictionary of column:value pairs to update
            where: WHERE clause
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected
        """
        set_clause = ', '.join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + where_params
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cursor = self.execute(query, values)
        self.commit()
        
        return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple) -> int:
        """
        Delete rows from the specified table.
        
        Args:
            table: Table name
            where: WHERE clause
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected
        """
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(query, where_params)
        self.commit()
        
        return cursor.rowcount
    
    def select(self, table: str, columns: str = "*", 
               where: str = None, where_params: Tuple = (), 
               order_by: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Select rows from the specified table.
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            where: WHERE clause (default: None)
            where_params: Parameters for WHERE clause (default: ())
            order_by: ORDER BY clause (default: None)
            limit: LIMIT clause (default: None)
            
        Returns:
            List of dictionaries with selected rows
        """
        query = f"SELECT {columns} FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.execute(query, where_params)
        return cursor.fetchall()
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """
        Get a credential value from the credentials table.
        
        Args:
            service: Service name (e.g., 'linkedin', 'openai')
            key: Credential key (e.g., 'access_token', 'api_key')
            
        Returns:
            Credential value or None if not found
        """
        query = "SELECT value FROM credentials WHERE service = ? AND key = ?"
        cursor = self.execute(query, (service, key))
        result = cursor.fetchone()
        
        return result['value'] if result else None
    
    def set_credential(self, service: str, key: str, value: str) -> int:
        """
        Store or update a credential in the credentials table.
        
        Args:
            service: Service name (e.g., 'linkedin', 'openai')
            key: Credential key (e.g., 'access_token', 'api_key')
            value: Credential value
            
        Returns:
            Row ID
        """
        # Try to update first
        query = """
        INSERT INTO credentials (service, key, value) VALUES (?, ?, ?)
        ON CONFLICT(service, key) DO UPDATE SET value = ?, created_at = CURRENT_TIMESTAMP
        """
        cursor = self.execute(query, (service, key, value, value))
        self.commit()
        
        return cursor.lastrowid
    
    def get_setting(self, key: str, default: Any = None) -> Optional[str]:
        """
        Get a setting value from the settings table.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value or default
        """
        query = "SELECT value FROM settings WHERE key = ?"
        cursor = self.execute(query, (key,))
        result = cursor.fetchone()
        
        return result['value'] if result else default
    
    def set_setting(self, key: str, value: str) -> None:
        """
        Store or update a setting in the settings table.
        
        Args:
            key: Setting key
            value: Setting value
        """
        query = """
        INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
        """
        self.execute(query, (key, value, value))
        self.commit()


# Create a global instance for convenience
db = Database()