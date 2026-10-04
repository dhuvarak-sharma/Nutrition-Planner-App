# Nutrition Planner

A Python desktop application for browsing dishes, viewing nutritional information, filtering recipes, and saving favourites. The application uses **Tkinter** for the interface and **MySQL** for persistent storage.

## Features

- Browse all available dishes
- Search dishes by name or cuisine
- Open a detailed dish view with ingredients and nutritional information
- Filter dishes by ingredients, nutrition, cuisine, and preparation time
- Add and remove favourites
- Persist favourites between sessions
- Load dish images with Pillow when available, with a built-in placeholder when an image cannot be loaded
- Use asynchronous image loading so image processing does not intentionally block the main interface

## Tech Stack

- **Python** — application logic
- **Tkinter** — desktop GUI
- **MySQL** — persistent database
- **mysql-connector-python** — Python/MySQL connection
- **Pillow** — dish image handling
- **threading** — background image loading

## Project Structure

```text
nutrition-planner-app/
├── database_mysql.py       # MySQL database setup and data access
├── dish_data.py            # Initial dish data
├── nutrition_planner.py    # Tkinter GUI and application logic
├── food_images/            # Local dish images referenced by dish_data.py
├── assets/
│   └── screenshots/        # Screenshots can be added here
├── requirements.txt
├── .gitignore
└── README.md
```

The application currently contains **20 seed dishes** in `dish_data.py`.

## How It Works

The project separates the initial data, database layer, and graphical interface:

```text
                    ┌─────────────────┐
                    │   dish_data.py  │
                    │  Seed dish data │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ database_mysql  │
                    │ .py             │
                    │                 │
                    │ MySQL database  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ nutrition_      │
                    │ planner.py      │
                    │                 │
                    │ Tkinter GUI     │
                    └─────────────────┘
```

On startup, the application initializes the `nutrition_planner` MySQL database and creates the `dishes` and `favourites` tables if they do not already exist. The seed data is then added when the dishes table is empty.

The GUI is organized into separate screens for the home menu, all dishes, dish details, filtering, filtered results, and favourites. Favourites are stored in MySQL so they remain available after the application is closed and reopened.

## Database

The application creates a MySQL database named:

```text
nutrition_planner
```

It uses two tables:

### `dishes`

Stores the dish ID, name, cuisine, preparation time, description, ingredients, nutrition text, image path, and tags.

### `favourites`

Stores the IDs of dishes marked as favourites. Each favourite references a dish through a foreign key.

The database layer also converts tags between the Python list representation and the comma-separated form stored in MySQL.

## Setup

### 1. Install Python

Use a recent Python 3 installation. Tkinter is required for the desktop interface.

### 2. Install MySQL

Make sure a local MySQL server is installed and running. The application expects a MySQL account with permission to create/use the `nutrition_planner` database.

### 3. Install Python dependencies

From the project directory:

```bash
pip install -r requirements.txt
```

### 4. Configure the MySQL password

Open `database_mysql.py` and update:

```python
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password_here"
}
```

Replace `your_mysql_password_here` with the password for your local MySQL account.

**Do not commit a real password to a public GitHub repository.**

### 5. Add dish images

`dish_data.py` contains local paths such as:

```text
food_images/paneer_butter_masala.jpg
```

Place the corresponding image files inside the `food_images/` directory. If an image is missing or cannot be loaded, the application can fall back to its generated placeholder when Pillow is available.

### 6. Run the application

```bash
python nutrition_planner.py
```

The first run initializes the database and inserts the seed dishes. Later runs reuse the existing database and saved favourites.

## Application Screenshots

Screenshots are intentionally left as placeholders so that actual screenshots of the application can be added later.

### Home Screen

> **Screenshot placeholder:** Add a screenshot of the Nutrition Planner home screen here.

```text
assets/screenshots/home-screen.png
```

![Home Screen](assets/screenshots/home-screen.png)

### All Dishes / Search

> **Screenshot placeholder:** Add a screenshot showing the All Dishes screen and search functionality here.

```text
assets/screenshots/all-dishes.png
```

![All Dishes](assets/screenshots/all-dishes.png)

### Dish Details

> **Screenshot placeholder:** Add a screenshot of a dish's detailed information page here.

```text
assets/screenshots/dish-details.png
```

![Dish Details](assets/screenshots/dish-details.png)

### Filter Dishes

> **Screenshot placeholder:** Add a screenshot showing the filtering interface and/or filtered results here.

```text
assets/screenshots/filter-dishes.png
```

![Filter Dishes](assets/screenshots/filter-dishes.png)

### Favourites

> **Screenshot placeholder:** Add a screenshot of the Favourites screen here.

```text
assets/screenshots/favourites.png
```

![Favourites](assets/screenshots/favourites.png)

## Notes and Limitations

- Nutritional information is stored as text in the seed data. Although the detail screen labels it as **per 100 gm**, the current application does not dynamically calculate nutritional values from a serving size.
- Search in the All Dishes screen is based on **dish name or cuisine**; it does not search every stored field.
- The filter system works by matching the entered criteria against the stored ingredient, nutrition, cuisine, and time text rather than calculating nutritional values.
- Dish images are local files referenced by path, so they need to be present on the machine running the application.
- The application is a desktop prototype and currently has no user authentication or separate user accounts.

## Future Improvements

- **Serving-size nutrition calculation:** Add structured nutritional values so the application can calculate calories and nutrients for a user-selected quantity instead of displaying stored text.
- **Improved search and filtering:** Expand search to ingredients, tags, descriptions, and more structured nutrition/time filters so users can find dishes more precisely.
- **Image management:** Store or manage dish images more reliably so the application does not depend on manually maintained local image paths.
- **User accounts:** Add authentication and user-specific favourites so different users can maintain separate saved dishes.
- **Recipe management:** Allow authorized users to add, edit, and remove dishes through the application instead of managing seed data manually.
- **Interface improvements:** Refine navigation and screen layout to make the application easier to use as the number of dishes and features grows.

## License

This project is intended as a student software project. Add a license here if you decide to publish the repository under a specific open-source license.
