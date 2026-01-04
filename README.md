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
- **macOS (.app)- currently!**

### 🪟 Windows Packaging (Terminal-only)
- **Windows (.exe)**

> ⚠️ **Important:** Windows packaging must be performed **on a Windows machine**.  
> Cross-platform builds (macOS → Windows) are **not supported** by PyInstaller.

No IDE is required. The entire process is done using **Command Prompt** or **PowerShell**.

##### ⚠️ Important Notes
- All data is stored locally (JSON files);
- Each month is fully independent;
- Manual edits are preserved;
- Locked months are immutable except for export;
- The application runs as a **portable executable** (no installation required).

---

#### 🔧 Prerequisites (Windows)
Before starting, make sure the following are installed:
- **Python 3.10+** (enable **“Add Python to PATH”** during installation)
- **Git for Windows**

A system restart after installation is recommended.

---

#### 1️⃣ Clone the project
```bat
git clone https://github.com/Zeus097/work_schedule.git
cd <Repo dir>
```
#### 2️⃣ Create and activate virtual environment
```bat
py -m venv venv
venv\Scripts\activate
```

#### 3️⃣ Install dependencies
```bat
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install pyinstaller
```


#### 4️⃣ Clean previous builds
```bat
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
```

#### 5️⃣ Build Windows executable
```bat
py -m PyInstaller Kantar.spec
```

#### 📦 Output
```bat
dist\Kantar.exe
```

**The resulting file is a single, self-contained Windows executable and can be:**
- copied directly to another computer,
- placed on a USB drive,
- executed without installation.

#### ✅ **Notes**
- The Windows build does not require PyCharm or any IDE.
- All packaging steps are executed via terminal.
- The .spec file defines included data files, resources, and runtime configuration.
- No business logic changes are required for Windows packaging.
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


