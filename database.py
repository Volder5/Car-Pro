import sqlite3

class Database:
    def __init__(self, db_path="carpro.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                sites TEXT,
                regions TEXT,
                make TEXT,
                budget INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_listings (
                link TEXT PRIMARY KEY
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS average_prices (
                model TEXT,
                year INTEGER,
                price INTEGER,
                updated_at TEXT,
                PRIMARY KEY (model, year)
            )
        """)
        self.conn.commit()

    def add_user(self, user_id):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    def toggle_site(self, user_id, site):
        self.cursor.execute("SELECT sites FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        sites = result[0].split(",") if result and result[0] else []
        if site in sites:
            sites.remove(site)
        else:
            sites.append(site)
        new_sites = ",".join(sites) if sites else ""
        self.cursor.execute("UPDATE users SET sites = ? WHERE user_id = ?", (new_sites, user_id))
        self.conn.commit()

    def toggle_region(self, user_id, region):
        self.cursor.execute("SELECT regions FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        regions = result[0].split(",") if result and result[0] else []
        if region in regions:
            regions.remove(region)
        else:
            regions.append(region)
        new_regions = ",".join(regions) if regions else ""
        self.cursor.execute("UPDATE users SET regions = ? WHERE user_id = ?", (new_regions, user_id))
        self.conn.commit()

    def toggle_make(self, user_id, make):
        self.cursor.execute("SELECT make FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        makes = result[0].split(",") if result and result[0] else []
        make = make.lower()  
        if make in makes:
            makes.remove(make)
        else:
            makes.append(make)
        new_makes = ",".join(makes) if makes else ""
        self.cursor.execute("UPDATE users SET make = ? WHERE user_id = ?", (new_makes, user_id))
        self.conn.commit()

    def get_user_makes(self, user_id):
        self.cursor.execute("SELECT make FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0].split(",") if result and result[0] else []

    def update_user_budget(self, user_id, budget):
        self.cursor.execute("UPDATE users SET budget = ? WHERE user_id = ?", (budget, user_id))
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute("SELECT user_id, sites, regions, make, budget FROM users")
        return self.cursor.fetchall()

    def reset_sent_listings(self):
        self.cursor.execute("DELETE FROM sent_listings")
        self.conn.commit()

    def is_listing_sent(self, link):
        self.cursor.execute("SELECT 1 FROM sent_listings WHERE link = ?", (link,))
        return bool(self.cursor.fetchone())

    def add_sent_listing(self, link):
        self.cursor.execute("INSERT OR IGNORE INTO sent_listings (link) VALUES (?)", (link,))
        self.conn.commit()

    def get_average_price(self, model, year):
        self.cursor.execute("SELECT price, updated_at FROM average_prices WHERE model = ? AND year = ?", (model, year))
        result = self.cursor.fetchone()
        return result if result else (None, None)

    def get_user_sites(self, user_id):
        self.cursor.execute("SELECT sites FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0].split(",") if result and result[0] else []
    
    def get_user_regions(self, user_id):
        self.cursor.execute("SELECT regions FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0].split(",") if result and result[0] else []
    
    def update_average_price(self, model, year, price):
        from datetime import datetime
        updated_at = datetime.now().isoformat()
        self.cursor.execute("""
            INSERT OR REPLACE INTO average_prices (model, year, price, updated_at)
            VALUES (?, ?, ?, ?)
        """, (model, year, price, updated_at))
        self.conn.commit()

    def close(self):
        self.conn.close()