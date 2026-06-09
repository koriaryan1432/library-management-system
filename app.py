from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pymysql
import pymysql.cursors
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# ─────────────────────────────────────────────
# MySQL CONNECTION
# ─────────────────────────────────────────────

DB_CONFIG = {
    'host':        os.getenv('DB_HOST',     'localhost'),
    'port':        int(os.getenv('DB_PORT', 3306)),
    'db':          os.getenv('DB_NAME',     'library_db'),
    'user':        os.getenv('DB_USER',     'root'),
    'password':    os.getenv('DB_PASSWORD', ''),
    'charset':     'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit':  False,
}


def get_db():
    """Open a fresh MySQL connection (one per request)."""
    return pymysql.connect(**DB_CONFIG)


# ─────────────────────────────────────────────
# DATABASE INITIALISATION
# ─────────────────────────────────────────────

def init_db():
    """Create the database + tables, seed sample data if empty."""
    import time
    cfg = {k: v for k, v in DB_CONFIG.items() if k not in ('db', 'cursorclass')}
    db_name = DB_CONFIG['db']

    # Retry loop — MySQL container may need a few extra seconds to be ready
    for attempt in range(1, 11):
        try:
            conn = pymysql.connect(**cfg, cursorclass=pymysql.cursors.DictCursor)
            break
        except pymysql.err.OperationalError as e:
            print(f"⏳ Waiting for MySQL... attempt {attempt}/10 ({e})")
            time.sleep(3)
    else:
        raise RuntimeError("❌ Could not connect to MySQL after 10 attempts.")
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{db_name}`")

        cur.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                title         VARCHAR(255) NOT NULL,
                author        VARCHAR(255) NOT NULL,
                isbn          VARCHAR(20)  UNIQUE,
                genre         VARCHAR(100),
                total_copies  INT DEFAULT 1,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id        INT AUTO_INCREMENT PRIMARY KEY,
                name      VARCHAR(255) NOT NULL,
                email     VARCHAR(255) UNIQUE NOT NULL,
                phone     VARCHAR(20),
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                book_id     INT NOT NULL,
                member_id   INT NOT NULL,
                loaned_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_at      DATE,
                returned_at DATETIME DEFAULT NULL,
                status      ENUM('active','returned','overdue') DEFAULT 'active',
                FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE RESTRICT,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB
        ''')

        # Seed only when tables are empty
        cur.execute("SELECT COUNT(*) AS cnt FROM books")
        if cur.fetchone()['cnt'] == 0:
            books = [
                ("The Great Gatsby",         "F. Scott Fitzgerald", "978-0-7432-7356-5", "Fiction",     3),
                ("To Kill a Mockingbird",    "Harper Lee",          "978-0-06-112008-4", "Fiction",     2),
                ("1984",                     "George Orwell",       "978-0-451-52493-5", "Dystopian",   4),
                ("Sapiens",                  "Yuval Noah Harari",   "978-0-06-231609-7", "Non-Fiction", 2),
                ("Clean Code",               "Robert C. Martin",    "978-0-13-235088-4", "Technology",  3),
                ("Atomic Habits",            "James Clear",         "978-0-7352-1129-2", "Self-Help",   5),
                ("The Pragmatic Programmer", "Andrew Hunt",         "978-0-13-595705-9", "Technology",  2),
                ("Dune",                     "Frank Herbert",       "978-0-441-17271-9", "Sci-Fi",      3),
            ]
            cur.executemany(
                "INSERT INTO books (title, author, isbn, genre, total_copies) VALUES (%s,%s,%s,%s,%s)",
                books
            )

            members = [
                ("Arjun Sharma", "arjun@email.com", "9876543210"),
                ("Priya Nair",   "priya@email.com", "9876543211"),
                ("Rahul Verma",  "rahul@email.com", "9876543212"),
                ("Sneha Kapoor", "sneha@email.com", "9876543213"),
            ]
            cur.executemany(
                "INSERT INTO members (name, email, phone) VALUES (%s,%s,%s)",
                members
            )

            due = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            cur.executemany(
                "INSERT INTO loans (book_id, member_id, due_at) VALUES (%s,%s,%s)",
                [(1, 1, due), (3, 2, due)]
            )

    conn.commit()
    conn.close()
    print(f"✅  MySQL database `{db_name}` is ready.")


# ─────────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


# ─────────────────────────────────────────────
# BOOKS API
# ─────────────────────────────────────────────

@app.route('/api/books', methods=['GET'])
def get_books():
    search = f"%{request.args.get('search', '')}%"
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT b.*,
                    (b.total_copies - COUNT(CASE WHEN l.status = 'active' THEN 1 END)) AS available
                FROM books b
                LEFT JOIN loans l ON l.book_id = b.id
                WHERE b.title LIKE %s OR b.author LIKE %s OR b.genre LIKE %s
                GROUP BY b.id
                ORDER BY b.title
            ''', (search, search, search))
            return jsonify(cur.fetchall())
    finally:
        conn.close()


@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO books (title, author, isbn, genre, total_copies) VALUES (%s,%s,%s,%s,%s)",
                (data['title'], data['author'], data.get('isbn'), data.get('genre'), data.get('total_copies', 1))
            )
        conn.commit()
        return jsonify({'id': cur.lastrowid, 'message': 'Book added successfully'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'ISBN already exists'}), 400
    finally:
        conn.close()


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.json
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE books SET title=%s, author=%s, isbn=%s, genre=%s, total_copies=%s WHERE id=%s",
                (data['title'], data['author'], data.get('isbn'), data.get('genre'), data.get('total_copies', 1), book_id)
            )
        conn.commit()
        return jsonify({'message': 'Book updated'})
    finally:
        conn.close()


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM loans WHERE book_id=%s AND status='active'", (book_id,)
            )
            if cur.fetchone()['cnt']:
                return jsonify({'error': 'Cannot delete a book with active loans'}), 400
            cur.execute("DELETE FROM books WHERE id=%s", (book_id,))
        conn.commit()
        return jsonify({'message': 'Book deleted'})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# MEMBERS API
# ─────────────────────────────────────────────

@app.route('/api/members', methods=['GET'])
def get_members():
    search = f"%{request.args.get('search', '')}%"
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM members WHERE name LIKE %s OR email LIKE %s ORDER BY name",
                (search, search)
            )
            return jsonify(cur.fetchall())
    finally:
        conn.close()


@app.route('/api/members', methods=['POST'])
def add_member():
    data = request.json
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO members (name, email, phone) VALUES (%s,%s,%s)",
                (data['name'], data['email'], data.get('phone'))
            )
        conn.commit()
        return jsonify({'id': cur.lastrowid, 'message': 'Member added'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        conn.close()


@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members WHERE id=%s", (member_id,))
        conn.commit()
        return jsonify({'message': 'Member deleted'})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# LOANS API
# ─────────────────────────────────────────────

@app.route('/api/loans', methods=['GET'])
def get_loans():
    status = request.args.get('status', '')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            base = '''
                SELECT l.*, b.title AS book_title, b.author,
                       m.name AS member_name, m.email
                FROM loans l
                JOIN books   b ON b.id = l.book_id
                JOIN members m ON m.id = l.member_id
            '''
            if status:
                cur.execute(base + " WHERE l.status = %s ORDER BY l.loaned_at DESC", (status,))
            else:
                cur.execute(base + " ORDER BY l.loaned_at DESC")
            return jsonify(cur.fetchall())
    finally:
        conn.close()


@app.route('/api/loans', methods=['POST'])
def create_loan():
    data      = request.json
    book_id   = data['book_id']
    member_id = data['member_id']
    days      = int(data.get('days', 14))
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT b.total_copies,
                       COUNT(CASE WHEN l.status = 'active' THEN 1 END) AS loaned
                FROM books b
                LEFT JOIN loans l ON l.book_id = b.id
                WHERE b.id = %s
                GROUP BY b.id
            ''', (book_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'Book not found'}), 404
            if row['loaned'] >= row['total_copies']:
                return jsonify({'error': 'No copies available'}), 400

            due = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            cur.execute(
                "INSERT INTO loans (book_id, member_id, due_at) VALUES (%s,%s,%s)",
                (book_id, member_id, due)
            )
        conn.commit()
        return jsonify({'id': cur.lastrowid, 'due_at': due, 'message': 'Loan created'}), 201
    finally:
        conn.close()


@app.route('/api/loans/<int:loan_id>/return', methods=['PUT'])
def return_book(loan_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE loans SET returned_at=NOW(), status='returned' WHERE id=%s",
                (loan_id,)
            )
        conn.commit()
        return jsonify({'message': 'Book returned successfully'})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Auto-mark overdue
            cur.execute(
                "UPDATE loans SET status='overdue' WHERE status='active' AND due_at < CURDATE()"
            )
            cur.execute("SELECT COALESCE(SUM(total_copies), 0) AS n FROM books")
            total_books = cur.fetchone()['n']

            cur.execute("SELECT COUNT(*) AS n FROM members")
            total_members = cur.fetchone()['n']

            cur.execute("SELECT COUNT(*) AS n FROM loans WHERE status='active'")
            active_loans = cur.fetchone()['n']

            cur.execute("SELECT COUNT(*) AS n FROM loans WHERE status='overdue'")
            overdue = cur.fetchone()['n']

        conn.commit()
        return jsonify({
            'total_books':   total_books,
            'total_members': total_members,
            'active_loans':  active_loans,
            'overdue_loans': overdue,
        })
    finally:
        conn.close()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("📚 Bibliotheca running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
