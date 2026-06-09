# 📚 Bibliotheca — Library Management System

A full-stack Library Management System with a dark academia aesthetic.
Built with **Flask** (Python) + **SQLite** backend and a custom HTML/CSS/JS frontend.

---

## 📁 Project Structure

```
library-management-system/
├── app.py                  # Flask backend + SQLite database logic
├── requirements.txt        # Python dependencies
├── library.db              # SQLite database (auto-created on first run)
├── templates/
│   └── index.html          # Main frontend HTML
└── static/
    ├── css/
    │   └── style.css       # All styles (dark academia theme)
    └── js/
        └── main.js         # All frontend JavaScript
```

---

## 🚀 Setup & Run

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

The SQLite database (`library.db`) is **auto-created** with sample data on first run.

---

## ✨ Features

| Module        | What it does |
|---------------|-------------|
| **Dashboard** | Live stats (books, members, active loans, overdue) + recent loan activity |
| **Books**     | Add, edit, delete books; search by title/author/genre; shows availability |
| **Members**   | Register and manage library members |
| **Loans**     | Full loan history with status filters (Active / Returned / Overdue) |
| **Issue Book**| Issue any available book to a member with configurable due date |

---

## 🗄️ Database Schema

### `books`
| Column        | Type    | Description               |
|---------------|---------|---------------------------|
| id            | INTEGER | Primary key               |
| title         | TEXT    | Book title                |
| author        | TEXT    | Author name               |
| isbn          | TEXT    | ISBN (unique)             |
| genre         | TEXT    | Genre category            |
| total_copies  | INTEGER | Total copies owned        |
| created_at    | TEXT    | Auto timestamp            |

### `members`
| Column    | Type | Description     |
|-----------|------|-----------------|
| id        | INTEGER | Primary key  |
| name      | TEXT    | Full name    |
| email     | TEXT    | Email (unique) |
| phone     | TEXT    | Phone number |
| joined_at | TEXT    | Auto timestamp |

### `loans`
| Column      | Type    | Description                          |
|-------------|---------|--------------------------------------|
| id          | INTEGER | Primary key                          |
| book_id     | INTEGER | FK → books.id                        |
| member_id   | INTEGER | FK → members.id                      |
| loaned_at   | TEXT    | When issued (auto)                   |
| due_at      | TEXT    | Return due date                      |
| returned_at | TEXT    | When returned (null if active)       |
| status      | TEXT    | `active` / `returned` / `overdue`    |

---

## 🌐 API Endpoints

| Method | Endpoint                        | Description               |
|--------|---------------------------------|---------------------------|
| GET    | `/api/stats`                    | Dashboard statistics      |
| GET    | `/api/books?search=`            | List / search books       |
| POST   | `/api/books`                    | Add a new book            |
| PUT    | `/api/books/<id>`               | Update book details       |
| DELETE | `/api/books/<id>`               | Delete book               |
| GET    | `/api/members?search=`          | List / search members     |
| POST   | `/api/members`                  | Register new member       |
| DELETE | `/api/members/<id>`             | Remove member             |
| GET    | `/api/loans?status=`            | List loans (filter by status) |
| POST   | `/api/loans`                    | Issue a book              |
| PUT    | `/api/loans/<id>/return`        | Mark book as returned     |

---

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Flask, SQLite3, Flask-CORS
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Fonts**: Playfair Display + DM Sans (Google Fonts)
- **Database**: SQLite (file-based, zero config)
