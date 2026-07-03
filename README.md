# Secure-Court-Connect: Digital Court Hearing Scheduling Platform

Secure-Court-Connect is a secure, role-based web application engineered to modernize judicial operations, manage digital case filings, and safeguard sensitive legal communications. 

The platform isolates workflows natively for three distinct user groups: **Courts (Judicial Admins)**, **Lawyers**, and **Clients/Citizens**.

---

## 🎯 Executive Highlights (For Recruiters)
* **Production Migration:** Successfully re-architected and migrated the data layer from temporary schema-less TinyDB dictionary stores to a strict relational **MySQL database backend**.
* **Data Protection & Privacy:** Implemented character-stream encryption on the wire using a custom implementation of the **Affine Cipher** to protect sensitive documents and communications.
* **System Stability & Defenses:** Engineered a strict database transaction wrapper using explicit `try/except/rollback` blocks to completely eliminate MySQL session deadlocks during concurrent write operations.
* **Security Injection Prevention:** Enforced dynamic alphanumeric hexadecimal IDs (e.g., `cd2c9d1e`) across files and appointments to mitigate predictable integer resource-scanning vulnerabilities.

---

## 🏗️ System Architecture & Database Schema

The platform maps system interactions cleanly using **Flask-SQLAlchemy** and the **PyMySQL** driver. Tables are tightly coupled to enforce relational data integrity:

* **Users & Profiles:** Centralizes platform authentication using `werkzeug.security` for salted password hashing. Relational identity branches out into specialized data tables: `CourtProfile`, `LawyerProfile`, and `ClientProfile` via cascading relational delete hooks.
* **Case Tracking (`cases`):** Tracks legal logs using strict `case_title` and `case_number` properties to drive dynamic dashboard template renderings.
* **Hearings Scheduler (`hearings`):** Chronologically links courtrooms, judges, statuses, and notes directly to a parent case using strict foreign key constraints.
* **Digital Storage Archive (`files`):** Tracks encrypted document assets on the server disk, preserving file metadata sizes as pure integers to protect downstream Jinja filter division.
* **Message Center (`messages`):** Provides a secure platform for communication, including an integrated UI framework allowing clients to safely view and decrypt court notifications on demand.

---

## 💻 Technical Stack

* **Backend Framework:** Python 3.12+, Flask, Flask-Login
* **Database Engine:** MySQL Server
* **ORM Connection Layer:** Flask-SQLAlchemy, PyMySQL
* **Security & Encryption:** Werkzeug (Hashing), Custom Affine Cipher (Payload Obfuscation)
* **Frontend Templating:** HTML5, CSS3, JavaScript, Jinja2 Engine

---

## 🚀 Local Installation & Quick Start

### 1. Clone & Navigate
```bash
git clone [https://github.com/Sumanth4299/Digital-court-hearing-and-scheduling-with-role-based-access-control.git](https://github.com/Sumanth4299/Digital-court-hearing-and-scheduling-with-role-based-access-control.git)
cd Secure-Court-Connect
