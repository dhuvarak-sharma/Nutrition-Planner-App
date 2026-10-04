import mysql.connector
from dish_data import SEED_DISHES


# ---------------------------------------------------------
# MySQL Configuration
# ---------------------------------------------------------

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "your_mysql_username_here",
    "password": "your_mysql_password_here"
}

DB_NAME = "nutrition_planner"


# ---------------------------------------------------------
# Initialize Database and Tables
# ---------------------------------------------------------

def init_db():
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host=MYSQL_CONFIG["host"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"]
    )

    cur = conn.cursor()

    # Create database if it does not already exist
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"
    )

    cur.close()
    conn.close()

    # Connect directly to the nutrition_planner database
    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    # Create dishes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            cuisine VARCHAR(255),
            time VARCHAR(255),
            description TEXT,
            ingredients TEXT,
            nutrition TEXT,
            image VARCHAR(255),
            tags VARCHAR(255)
        )
    """)

    # Create favourites table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favourites (
            dish_id INT PRIMARY KEY,
            FOREIGN KEY (dish_id)
                REFERENCES dishes(id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()

    cur.close()
    conn.close()


# ---------------------------------------------------------
# Add Missing Seed Dishes
# ---------------------------------------------------------

def seed_if_empty():
    """
    Adds dishes from SEED_DISHES that are not already
    present in the database.

    Unlike the original version, this does NOT require
    the dishes table to be completely empty.
    """

    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    for dish in SEED_DISHES:

        # Check whether this dish already exists
        cur.execute(
            "SELECT id FROM dishes WHERE id = %s",
            (dish["id"],)
        )

        existing_dish = cur.fetchone()

        # Only insert if the dish does not already exist
        if existing_dish is None:

            cur.execute("""
                INSERT INTO dishes
                (
                    id,
                    name,
                    cuisine,
                    time,
                    description,
                    ingredients,
                    nutrition,
                    image,
                    tags
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dish["id"],
                dish["name"],
                dish["cuisine"],
                dish["time"],
                dish["description"],
                dish["ingredients"],
                dish["nutrition"],
                dish["image"],
                ",".join(dish["tags"])
            ))

    conn.commit()

    cur.close()
    conn.close()


# ---------------------------------------------------------
# Convert Database Row into Python Dictionary
# ---------------------------------------------------------

def _row_to_dish(row):

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "cuisine": row[2],
        "time": row[3],
        "description": row[4],
        "ingredients": row[5],
        "nutrition": row[6],
        "image": row[7],
        "tags": row[8].split(",") if row[8] else []
    }


# ---------------------------------------------------------
# Columns Used When Selecting Dishes
# ---------------------------------------------------------

_SELECT_COLUMNS = """
    id,
    name,
    cuisine,
    time,
    description,
    ingredients,
    nutrition,
    image,
    tags
"""


# ---------------------------------------------------------
# Get All Dishes
# ---------------------------------------------------------

def get_all_dishes():

    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {_SELECT_COLUMNS}
        FROM dishes
        ORDER BY id
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        _row_to_dish(row)
        for row in rows
    ]


# ---------------------------------------------------------
# Get One Dish by ID
# ---------------------------------------------------------

def get_dish_by_id(dish_id):

    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {_SELECT_COLUMNS}
        FROM dishes
        WHERE id = %s
        """,
        (dish_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return _row_to_dish(row)


# ---------------------------------------------------------
# Load Favourite Dishes
# ---------------------------------------------------------

def load_favourites():

    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    cur.execute(
        "SELECT dish_id FROM favourites"
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Convert list of tuples into a set of IDs
    return {
        row[0]
        for row in rows
    }


# ---------------------------------------------------------
# Save Favourite Dishes
# ---------------------------------------------------------

def save_favourites(favs):

    conn = mysql.connector.connect(
        database=DB_NAME,
        **MYSQL_CONFIG
    )

    cur = conn.cursor()

    # Remove existing favourites
    cur.execute(
        "DELETE FROM favourites"
    )

    # Insert current favourites
    if favs:
        cur.executemany(
            """
            INSERT INTO favourites (dish_id)
            VALUES (%s)
            """,
            [
                (dish_id,)
                for dish_id in favs
            ]
        )

    conn.commit()

    cur.close()
    conn.close()
