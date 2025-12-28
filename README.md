# 🗓️ 24/7 Work Schedule Manager

<img width="463" height="185" alt="Screenshot 2025-12-06 at 14 29 03" src="https://github.com/user-attachments/assets/95486ff4-55fe-4fe2-853d-0e56aff18970" />
 

A desktop application for generating, editing, validating, and 
exporting monthly work schedules for 24/7 shift-based operations.

The application is designed as a **standalone desktop system** 
with no web server, no browser, and no database requirements.

Developed as a real-world scheduling solution with a focus on 
stability, clarity, and long-term maintainability.

---

## ✨ Key Features

- ⚙️ **Automatic Schedule Generation**
  - Rotation-based logic (Day / Evening / Night);
  - Minimum requirement: 4 rotational employees + 1 administrator;
  - Shift sequence and rest validation;
  - Automatic handling of weekends and official holidays.

- ✏️ **Manual Schedule Overrides**
  - Inline shift editing directly in the calendar
  - Immediate persistence of changes
  - Manual edits never overwrite generator logic

- 👥 **Employee Management**
  - CRUD;
  - Optional employee card number;
  - Assign a monthly administrator.

- 🔒 **Month Locking & Validation**
  - Full validation before locking;
  - Coverage and rotation checks;
  - Locked months become read-only;
  - Required before export.

- 📊 **Excel Export**
  - Clean, printable Excel output;
  - Suitable for distribution and archiving.

- 📄 **User Guide**
  - Accessible directly from the application;
  - Opens as an external document (Word / PDF).

---

## 🧠 Architecture Overview

- **Python 3.13**
- **PyQt6** – desktop UI
- **JSON-based storage** – no database
- **No Django runtime**
  - Django-inspired logic reused only for business rules;
  - No HTTP, no `runserver`, no backend service.

---

## 📦 Packaging (Production)

The application is prepared for distribution as:
- **Windows (.exe)**
- **macOS (.app)**

Using PyInstaller, with no Python installation required for end users.

---

## 🧪 Tests

Mostly the Generator of the shifts is covered.

- **Test coverage includes:**
- Missing administrator;
- Insufficient employees;
- Successful generation;
- Daily shift coverage;
- Administrator weekday-only rules;
- Non-strict generation behavior.

---

## ⚠️ Important Notes

- All data is stored locally (JSON files);
- Each month is fully independent;
- Manual edits are preserved;
- Locked months are immutable except for export.

---

## 🤖 AI-Assisted Development
This project was developed with the assistance of AI tools used as a collaborative aid for:
- Architecture validation;
- code assistance;
- Edge-case analysis;
- Refactoring support;
- Test case design;

**All core logic, structure, and final decisions were designed, reviewed, and validated by the developer.**

---

---


