# 🔧 Flask REST API – Marketplace Backend Server

## 📌 Overview
Proyek ini adalah **RESTful Backend Server** berbasis **Flask** yang dirancang untuk mendukung aplikasi **mobile e-commerce / marketplace**. Sistem berfokus pada **API design, autentikasi & otorisasi, manajemen user, manajemen produk, serta pengelolaan database relasional**.

Aplikasi dibangun dengan arsitektur backend yang terstruktur dan modular.  
Fitur web crawling sempat dikembangkan, namun **pada versi ini sengaja dinonaktifkan** agar sistem berfungsi sebagai **API statis yang stabil, aman, dan siap diintegrasikan dengan client mobile**.

Proyek ini digunakan sebagai **portfolio teknis untuk pendaftaran magang Backend Engineer**.

---

## 🧠 Backend Engineering Focus
Proyek ini menonjolkan kemampuan:
- REST API development
- Authentication & Authorization
- Role-based access control
- Database modeling & relational data
- Clean & modular backend architecture
- Security awareness (hashing, token validation, safe logging)

---

## 🚀 Core Features

### 🔐 Authentication & Authorization
- User registration & login
- Token-based authentication (Bearer Token / JWT-like)
- Password hashing menggunakan **SHA-256 + salt**
- Role-based access control:
  - `admin`
  - `seller`
  - `buyer`
- Custom decorators:
  - `token_required`
  - `role_required`

---

### 👤 User Management
- Get & update user profile
- Upload avatar user
- Activity logging (user interaction log)
- Export activity log ke **CSV / JSON**

---

### 🛒 Product Management
- CRUD produk
- Pagination, filtering, dan sorting
- Manajemen kategori & brand
- Upload gambar produk
- Import produk dari file CSV
- Akses endpoint dikontrol berdasarkan role

---

### 🗄️ Data Handling
- PostgreSQL sebagai relational database
- SQLAlchemy ORM untuk:
  - Relasi antar tabel
  - Query abstraction
- Marshmallow untuk:
  - Serialization
  - Data validation
- Database dan tabel dibuat otomatis saat aplikasi pertama dijalankan

---

### 🧾 Logging & Maintainability
- Logging aktivitas server
- Tidak menyimpan data sensitif (password, token)
- Struktur kode modular dan mudah dikembangkan

---

## 🏗️ Backend Architecture

Aplikasi menggunakan **Layered Monolithic REST Architecture** dengan pemisahan tanggung jawab yang jelas antara routing, security, business logic, dan data access.


### Layer Explanation
- **Client Layer**: Mobile/Web client berkomunikasi melalui HTTP REST API menggunakan JSON dan Bearer Token.
- **API Routing Layer**: Flask Blueprint memisahkan domain API (`auth`, `users`, `products`).
- **Auth Layer**: Validasi token dan role user sebelum mengakses endpoint terproteksi.
- **Business Logic Layer**: Mengelola alur proses aplikasi dan validasi data.
- **Data Access Layer**: SQLAlchemy ORM sebagai abstraction layer database.
- **Database Layer**: PostgreSQL menyimpan data user, produk, kategori, brand, inventory, dan activity log.

---

## 🧱 Architectural Decisions

| Decision | Reason |
|--------|--------|
| Monolithic REST API | Sederhana dan cocok untuk tahap awal |
| Flask Blueprint | Modular dan scalable |
| Token-based Auth | Stateless dan mobile-friendly |
| SQLAlchemy ORM | Aman dan maintainable |
| Role-based Access | Mendukung multi-user system |

---

## 🧰 Tech Stack

| Layer | Technology |
|-----|-----------|
| Language | Python |
| Framework | Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Serialization | Marshmallow |
| Auth | Token-based Authentication |
| Scheduler | APScheduler (disabled) |
| Storage | Local File Storage |

---

## 🗂️ Project Structure
```
flask-ecommerce-server/
│
├── app/
│ ├── init.py # App factory & initialization
│ ├── config.py # Environment & DB config
│ ├── models/ # Database models
│ ├── routes/ # REST API endpoints
│ ├── utils/ # Auth decorator & helpers
│
├── uploads/ # User & product images
├── run.py # Application entry point
└── requirements.txt
```

---

## 🔗 API Endpoint Overview

### Auth – `/api/auth`
- `POST /register`
- `POST /login`

### Users – `/api/users`
- `GET /profile`
- `PUT /profile`
- `POST /upload-avatar`
- `GET /activities`
- `GET /export-activities`

### Products – `/api/products`
- `GET /`
- `POST /`
- `GET /<id>`
- `PUT /<id>`
- `DELETE /<id>`
- `POST /<id>/images`
- `GET /categories`
- `GET /brands`
- `POST /import-csv`

---

## ▶️ How to Run

### 1. Clone Repository
```bash
git clone https://github.com/Efind2/flask-ecommerce-server.git
cd flask-ecommerce-server
```
### 2. Create & Activate Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Configure Database
Sesuaikan konfigurasi PostgreSQL pada `app/config.py`:
```
SQLALCHEMY_DATABASE_URI = "postgresql://username:password@localhost:5432/db_name"
```
### 5. Run Application
```
python run.py
```
Server akan berjalan di:
```
http://127.0.0.1:5000
```

---

## Purpose

Proyek ini dikembangkan sebagai:

- Latihan Backend Engineering
- Backend service untuk aplikasi mobile
- Technical portfolio untuk pendaftaran magang Backend Engineer

## Note
Fitur crawling dinonaktifkan secara sengaja untuk menjaga stabilitas sistem dan memfokuskan pengembangan pada API backend inti.
