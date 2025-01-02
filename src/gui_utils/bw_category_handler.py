import json
import aiohttp
from datetime import datetime
import pymssql
from typing import List, Tuple, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from src.sa_secrets.keys import BW_API_KEY, PROJECT_ID
from src.sa_secrets.azure import SERVER, DATABASE, UID, PWD

class BWCategoryHandler:
    def __init__(self, log_message):
        self.log_message = log_message
        print("Initializing BWCategoryHandler...")
        self.log_message("Initializing database connection...")
        self.server = SERVER
        self.database = DATABASE
        self.username = UID
        self.password = PWD
        # Initialize the database table
        self.init_db()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def get_connection(self):
        try:
            return pymssql.connect(
                server=self.server,
                database=self.database,
                user=self.username,
                password=self.password
            )
        except pymssql.OperationalError as e:
            if e.args[0] == 40613:  # Transient error code
                print("Database temporarily unavailable, retrying...")
                raise  # Retry will catch this
            raise  # Non-transient error, don't retry
    
    def init_db(self):
        print("Initializing database tables...")
        self.log_message("Initializing database tables...")
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # First check if the table exists
                    cursor.execute("""
                        IF NOT EXISTS (
                            SELECT * 
                            FROM INFORMATION_SCHEMA.TABLES 
                            WHERE TABLE_SCHEMA = 'dbo' 
                            AND TABLE_NAME = 'bw_categories'
                        )
                        BEGIN
                            CREATE TABLE bw_categories (
                                parent_id INT PRIMARY KEY,
                                parent_name NVARCHAR(255),
                                children_json NVARCHAR(MAX),
                                last_updated DATETIME
                            )
                        END
                    """)
                    conn.commit()
            print("Database initialization complete")
            self.log_message("Database initialization complete")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise
    
    async def fetch_categories(self) -> Dict:
        print("Fetching categories from Brandwatch API...")
        url = f"https://api.brandwatch.com/projects/{PROJECT_ID}/categories"
        headers = {
            "authorization": f"bearer {BW_API_KEY}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print("Successfully fetched categories")
                    data = await response.json()
                    await self.save_categories(data)
                    return data
                else:
                    print(f"Error fetching categories: {response.status}")
                    raise Exception(f"Failed to fetch categories: {response.status}")
    
    async def save_categories(self, data: Dict):
        print(f"Saving {len(data['results'])} categories to database...")
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Clear existing data
                cursor.execute("DELETE FROM bw_categories")
                
                # Insert new data
                for category in data['results']:
                    cursor.execute("""
                        INSERT INTO bw_categories 
                        (parent_id, parent_name, children_json, last_updated) 
                        VALUES (%s, %s, %s, %s)
                    """, 
                    (category['id'], 
                     category['name'], 
                     json.dumps(category['children']), 
                     datetime.now())
                    )
                conn.commit()
        print("Categories saved successfully")
    
    def get_all_parents(self) -> List[Tuple[int, str]]:
        print("Retrieving all parent categories...")
        self.log_message("Retrieving all parent categories...")
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT parent_id, parent_name FROM bw_categories")
                return cursor.fetchall()
    
    def get_children(self, parent_id: int) -> List[Dict]:
        print(f"Retrieving children for parent ID: {parent_id}")
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT children_json FROM bw_categories WHERE parent_id = %s", 
                    (parent_id,)
                )
                result = cursor.fetchone()
                return json.loads(result[0]) if result else []
    
    def get_last_update(self) -> datetime:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT TOP 1 last_updated FROM bw_categories")
                result = cursor.fetchone()
                return result[0] if result else None