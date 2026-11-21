# PharmaSystem — CLI Pharmacy Management System

A terminal-based pharmacy management system built with Python and MySQL. It supports medicine and batch inventory management, FEFO (First-Expiry-First-Out) sales, expiry and low-stock alerts, and role-based access control for pharmacists and attendants.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Role Permissions](#role-permissions)
- [Security](#security)
- [Default Credentials](#default-credentials)

---

## Features

- **Role-based access control** — `pharmacist` and `attendant` roles with distinct permissions
- **Medicine & batch management** — add medicines with batch numbers, quantities, prices, expiry dates, and reorder levels
- **FEFO sales** — sales automatically consume stock from the earliest-expiring batch first
- **Expiry alerts** — lists batches expiring within 90 days and already-expired stock
- **Low/out-of-stock alerts** — flags medicines at or below their reorder level
- **Sales reporting** — today's completed sales count and total revenue
- **Sale voiding** — pharmacists can void completed sales with a reason; batch quantities are automatically restored
- **User management** — pharmacists can create and delete system users
- **Secure password hashing** — PBKDF2-HMAC-SHA256 with a unique random salt per user
- **Auto database provisioning** — database and all tables are created automatically on first run

---

## Project Structure

```
PLP2_Group19/
├── main.py              # Entry point; CLI loop and menu handling
├── db.py                # Database connection and schema initialisation
├── auth.py              # Authentication, user management, password hashing
├── inventory.py         # Medicine and batch management, stock status computation
├── sales.py             # FEFO sale recording and sale voiding
├── alerts_reports.py    # Expiry alerts, low-stock alerts, sales summary
├── .env                 # Local environment variables (not committed)
├── .env.example         # Environment variable template
└── .gitignore
```

---

## Database Schema

The system uses five MySQL tables:

### `users`
| Column          | Type                              | Description                        |
|-----------------|-----------------------------------|------------------------------------|
| `id`            | INT AUTO_INCREMENT PK             | User ID                            |
| `username`      | VARCHAR(30) UNIQUE NOT NULL       | Login username                     |
| `full_name`     | VARCHAR(100) NOT NULL             | Display name                       |
| `password_hash` | VARCHAR(255) NOT NULL             | `salt$pbkdf2_digest` format        |
| `role`          | ENUM(`pharmacist`, `attendant`)   | Access role                        |
| `is_active`     | TINYINT(1)                        | Account active flag                |

### `medicines`
| Column          | Type                    | Description                          |
|-----------------|-------------------------|--------------------------------------|
| `id`            | INT AUTO_INCREMENT PK   | Medicine ID                          |
| `name`          | VARCHAR(100) UNIQUE     | Medicine name                        |
| `unit_price`    | DECIMAL(10,2)           | Selling price per unit               |
| `reorder_level` | INT DEFAULT 20          | Minimum stock threshold for alerts   |
| `is_active`     | TINYINT(1)              | Soft-delete flag                     |

### `batches`
| Column          | Type                    | Description                          |
|-----------------|-------------------------|--------------------------------------|
| `id`            | INT AUTO_INCREMENT PK   | Batch ID                             |
| `medicine_id`   | INT FK → medicines      | Associated medicine                  |
| `batch_number`  | VARCHAR(50)             | Supplier batch reference             |
| `quantity`      | INT                     | Current remaining quantity           |
| `expiry_date`   | DATE                    | Batch expiry date                    |
| `received_date` | DATE                    | Date batch was received              |
| `is_active`     | TINYINT(1)              | Soft-delete flag                     |

### `sales`
| Column          | Type                              | Description                          |
|-----------------|-----------------------------------|--------------------------------------|
| `id`            | INT AUTO_INCREMENT PK             | Sale ID                              |
| `user_id`       | INT FK → users (nullable)         | Staff who recorded the sale          |
| `total_amount`  | DECIMAL(12,2)                     | Total sale value                     |
| `status`        | ENUM(`completed`, `voided`)       | Sale status                          |
| `void_reason`   | VARCHAR(255) nullable             | Reason if voided                     |
| `sold_at`       | DATETIME DEFAULT CURRENT_TIMESTAMP| Sale timestamp                       |

### `sale_items`
| Column       | Type                  | Description                            |
|--------------|-----------------------|----------------------------------------|
| `id`         | INT AUTO_INCREMENT PK | Item ID                                |
| `sale_id`    | INT FK → sales        | Parent sale                            |
| `batch_id`   | INT FK → batches      | Batch stock was drawn from             |
| `medicine_id`| INT FK → medicines    | Medicine sold                          |
| `quantity`   | INT                   | Units sold from this batch             |
| `unit_price` | DECIMAL(10,2)         | Price at time of sale                  |

---

## Architecture Overview

The application follows a layered service architecture:

```
main.py  (CLI / Presentation Layer)
    │
    ├── AuthService        (auth.py)
    ├── InventoryService   (inventory.py)
    ├── SalesService       (sales.py)
    └── AlertsAndReportsService  (alerts_reports.py)
            │
            └── PharmaDatabase  (db.py)  ← MySQL via mysql-connector-python
```

- `PharmaDatabase` owns all connections and schema initialisation. Every service receives a `db` instance and calls `db.connect()` to get a fresh connection per operation.
- All write operations use explicit transactions with rollback on failure.
- The CLI layer in `main.py` catches `ValueError` (business rule violations) and `mysql.connector.Error` (database errors) separately, displaying user-friendly messages without crashing.

---

## Prerequisites

- Python 3.10+
- MySQL 8.0+ (or MariaDB 10.6+)
- `mysql-connector-python` package

---

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PLP2_Group19
   ```

2. **Install dependencies**
   ```bash
   pip install mysql-connector-python
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your MySQL credentials (see [Configuration](#configuration)).

4. **Run the application** — the database and all tables are created automatically on first run.
   ```bash
   py main.py
   ```

---

## Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and fill in your values:

```env
PHARMA_DB_HOST=localhost
PHARMA_DB_PORT=3306
PHARMA_DB_USER=root
PHARMA_DB_PASSWORD=your_password
PHARMA_DB_NAME=pharma_db
```

| Variable           | Default     | Description                  |
|--------------------|-------------|------------------------------|
| `PHARMA_DB_HOST`   | —           | MySQL server hostname        |
| `PHARMA_DB_PORT`   | `3306`      | MySQL server port            |
| `PHARMA_DB_USER`   | —           | MySQL username               |
| `PHARMA_DB_PASSWORD` | —         | MySQL password               |
| `PHARMA_DB_NAME`   | —           | Database name to use/create  |

> The `.env` file is listed in `.gitignore` and should never be committed to version control.

---

## Running the Application

```bash
py main.py
```

On startup the application will:
1. Load environment variables from `.env`
2. Connect to MySQL and create the database if it does not exist
3. Create all required tables if they do not exist
4. Seed a default admin account if no `admin` user exists
5. Present the login prompt

---

## Usage Guide

### Login
```
=== PHARMA LOGIN ===
Username: admin
Password: admin123
```
Three failed attempts will exit the login loop.

### Main Menu

```
=== PHARMA MENU ===
1. Search medicines
2. Record FEFO sale
3. View expiry & low-stock alerts
4. Add medicine / batch          [pharmacist only]
5. Today's sales summary         [pharmacist only]
6. Void a sale                   [pharmacist only]
7. Create user                   [pharmacist only]
8. Delete user                   [pharmacist only]
0. Logout / Exit
```

### Option 1 — Search Medicines
Enter a keyword or leave blank to list all active medicines. Displays stock quantity, status, unit price, and nearest expiry date.

### Option 2 — Record FEFO Sale
Enter a medicine ID and quantity. The system automatically allocates stock from the earliest-expiring non-expired batch first. Prints a per-batch allocation breakdown with remaining quantities.

### Option 3 — Expiry & Low-Stock Alerts
Displays three sections:
- Batches expiring within the next 90 days (with days remaining)
- Already-expired batches still holding stock
- Medicines at Low Stock or Out of Stock status

### Option 4 — Add Medicine / Batch *(pharmacist)*
Adds a new medicine or updates an existing one's price and reorder level, then records a new batch with quantity and expiry date. Expiry date must be in the future.

### Option 5 — Today's Sales Summary *(pharmacist)*
Shows the total number of completed sales and total revenue for the current calendar day.

### Option 6 — Void a Sale *(pharmacist)*
Voids a completed sale by ID with a mandatory reason. All batch quantities consumed by the sale are automatically restored.

### Option 7 — Create User *(pharmacist)*
Creates a new system user with a username, full name, password, and role (`pharmacist` or `attendant`).

### Option 8 — Delete User *(pharmacist)*
Lists all users with their ID, username, full name, role, and active status, then prompts for a username to permanently delete. The default `admin` account cannot be deleted.

---

## Role Permissions

| Feature                    | Pharmacist | Attendant |
|----------------------------|:----------:|:---------:|
| Search medicines           | ✅         | ✅        |
| Record FEFO sale           | ✅         | ✅        |
| View expiry/stock alerts   | ✅         | ✅        |
| Add medicine / batch       | ✅         | ❌        |
| Today's sales summary      | ✅         | ❌        |
| Void a sale                | ✅         | ❌        |
| Create user                | ✅         | ❌        |
| Delete user                | ✅         | ❌        |

---

## Security

- **Password hashing** — passwords are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and a cryptographically random 16-byte salt generated per user via `os.urandom`. The stored format is `hex_salt$hex_digest`.
- **No plaintext credentials** — passwords are never stored or logged in plaintext.
- **Environment-based configuration** — database credentials are loaded from `.env` at runtime and never hardcoded.
- **Transaction safety** — all write operations (sales, batch updates, user creation) are wrapped in explicit transactions and rolled back on any failure.
- **Protected admin account** — the default `admin` account cannot be deleted through the application.

---

## Default Credentials

> **Change these immediately after first login.**

| Username | Password  | Role        |
|----------|-----------|-------------|
| `admin`  | `admin123`| pharmacist  |

The default admin account is created automatically on first run only if no `admin` user exists in the database.
