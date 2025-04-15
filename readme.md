# CS432 - Module 3 

This Flask API implements Task 1 (Member Creation) and Task 2 (Role-Based Access Control - RBAC) for the CS432 Module 3 assignment.

## Prerequisites

* Python 3.8+
* pip (Python package installer)
* Access to the CS432 CIMS Database (`10.0.116.125`) with Group 2 (`cs432g2`) credentials.

## Setup Instructions

1. **Clone the repository (if applicable) or ensure code structure:**

   ```
   Database-Integration-and-Secure-API-Development
   |__ backend
       |__ app
           |__ auth
               |__ __init__.py
               |__ decorators.py
               |__ routes.py
           |__ equipment
               |__ __init__.py
               |__ routes.py
           |__ events
               |__ __init__.py
               |__ routes.py
           |__ matches
               |__ __init__.py
               |__ routes.py
           |__ members
               |__ __init__.py
               |__ routes.py
           |__ teams
               |__ __init__.py
               |__ routes.py
           |__ utils
               |__ __init__.py
               |__ database.py
               |__ helpers.py
           |__ venues
               |__ __init__.py
               |__ routes.py
           |__ __init__.py
       |__ instance
           |__ config.py
       |__ logs
           |__ app_task5_teams_tests.log
           |__ app_task123.log
       |__ config.py
       |__ demo.sh
       |__ run.py
   |__ frontend
       |__ public
           |__ favicon.ico  
           |__ index.html  
           |__ logo192.png  
           |__ logo512.png  
           |__ manifest.json  
           |__ robots.txt
       |__ src
           |__ components
               |__ EditMemberForm.js
           |__ context
               |__ AuthContext.js
           |__ pages
               |__ HomePage.js
               |__ LoginPage.js
               |__ MembersPage.js
           |__ services
               |__ api.js
           |__ App.css
           |__ App.js
           |__ App.test.js
           |__ index.css
           |__ index.js
           |__ logo.svg
           |__ reportWebVitals.js
           |__ setupTests.js
       |__ .gitignore
       |__ package.json
       |__ readme.md
   |__ logs
       |__ app.log  
       |__ app.log.1  
       |__ app.log.2  
       |__ app_task123.log  
       |__ app_task5_teams_tests.log
   |__ .gitignore
   |__ readme.md
   |__ requirements.txt
   ```

2. **Navigate to the project root directory:**

   ```bash
   cd /path/to/Database-Integration-and-Secure-API-Development
   ```

3. **Create and activate a virtual environment (highly recommended):**

   ```bash
   python3 -m venv mod3
   ```

   On Windows:

   ```bash
   .\mod3\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source mod3/bin/activate
   ```

4. **Install required Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install frontend dependencies:**

   Navigate to the `frontend/` directory:

   ```bash
   cd frontend
   npm install
   npm install axios
   npm install react-router-dom
   ```

## Running the Application

1. Ensure your virtual environment is activated.
2. Navigate to the backend directory and start the Flask app:

   ```bash
   cd backend
   python run.py
   ```

3. For the frontend, in a separate terminal:

   ```bash
   cd frontend
   npm start
   ```

4. Flask server typically runs on `http://0.0.0.0:5001` and React frontend on `http://localhost:3000`.

5. Logs will be saved under the `logs/` folder and `backend/logs/`.
