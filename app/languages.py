"""
Language Registry & Built-in Code Examples Library for CodeMirror 2.0 / Code Wizard
Defines supported programming languages, beginner lessons, a fixed 6-example beginner
library per language (Hello world, Variables, Condition, Loop, Function, Practical),
and setup guides matched to each language's real runner.
"""

from typing import Dict, Any, List
from app.runtimes import check_language_runtime

LANGUAGES_CATALOG: Dict[str, Dict[str, Any]] = {
    "python": {
        "id": "python",
        "name": "Python",
        "icon": "🐍",
        "category": "Interpreted",
        "difficulty": "Beginner Friendly",
        "short_description": "Clean, readable syntax ideal for learning fundamental logic, data manipulation, and backend APIs.",
        "paradigm": "Multi-paradigm: Object-Oriented, Functional, Procedural",
        "starter_code": "# Welcome to the Python Workspace!\n# Write your code below:\n\ndef main():\n    print('Hello, Python Learner!')\n\nif __name__ == '__main__':\n    main()\n",
        "file_ext": ".py",
        "monaco_lang": "python",
        "setup_guide": {
            "title": "Python 3 Interpreter Setup",
            "instructions": (
                "Python is installed and available on this server. "
                "For local development, download Python 3.10+ from python.org and check 'Add python.exe to PATH' during installation."
            ),
            "command": "python --version"
        },
        "lessons": [
            {
                "id": "py_lesson_1",
                "title": "1. Variables & Basic Types",
                "summary": "Understand integers, floats, strings, and booleans in Python without variable declarations.",
                "explanation": "In Python, variables are dynamically typed. Assign values using the = operator.",
                "example": "student_name = 'Alex'\nage = 20\ngpa = 3.85\nis_enrolled = True\nprint(f'{student_name} is {age} years old.')"
            },
            {
                "id": "py_lesson_2",
                "title": "2. Conditional Logic & Comparisons",
                "summary": "Make decisions using if, elif, and else statements.",
                "explanation": "Python uses indentation (4 spaces) rather than curly braces to define code blocks.",
                "example": "score = 85\nif score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelse:\n    grade = 'C'\nprint(f'Grade: {grade}')"
            },
            {
                "id": "py_lesson_3",
                "title": "3. Loops: For & While",
                "summary": "Iterate through lists, ranges, and repeat actions.",
                "explanation": "Use 'for item in collection' to loop over sequences, and 'while condition' for indeterminate loops.",
                "example": "for count in range(1, 4):\n    print(f'Step {count}')\n\nitems = ['apples', 'oranges', 'pears']\nfor fruit in items:\n    print(fruit.upper())"
            },
            {
                "id": "py_lesson_4",
                "title": "4. Functions & Scope",
                "summary": "Encapsulate reusable logic with the def keyword.",
                "explanation": "Functions accept parameters, perform calculations, and return results with the return statement.",
                "example": "def calculate_rectangle_area(width: float, height: float) -> float:\n    if width <= 0 or height <= 0:\n        return 0.0\n    return width * height\n\narea = calculate_rectangle_area(5.0, 4.0)\nprint(f'Area: {area}')"
            }
        ],
        "examples": [
            {
                "id": "py_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Prints a friendly greeting to the console using Python's built-in print() function.",
                "explanation": "Prints a friendly greeting to the console using Python's built-in print() function.",
                "filename": "hello.py",
                "code": (
                    "# 1. Hello, world in Python\n"
                    "# print() displays text in the output panel.\n"
                    "print(\"Hello, World!\")\n"
                    "print(\"Welcome to Python in Code Wizard.\")\n"
                ),
                "expected_output": "Hello, World!\nWelcome to Python in Code Wizard."
            },
            {
                "id": "py_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Stores text, whole numbers, decimals, and true/false values in named variables.",
                "explanation": "Stores text, whole numbers, decimals, and true/false values in named variables.",
                "filename": "variables.py",
                "code": (
                    "# 2. Variables and basic data types in Python\n"
                    "student_name = \"Maya\"     # String (text)\n"
                    "completed_labs = 4        # Integer (whole number)\n"
                    "average_score = 92.5      # Float (decimal number)\n"
                    "is_active = True          # Boolean (True or False)\n\n"
                    "# Use an f-string to combine variables into a message\n"
                    "print(f\"Student: {student_name}\")\n"
                    "print(f\"Completed labs: {completed_labs}\")\n"
                    "print(f\"Average score: {average_score}\")\n"
                    "print(f\"Active account: {is_active}\")\n"
                ),
                "expected_output": (
                    "Student: Maya\n"
                    "Completed labs: 4\n"
                    "Average score: 92.5\n"
                    "Active account: True"
                )
            },
            {
                "id": "py_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Uses if, elif, and else statements to choose a letter grade based on a numeric score.",
                "explanation": "Uses if, elif, and else statements to choose a letter grade based on a numeric score.",
                "filename": "condition.py",
                "code": (
                    "# 3. Making decisions with if / elif / else\n"
                    "score = 86\n\n"
                    "# Python checks each condition from top to bottom\n"
                    "if score >= 90:\n"
                    "    grade = \"A\"\n"
                    "elif score >= 80:\n"
                    "    grade = \"B\"\n"
                    "elif score >= 70:\n"
                    "    grade = \"C\"\n"
                    "else:\n"
                    "    grade = \"Needs Review\"\n\n"
                    "print(f\"Score: {score} -> Grade: {grade}\")\n"
                ),
                "expected_output": "Score: 86 -> Grade: B"
            },
            {
                "id": "py_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Repeats an action for every item in a list and totals the numbers with a for loop.",
                "explanation": "Repeats an action for every item in a list and totals the numbers with a for loop.",
                "filename": "loop.py",
                "code": (
                    "# 4. Looping through a list of numbers\n"
                    "daily_points = [10, 15, 20, 25]\n"
                    "total = 0\n\n"
                    "# Visit each number in daily_points one by one\n"
                    "for day_index, points in enumerate(daily_points, start=1):\n"
                    "    total += points\n"
                    "    print(f\"Day {day_index}: +{points} pts (Running total: {total})\")\n\n"
                    "print(f\"Final total: {total} pts\")\n"
                ),
                "expected_output": (
                    "Day 1: +10 pts (Running total: 10)\n"
                    "Day 2: +15 pts (Running total: 25)\n"
                    "Day 3: +20 pts (Running total: 45)\n"
                    "Day 4: +25 pts (Running total: 70)\n"
                    "Final total: 70 pts"
                )
            },
            {
                "id": "py_function",
                "category": "function",
                "title": "A simple function",
                "description": "Defines a reusable function that takes two numbers, calculates rectangle area, and returns the result.",
                "explanation": "Defines a reusable function that takes two numbers, calculates rectangle area, and returns the result.",
                "filename": "function.py",
                "code": (
                    "# 5. Defining and calling a reusable function\n"
                    "def calculate_area(width, height):\n"
                    "    \"\"\"Returns the area of a rectangle.\"\"\"\n"
                    "    return width * height\n\n"
                    "# Call the function with different inputs\n"
                    "first_room = calculate_area(5, 4)\n"
                    "second_room = calculate_area(8, 3)\n\n"
                    "print(f\"5x4 room area: {first_room}\")\n"
                    "print(f\"8x3 room area: {second_room}\")\n"
                ),
                "expected_output": "5x4 room area: 20\n8x3 room area: 24"
            },
            {
                "id": "py_practical",
                "category": "practical",
                "title": "Practical example: Filter active study groups",
                "description": "Filters a list of dictionary records to find active study groups and summarizes their enrollment.",
                "explanation": "Filters a list of dictionary records to find active study groups and summarizes their enrollment.",
                "filename": "study_groups.py",
                "code": (
                    "# 6. Practical example: Filtering dictionary records in Python\n"
                    "study_groups = [\n"
                    "    {\"name\": \"Python Basics\", \"members\": 14, \"active\": True},\n"
                    "    {\"name\": \"Archived Club\", \"members\": 5, \"active\": False},\n"
                    "    {\"name\": \"SQL Workshop\", \"members\": 18, \"active\": True},\n"
                    "]\n\n"
                    "# Keep only groups where 'active' is True\n"
                    "active_groups = [g for g in study_groups if g[\"active\"]]\n\n"
                    "print(f\"Active groups ({len(active_groups)}):\")\n"
                    "for group in active_groups:\n"
                    "    print(f\"- {group['name']}: {group['members']} members\")\n"
                ),
                "expected_output": (
                    "Active groups (2):\n"
                    "- Python Basics: 14 members\n"
                    "- SQL Workshop: 18 members"
                )
            }
        ]
    },
    "sql": {
        "id": "sql",
        "name": "SQL (SQLite)",
        "icon": "🗄️",
        "category": "Query Language",
        "difficulty": "Beginner Friendly",
        "short_description": "Declarative language to query, filter, sort, and join structured relational tables.",
        "paradigm": "Declarative Relational Database Querying",
        "starter_code": "-- Welcome to the SQL Database Workspace!\n-- Write your SELECT query below:\n\nSELECT id, title, status FROM resources;\n",
        "file_ext": ".sql",
        "monaco_lang": "sql",
        "setup_guide": {
            "title": "SQLite Engine Setup",
            "instructions": (
                "SQLite is built directly into Python's standard library and runs in an isolated in-memory database on this server. "
                "No external database installation is required."
            ),
            "command": "python -c \"import sqlite3; print(sqlite3.sqlite_version)\""
        },
        "lessons": [
            {
                "id": "sql_lesson_1",
                "title": "1. The SELECT Statement",
                "summary": "Retrieve specific columns or all columns from a table.",
                "explanation": "Use SELECT column1, column2 FROM table_name to query records.",
                "example": "SELECT id, title, created_at FROM resources;"
            },
            {
                "id": "sql_lesson_2",
                "title": "2. Filtering with WHERE",
                "summary": "Narrow down records based on conditions using comparison and logical operators.",
                "explanation": "Combine filters using AND, OR, and NOT. Use strings enclosed in single quotes.",
                "example": "SELECT id, title FROM resources WHERE status = 'active' AND category_id = 2;"
            },
            {
                "id": "sql_lesson_3",
                "title": "3. Sorting & Limits",
                "summary": "Order query results and limit result row counts.",
                "explanation": "Use ORDER BY column ASC/DESC to sort, and LIMIT n to cap output rows.",
                "example": "SELECT title, created_at FROM resources ORDER BY created_at DESC LIMIT 10;"
            },
            {
                "id": "sql_lesson_4",
                "title": "4. Relational Joins",
                "summary": "Combine data across multiple tables connected by foreign keys.",
                "explanation": "INNER JOIN combines rows from both tables whenever the join condition matches.",
                "example": "SELECT r.id, r.title, c.name AS category_name\nFROM resources r\nINNER JOIN categories c ON r.category_id = c.id;"
            }
        ],
        "examples": [
            {
                "id": "sql_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Returns a single greeting column using a simple SQL SELECT statement.",
                "explanation": "Returns a single greeting column using a simple SQL SELECT statement.",
                "filename": "hello.sql",
                "code": (
                    "-- 1. Hello, world in SQL\n"
                    "-- SELECT can return literal text with a column alias using AS.\n"
                    "SELECT 'Hello, World!' AS message, 'SQLite is ready' AS status;\n"
                ),
                "expected_output": (
                    "message       | status         \n"
                    "--------------+----------------\n"
                    "Hello, World! | SQLite is ready"
                )
            },
            {
                "id": "sql_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Creates a small table with text, integer, and decimal columns, inserts rows, and selects them.",
                "explanation": "Creates a small table with text, integer, and decimal columns, inserts rows, and selects them.",
                "filename": "variables_data.sql",
                "code": (
                    "-- 2. Storing basic data types (TEXT, INTEGER, REAL) in a SQL table\n"
                    "CREATE TABLE students_demo (\n"
                    "    id INTEGER PRIMARY KEY,\n"
                    "    name TEXT NOT NULL,\n"
                    "    credits INTEGER,\n"
                    "    gpa REAL\n"
                    ");\n\n"
                    "INSERT INTO students_demo (id, name, credits, gpa) VALUES\n"
                    "(1, 'Alex', 15, 3.8),\n"
                    "(2, 'Priya', 18, 3.95);\n\n"
                    "SELECT name, credits, gpa FROM students_demo ORDER BY id;\n"
                ),
                "expected_output": (
                    "name  | credits | gpa \n"
                    "------+---------+-----\n"
                    "Alex  | 15      | 3.8 \n"
                    "Priya | 18      | 3.95"
                )
            },
            {
                "id": "sql_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Uses a WHERE clause and a CASE expression to filter and label rows based on a condition.",
                "explanation": "Uses a WHERE clause and a CASE expression to filter and label rows based on a condition.",
                "filename": "condition.sql",
                "code": (
                    "-- 3. Filtering rows with WHERE and conditional labels with CASE\n"
                    "SELECT\n"
                    "    id,\n"
                    "    title,\n"
                    "    CASE\n"
                    "        WHEN category_id = 1 THEN 'STEM Track'\n"
                    "        ELSE 'General Track'\n"
                    "    END AS track_label\n"
                    "FROM resources\n"
                    "WHERE status = 'active'\n"
                    "ORDER BY id;\n"
                ),
                "expected_output": (
                    "id  | title                 | track_label  \n"
                    "----+-----------------------+--------------\n"
                    "101 | 3D Printer Lab Access | STEM Track   \n"
                    "103 | Resume Review Session | General Track\n"
                    "104 | VR Development Kit    | STEM Track   "
                )
            },
            {
                "id": "sql_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Generates a sequence of numbers from 1 to 5 using a recursive Common Table Expression (CTE).",
                "explanation": "Generates a sequence of numbers from 1 to 5 using a recursive Common Table Expression (CTE).",
                "filename": "loop_sequence.sql",
                "code": (
                    "-- 4. Generating a sequence of steps (1 to 5) in SQLite\n"
                    "WITH RECURSIVE counter(step_number) AS (\n"
                    "    SELECT 1\n"
                    "    UNION ALL\n"
                    "    SELECT step_number + 1\n"
                    "    FROM counter\n"
                    "    WHERE step_number < 5\n"
                    ")\n"
                    "SELECT step_number, step_number * 10 AS points\n"
                    "FROM counter;\n"
                ),
                "expected_output": (
                    "step_number | points\n"
                    "------------+-------\n"
                    "1           | 10    \n"
                    "2           | 20    \n"
                    "3           | 30    \n"
                    "4           | 40    \n"
                    "5           | 50    "
                )
            },
            {
                "id": "sql_function",
                "category": "function",
                "title": "A simple function",
                "description": "Uses built-in SQL functions (COUNT, UPPER, and LENGTH) to transform text and summarize rows.",
                "explanation": "Uses built-in SQL functions (COUNT, UPPER, and LENGTH) to transform text and summarize rows.",
                "filename": "functions.sql",
                "code": (
                    "-- 5. Using built-in SQL functions (UPPER and LENGTH)\n"
                    "SELECT\n"
                    "    id,\n"
                    "    UPPER(title) AS upper_title,\n"
                    "    LENGTH(title) AS title_length\n"
                    "FROM resources\n"
                    "WHERE status = 'active'\n"
                    "ORDER BY id;\n"
                ),
                "expected_output": (
                    "id  | upper_title           | title_length\n"
                    "----+-----------------------+-------------\n"
                    "101 | 3D PRINTER LAB ACCESS | 21          \n"
                    "103 | RESUME REVIEW SESSION | 21          \n"
                    "104 | VR DEVELOPMENT KIT    | 18          "
                )
            },
            {
                "id": "sql_practical",
                "category": "practical",
                "title": "Practical example: Join resources with category names",
                "description": "Combines the resources and categories tables with INNER JOIN to display active campus items newest first.",
                "explanation": "Combines the resources and categories tables with INNER JOIN to display active campus items newest first.",
                "filename": "join_query.sql",
                "code": (
                    "-- 6. Practical query: Join two tables, filter active rows, and sort\n"
                    "SELECT\n"
                    "    r.id,\n"
                    "    r.title,\n"
                    "    c.name AS category_name,\n"
                    "    r.created_at\n"
                    "FROM resources r\n"
                    "INNER JOIN categories c ON r.category_id = c.id\n"
                    "WHERE r.status = 'active'\n"
                    "ORDER BY r.created_at DESC;\n"
                ),
                "expected_output": (
                    "id  | title                 | category_name   | created_at         \n"
                    "----+-----------------------+-----------------+--------------------\n"
                    "104 | VR Development Kit    | STEM & Robotics | 2026-10-20 09:30:00\n"
                    "103 | Resume Review Session | Career Services | 2026-10-15 14:00:00\n"
                    "101 | 3D Printer Lab Access | STEM & Robotics | 2026-10-01 10:00:00"
                )
            }
        ]
    },
    "html": {
        "id": "html",
        "name": "HTML & CSS",
        "icon": "🌐",
        "category": "Web Markup & Styling",
        "difficulty": "Beginner Friendly",
        "short_description": "Semantic markup and styling for modern web pages with immediate visual browser rendering.",
        "paradigm": "Declarative Markup & CSS Cascade",
        "starter_code": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>Student Page</title>\n  <style>\n    body { font-family: sans-serif; padding: 20px; }\n    .card { background: #FFFFFF; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; }\n  </style>\n</head>\n<body>\n  <div class=\"card\">\n    <h2>Hello, Web Learner!</h2>\n    <p>Edit this HTML and CSS to see the preview update.</p>\n  </div>\n</body>\n</html>\n",
        "file_ext": ".html",
        "monaco_lang": "html",
        "setup_guide": {
            "title": "Web Browser Preview Environment",
            "instructions": "HTML and CSS render directly inside your web browser's sandboxed preview frame.",
            "command": "Native Browser Engine"
        },
        "lessons": [
            {
                "id": "html_lesson_1",
                "title": "1. Semantic HTML Structure",
                "summary": "Build accessible documents using header, main, section, and article.",
                "explanation": "Semantic tags describe the meaning of content for screen readers and search engines.",
                "example": "<article class=\"profile-card\">\n  <header><h3>Student Moniker</h3></header>\n  <p>Enrolled in CS101</p>\n</article>"
            },
            {
                "id": "html_lesson_2",
                "title": "2. CSS Box Model & Colors",
                "summary": "Control margins, borders, padding, and content dimensions.",
                "explanation": "Every element on a web page is rendered as a rectangular box.",
                "example": ".box {\n  width: 240px;\n  padding: 16px;\n  border: 1px solid #E2E8F0;\n  margin-bottom: 12px;\n  border-radius: 6px;\n}"
            }
        ],
        "examples": [
            {
                "id": "html_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Displays a styled heading and welcome paragraph on a web page using HTML and CSS.",
                "explanation": "Displays a styled heading and welcome paragraph on a web page using HTML and CSS.",
                "filename": "hello.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 1. Hello, world in HTML & CSS -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    body { font-family: system-ui, sans-serif; padding: 18px; background: #F8FAFC; color: #0F172A; }\n"
                    "    h1 { color: #4F46E5; margin: 0 0 8px; font-size: 1.4rem; }\n"
                    "    p { margin: 0; color: #475569; }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <h1>Hello, World!</h1>\n"
                    "  <p>Welcome to HTML &amp; CSS in Code Wizard.</p>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Renders a blue 'Hello, World!' heading and welcome paragraph."
            },
            {
                "id": "html_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Defines reusable CSS custom properties (--primary-color and --card-padding) to style data badges.",
                "explanation": "Defines reusable CSS custom properties (--primary-color and --card-padding) to style data badges.",
                "filename": "css_variables.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 2. CSS Custom Properties (Variables) and structured data -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    :root {\n"
                    "      --brand-color: #0F9F82;\n"
                    "      --badge-bg: #ECFDF5;\n"
                    "      --card-padding: 14px;\n"
                    "    }\n"
                    "    body { font-family: system-ui, sans-serif; padding: 16px; }\n"
                    "    .data-card { border: 2px solid var(--brand-color); padding: var(--card-padding); border-radius: 8px; }\n"
                    "    .pill { display: inline-block; background: var(--badge-bg); color: var(--brand-color); padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <div class=\"data-card\">\n"
                    "    <span class=\"pill\">Track: Web Basics</span>\n"
                    "    <p style=\"margin: 8px 0 0;\">Reusable CSS variables keep colors and spacing consistent.</p>\n"
                    "  </div>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Renders a green-bordered card styled with CSS variables."
            },
            {
                "id": "html_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Uses CSS conditional state selectors (:checked) to change a task label when a checkbox is toggled.",
                "explanation": "Uses CSS conditional state selectors (:checked) to change a task label when a checkbox is toggled.",
                "filename": "condition_state.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 3. Conditional styling with the CSS :checked selector -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    body { font-family: system-ui, sans-serif; padding: 16px; }\n"
                    "    .todo-row { display: flex; align-items: center; gap: 10px; font-size: 1rem; }\n"
                    "    /* When the checkbox is checked, strike through the label text */\n"
                    "    input[type=\"checkbox\"]:checked + span {\n"
                    "      color: #0F9F82;\n"
                    "      text-decoration: line-through;\n"
                    "      font-weight: 700;\n"
                    "    }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <label class=\"todo-row\">\n"
                    "    <input type=\"checkbox\" checked>\n"
                    "    <span>Complete HTML &amp; CSS starter lesson</span>\n"
                    "  </label>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Interactive checkbox that updates the label style when checked."
            },
            {
                "id": "html_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Arranges a repeating collection of course items into an automatic responsive CSS Grid.",
                "explanation": "Arranges a repeating collection of course items into an automatic responsive CSS Grid.",
                "filename": "repeating_grid.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 4. Repeating list items styled with CSS Grid -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    body { font-family: system-ui, sans-serif; padding: 14px; }\n"
                    "    .step-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; list-style: none; padding: 0; margin: 0; }\n"
                    "    .step-item { background: #EEF2FF; border: 1px solid #C7D2FE; padding: 10px; border-radius: 6px; text-align: center; font-weight: 600; color: #3730A3; }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <ul class=\"step-grid\">\n"
                    "    <li class=\"step-item\">1. Read</li>\n"
                    "    <li class=\"step-item\">2. Code</li>\n"
                    "    <li class=\"step-item\">3. Test</li>\n"
                    "  </ul>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Displays 3 evenly spaced step cards in a row."
            },
            {
                "id": "html_function",
                "category": "function",
                "title": "A simple function",
                "description": "Uses CSS functions (calc() and linear-gradient()) to compute layout widths and background colors.",
                "explanation": "Uses CSS functions (calc() and linear-gradient()) to compute layout widths and background colors.",
                "filename": "css_functions.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 5. Using CSS functions: calc() and linear-gradient() -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    body { font-family: system-ui, sans-serif; padding: 16px; margin: 0; }\n"
                    "    .banner {\n"
                    "      width: calc(100% - 24px);\n"
                    "      padding: 12px;\n"
                    "      border-radius: 8px;\n"
                    "      background: linear-gradient(90deg, #4F46E5, #0F9F82);\n"
                    "      color: #FFFFFF;\n"
                    "      font-weight: 700;\n"
                    "    }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <div class=\"banner\">CSS functions compute sizes and gradients automatically.</div>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Renders a responsive gradient banner sized with calc()."
            },
            {
                "id": "html_practical",
                "category": "practical",
                "title": "Practical example: Student profile card",
                "description": "Builds a complete, accessible student profile card with a header, skill list, and action link.",
                "explanation": "Builds a complete, accessible student profile card with a header, skill list, and action link.",
                "filename": "profile_card.html",
                "is_html_preview": True,
                "code": (
                    "<!-- 6. Practical example: Accessible Student Profile Card -->\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "  <meta charset=\"UTF-8\">\n"
                    "  <style>\n"
                    "    body { font-family: system-ui, sans-serif; background: #F8FAFC; padding: 16px; margin: 0; }\n"
                    "    .profile-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; max-width: 340px; }\n"
                    "    .profile-card h2 { margin: 0 0 4px; font-size: 1.15rem; color: #1E293B; }\n"
                    "    .role { color: #64748B; font-size: 0.85rem; margin: 0 0 12px; }\n"
                    "    .skills { display: flex; gap: 6px; list-style: none; padding: 0; margin: 0; }\n"
                    "    .skills li { background: #EEF2FF; color: #4F46E5; padding: 4px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }\n"
                    "  </style>\n"
                    "</head>\n"
                    "<body>\n"
                    "  <article class=\"profile-card\">\n"
                    "    <h2>Jordan Rivera</h2>\n"
                    "    <p class=\"role\">First-Year Computer Science Student</p>\n"
                    "    <ul class=\"skills\">\n"
                    "      <li>HTML5</li>\n"
                    "      <li>CSS3</li>\n"
                    "      <li>Python</li>\n"
                    "    </ul>\n"
                    "  </article>\n"
                    "</body>\n"
                    "</html>\n"
                ),
                "expected_output": "Browser Preview: Renders a complete student profile card with skill badges."
            }
        ]
    },
    "javascript": {
        "id": "javascript",
        "name": "JavaScript",
        "icon": "⚡",
        "category": "Interpreted / JIT",
        "difficulty": "Beginner Friendly",
        "short_description": "The dynamic language of the modern web, powering interactive pages and Node.js applications.",
        "paradigm": "Event-driven, Functional, Prototype-based",
        "starter_code": "// Welcome to the JavaScript Workspace!\nfunction greet(name) {\n  return `Hello, ${name}!`;\n}\nconsole.log(greet('Student'));\n",
        "file_ext": ".js",
        "monaco_lang": "javascript",
        "setup_guide": {
            "title": "JavaScript Runtime (Node.js) Setup",
            "instructions": (
                "To run JavaScript programs on the host, install Node.js (LTS version) from https://nodejs.org "
                "and ensure 'node' is added to your system PATH."
            ),
            "command": "node --version"
        },
        "lessons": [
            {
                "id": "js_lesson_1",
                "title": "1. let, const & Arrow Functions",
                "summary": "Declare immutable and mutable variables and modern function syntax.",
                "explanation": "Prefer const by default. Use let only when values need reassignment.",
                "example": "const greeting = 'Welcome';\nconst square = (n) => n * n;\nconsole.log(`${greeting}! 4 squared is ${square(4)}`);"
            },
            {
                "id": "js_lesson_2",
                "title": "2. Array Higher-Order Methods",
                "summary": "Transform and filter lists with map, filter, and reduce.",
                "explanation": "Array methods return new arrays without mutating the source data.",
                "example": "const scores = [65, 88, 92, 74];\nconst passingScores = scores.filter(s => s >= 70);\nconsole.log(passingScores);"
            }
        ],
        "examples": [
            {
                "id": "js_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Prints a greeting to the console using JavaScript's console.log() function.",
                "explanation": "Prints a greeting to the console using JavaScript's console.log() function.",
                "filename": "hello.js",
                "code": (
                    "// 1. Hello, world in JavaScript\n"
                    "// console.log() prints a line of text to standard output.\n"
                    "console.log(\"Hello, World!\");\n"
                    "console.log(\"Welcome to JavaScript in Code Wizard.\");\n"
                ),
                "expected_output": "Hello, World!\nWelcome to JavaScript in Code Wizard."
            },
            {
                "id": "js_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Declares constants and mutable variables using const and let with template strings.",
                "explanation": "Declares constants and mutable variables using const and let with template strings.",
                "filename": "variables.js",
                "code": (
                    "// 2. Variables and basic data in JavaScript\n"
                    "const courseTitle = \"Web Development 101\";\n"
                    "let lessonsCompleted = 3;\n"
                    "const isPublished = true;\n\n"
                    "// Update a 'let' variable\n"
                    "lessonsCompleted += 1;\n\n"
                    "console.log(`Course: ${courseTitle}`);\n"
                    "console.log(`Lessons completed: ${lessonsCompleted}`);\n"
                    "console.log(`Published: ${isPublished}`);\n"
                ),
                "expected_output": (
                    "Course: Web Development 101\n"
                    "Lessons completed: 4\n"
                    "Published: true"
                )
            },
            {
                "id": "js_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Checks whether a title string meets minimum length rules using if, else if, and else.",
                "explanation": "Checks whether a title string meets minimum length rules using if, else if, and else.",
                "filename": "condition.js",
                "code": (
                    "// 3. Conditional checks with if / else if / else\n"
                    "const title = \"Robotics Club\";\n\n"
                    "if (title.length === 0) {\n"
                    "  console.log(\"Status: Title cannot be empty.\");\n"
                    "} else if (title.length < 3) {\n"
                    "  console.log(\"Status: Title is too short.\");\n"
                    "} else {\n"
                    "  console.log(`Status: '${title}' is valid (${title.length} chars).`);\n"
                    "}\n"
                ),
                "expected_output": "Status: 'Robotics Club' is valid (13 chars)."
            },
            {
                "id": "js_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Iterates through an array of scores with a for...of loop to calculate the sum.",
                "explanation": "Iterates through an array of scores with a for...of loop to calculate the sum.",
                "filename": "loop.js",
                "code": (
                    "// 4. Looping over an array in JavaScript\n"
                    "const quizScores = [18, 20, 17, 19];\n"
                    "let totalScore = 0;\n\n"
                    "for (const score of quizScores) {\n"
                    "  totalScore += score;\n"
                    "}\n\n"
                    "console.log(`Quizzes taken: ${quizScores.length}`);\n"
                    "console.log(`Total points: ${totalScore}`);\n"
                ),
                "expected_output": "Quizzes taken: 4\nTotal points: 74"
            },
            {
                "id": "js_function",
                "category": "function",
                "title": "A simple function",
                "description": "Creates a function that converts Celsius temperatures to Fahrenheit and prints the result.",
                "explanation": "Creates a function that converts Celsius temperatures to Fahrenheit and prints the result.",
                "filename": "function.js",
                "code": (
                    "// 5. A simple reusable function in JavaScript\n"
                    "function celsiusToFahrenheit(celsius) {\n"
                    "  return (celsius * 9) / 5 + 32;\n"
                    "}\n\n"
                    "console.log(`0C = ${celsiusToFahrenheit(0)}F`);\n"
                    "console.log(`25C = ${celsiusToFahrenheit(25)}F`);\n"
                ),
                "expected_output": "0C = 32F\n25C = 77F"
            },
            {
                "id": "js_practical",
                "category": "practical",
                "title": "Practical example: Validate and format form input",
                "description": "Trims extra whitespace from user input and returns a validation summary object.",
                "explanation": "Trims extra whitespace from user input and returns a validation summary object.",
                "filename": "validate_input.js",
                "code": (
                    "// 6. Practical example: Trimming and validating user input\n"
                    "function validateTitle(rawTitle) {\n"
                    "  const cleaned = String(rawTitle || \"\").trim();\n"
                    "  if (cleaned.length < 3) {\n"
                    "    return { valid: false, message: \"Must be at least 3 characters.\" };\n"
                    "  }\n"
                    "  return { valid: true, title: cleaned };\n"
                    "}\n\n"
                    "console.log(JSON.stringify(validateTitle(\"   \")));\n"
                    "console.log(JSON.stringify(validateTitle(\"  Campus Hackathon  \")));\n"
                ),
                "expected_output": (
                    "{\"valid\":false,\"message\":\"Must be at least 3 characters.\"}\n"
                    "{\"valid\":true,\"title\":\"Campus Hackathon\"}"
                )
            }
        ]
    },
    "java": {
        "id": "java",
        "name": "Java",
        "icon": "☕",
        "category": "Compiled (JVM)",
        "difficulty": "Intermediate",
        "short_description": "Strongly typed, object-oriented language widely taught in university introductory CS curricula.",
        "paradigm": "Object-Oriented, Class-based, Strictly Typed",
        "starter_code": "// Welcome to the Java Workspace!\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Java Learner!\");\n    }\n}\n",
        "file_ext": ".java",
        "monaco_lang": "java",
        "setup_guide": {
            "title": "Java Development Kit (JDK) Setup",
            "instructions": (
                "Java requires javac (compiler) and java (JVM runtime). "
                "Install OpenJDK from https://adoptium.net and add its bin folder to your system PATH."
            ),
            "command": "javac -version && java -version"
        },
        "lessons": [
            {
                "id": "java_lesson_1",
                "title": "1. Classes, Methods & Types",
                "summary": "Every Java program is structured around classes with strictly typed variables.",
                "explanation": "Primitive types include int, double, boolean, and char. Classes begin with uppercase.",
                "example": "public class Calculator {\n    public static int add(int a, int b) {\n        return a + b;\n    }\n}"
            },
            {
                "id": "java_lesson_2",
                "title": "2. Arrays & Boundary Checking",
                "summary": "Fixed-size arrays and preventing ArrayIndexOutOfBoundsException.",
                "explanation": "Arrays in Java have a fixed length. Valid indices are 0 to array.length - 1.",
                "example": "int[] numbers = {10, 20, 30};\nfor (int i = 0; i < numbers.length; i++) {\n    System.out.println(\"Item: \" + numbers[i]);\n}"
            }
        ],
        "examples": [
            {
                "id": "java_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Defines a Main class and main() entry point that prints a greeting with System.out.println.",
                "explanation": "Defines a Main class and main() entry point that prints a greeting with System.out.println.",
                "filename": "Main.java",
                "code": (
                    "// 1. Hello, world in Java\n"
                    "public class Main {\n"
                    "    public static void main(String[] args) {\n"
                    "        System.out.println(\"Hello, World!\");\n"
                    "        System.out.println(\"Welcome to Java in Code Wizard.\");\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": "Hello, World!\nWelcome to Java in Code Wizard."
            },
            {
                "id": "java_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Declares strongly typed int, double, boolean, and String variables in Java.",
                "explanation": "Declares strongly typed int, double, boolean, and String variables in Java.",
                "filename": "VariablesDemo.java",
                "code": (
                    "// 2. Strongly typed variables in Java\n"
                    "public class VariablesDemo {\n"
                    "    public static void main(String[] args) {\n"
                    "        String student = \"Liam\";\n"
                    "        int credits = 16;\n"
                    "        double gpa = 3.75;\n"
                    "        boolean enrolled = true;\n\n"
                    "        System.out.println(\"Student: \" + student);\n"
                    "        System.out.println(\"Credits: \" + credits);\n"
                    "        System.out.println(\"GPA: \" + gpa);\n"
                    "        System.out.println(\"Enrolled: \" + enrolled);\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": (
                    "Student: Liam\n"
                    "Credits: 16\n"
                    "GPA: 3.75\n"
                    "Enrolled: true"
                )
            },
            {
                "id": "java_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Uses an if-else statement in Java to check whether an exam score passes the threshold.",
                "explanation": "Uses an if-else statement in Java to check whether an exam score passes the threshold.",
                "filename": "ConditionDemo.java",
                "code": (
                    "// 3. Conditional logic in Java\n"
                    "public class ConditionDemo {\n"
                    "    public static void main(String[] args) {\n"
                    "        int examScore = 82;\n\n"
                    "        if (examScore >= 70) {\n"
                    "            System.out.println(\"Score \" + examScore + \": Passed!\");\n"
                    "        } else {\n"
                    "            System.out.println(\"Score \" + examScore + \": Keep practicing.\");\n"
                    "        }\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": "Score 82: Passed!"
            },
            {
                "id": "java_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Loops over an integer array with a standard for loop and prints each element.",
                "explanation": "Loops over an integer array with a standard for loop and prints each element.",
                "filename": "LoopDemo.java",
                "code": (
                    "// 4. Looping through an array in Java\n"
                    "public class LoopDemo {\n"
                    "    public static void main(String[] args) {\n"
                    "        int[] steps = {10, 20, 30, 40};\n"
                    "        int sum = 0;\n\n"
                    "        for (int i = 0; i < steps.length; i++) {\n"
                    "            sum += steps[i];\n"
                    "            System.out.println(\"Index \" + i + \": \" + steps[i]);\n"
                    "        }\n"
                    "        System.out.println(\"Total: \" + sum);\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": (
                    "Index 0: 10\n"
                    "Index 1: 20\n"
                    "Index 2: 30\n"
                    "Index 3: 40\n"
                    "Total: 100"
                )
            },
            {
                "id": "java_function",
                "category": "function",
                "title": "A simple function",
                "description": "Defines a static helper method that returns the maximum of two integers.",
                "explanation": "Defines a static helper method that returns the maximum of two integers.",
                "filename": "FunctionDemo.java",
                "code": (
                    "// 5. Defining a static method (function) in Java\n"
                    "public class FunctionDemo {\n"
                    "    public static int maxOfTwo(int a, int b) {\n"
                    "        return (a > b) ? a : b;\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        System.out.println(\"Max of 14 and 9: \" + maxOfTwo(14, 9));\n"
                    "        System.out.println(\"Max of 3 and 21: \" + maxOfTwo(3, 21));\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": "Max of 14 and 9: 14\nMax of 3 and 21: 21"
            },
            {
                "id": "java_practical",
                "category": "practical",
                "title": "Practical example: Safe grade average calculator",
                "description": "Computes the average of valid exam scores between 0 and 100 while guarding against empty arrays.",
                "explanation": "Computes the average of valid exam scores between 0 and 100 while guarding against empty arrays.",
                "filename": "GradeAverage.java",
                "code": (
                    "// 6. Practical example: Safe Grade Average Calculator in Java\n"
                    "public class GradeAverage {\n"
                    "    public static double computeAverage(int[] grades) {\n"
                    "        if (grades == null || grades.length == 0) {\n"
                    "            return 0.0;\n"
                    "        }\n"
                    "        int sum = 0;\n"
                    "        int count = 0;\n"
                    "        for (int g : grades) {\n"
                    "            if (g >= 0 && g <= 100) {\n"
                    "                sum += g;\n"
                    "                count++;\n"
                    "            }\n"
                    "        }\n"
                    "        return count > 0 ? (double) sum / count : 0.0;\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        int[] scores = {80, 90, 100, -5};\n"
                    "        System.out.println(\"Valid average: \" + computeAverage(scores));\n"
                    "    }\n"
                    "}\n"
                ),
                "expected_output": "Valid average: 90.0"
            }
        ]
    },
    "c": {
        "id": "c",
        "name": "C",
        "icon": "⚙️",
        "category": "Compiled (Native)",
        "difficulty": "Intermediate",
        "short_description": "Foundational procedural systems language emphasizing memory control, pointers, and hardware architecture.",
        "paradigm": "Procedural, Imperative, Structured",
        "starter_code": "// Welcome to the C Workspace!\n#include <stdio.h>\n\nint main(void) {\n    printf(\"Hello, C Learner!\\n\");\n    return 0;\n}\n",
        "file_ext": ".c",
        "monaco_lang": "c",
        "setup_guide": {
            "title": "C Compiler (GCC / Clang) Setup",
            "instructions": (
                "C requires GCC or Clang. On Windows, install w64devkit or MinGW-w64 from winlibs.com, "
                "or install Clang via LLVM, and add 'gcc' to your system PATH."
            ),
            "command": "gcc --version"
        },
        "lessons": [
            {
                "id": "c_lesson_1",
                "title": "1. Pointers & Memory Basics",
                "summary": "Understand memory addresses and dereferencing.",
                "explanation": "A pointer stores the memory address of another variable using the & and * operators.",
                "example": "int val = 42;\nint *ptr = &val;\nprintf(\"Value: %d, Address: %p\\n\", *ptr, (void*)ptr);"
            },
            {
                "id": "c_lesson_2",
                "title": "2. Array Bounds & Off-by-One",
                "summary": "Guarding against buffer overflows and memory corruption.",
                "explanation": "C does not perform bounds checking at runtime. Accessing arr[size] leads to undefined behavior.",
                "example": "int arr[3] = {1, 2, 3};\nfor (int i = 0; i < 3; i++) {\n    printf(\"%d\\n\", arr[i]);\n}"
            }
        ],
        "examples": [
            {
                "id": "c_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Includes stdio.h and prints a line of text from main() using printf().",
                "explanation": "Includes stdio.h and prints a line of text from main() using printf().",
                "filename": "hello.c",
                "code": (
                    "// 1. Hello, world in C\n"
                    "#include <stdio.h>\n\n"
                    "int main(void) {\n"
                    "    printf(\"Hello, World!\\n\");\n"
                    "    printf(\"Welcome to C programming in Code Wizard.\\n\");\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Hello, World!\nWelcome to C programming in Code Wizard."
            },
            {
                "id": "c_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Formats and prints integer, floating-point, and character variables with printf format specifiers.",
                "explanation": "Formats and prints integer, floating-point, and character variables with printf format specifiers.",
                "filename": "variables.c",
                "code": (
                    "// 2. Variables and format specifiers in C\n"
                    "#include <stdio.h>\n\n"
                    "int main(void) {\n"
                    "    int labs_done = 5;\n"
                    "    double score = 94.5;\n"
                    "    char section = 'A';\n\n"
                    "    printf(\"Section: %c\\n\", section);\n"
                    "    printf(\"Labs completed: %d\\n\", labs_done);\n"
                    "    printf(\"Average score: %.1f\\n\", score);\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": (
                    "Section: A\n"
                    "Labs completed: 5\n"
                    "Average score: 94.5"
                )
            },
            {
                "id": "c_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Checks sensor temperature thresholds using if, else if, and else blocks.",
                "explanation": "Checks sensor temperature thresholds using if, else if, and else blocks.",
                "filename": "condition.c",
                "code": (
                    "// 3. Conditional branching in C\n"
                    "#include <stdio.h>\n\n"
                    "int main(void) {\n"
                    "    int temperature_c = 22;\n\n"
                    "    if (temperature_c > 30) {\n"
                    "        printf(\"Status: Cooling required (%d C)\\n\", temperature_c);\n"
                    "    } else if (temperature_c < 15) {\n"
                    "        printf(\"Status: Heating required (%d C)\\n\", temperature_c);\n"
                    "    } else {\n"
                    "        printf(\"Status: Normal operating range (%d C)\\n\", temperature_c);\n"
                    "    }\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Status: Normal operating range (22 C)"
            },
            {
                "id": "c_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Iterates through a fixed-size C array within strict index bounds (0 to count - 1).",
                "explanation": "Iterates through a fixed-size C array within strict index bounds (0 to count - 1).",
                "filename": "loop.c",
                "code": (
                    "// 4. Safe array iteration with a for loop in C\n"
                    "#include <stdio.h>\n\n"
                    "int main(void) {\n"
                    "    int readings[4] = {12, 18, 24, 30};\n"
                    "    int count = 4;\n"
                    "    int total = 0;\n\n"
                    "    for (int i = 0; i < count; i++) {\n"
                    "        total += readings[i];\n"
                    "        printf(\"Reading[%d] = %d\\n\", i, readings[i]);\n"
                    "    }\n"
                    "    printf(\"Sum = %d\\n\", total);\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": (
                    "Reading[0] = 12\n"
                    "Reading[1] = 18\n"
                    "Reading[2] = 24\n"
                    "Reading[3] = 30\n"
                    "Sum = 84"
                )
            },
            {
                "id": "c_function",
                "category": "function",
                "title": "A simple function",
                "description": "Defines a function that computes the perimeter of a rectangle and calls it from main().",
                "explanation": "Defines a function that computes the perimeter of a rectangle and calls it from main().",
                "filename": "function.c",
                "code": (
                    "// 5. Writing and calling a function in C\n"
                    "#include <stdio.h>\n\n"
                    "int rectangle_perimeter(int width, int height) {\n"
                    "    return 2 * (width + height);\n"
                    "}\n\n"
                    "int main(void) {\n"
                    "    int result = rectangle_perimeter(6, 4);\n"
                    "    printf(\"Perimeter of 6x4 rectangle: %d\\n\", result);\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Perimeter of 6x4 rectangle: 20"
            },
            {
                "id": "c_practical",
                "category": "practical",
                "title": "Practical example: Safe array average with boundary check",
                "description": "Computes the floating-point mean of an integer array while guarding against zero-length inputs.",
                "explanation": "Computes the floating-point mean of an integer array while guarding against zero-length inputs.",
                "filename": "safe_average.c",
                "code": (
                    "// 6. Practical example: Safe array average in C\n"
                    "#include <stdio.h>\n\n"
                    "double calculate_average(const int scores[], int count) {\n"
                    "    if (scores == NULL || count <= 0) {\n"
                    "        return 0.0;\n"
                    "    }\n"
                    "    long sum = 0;\n"
                    "    for (int i = 0; i < count; i++) {\n"
                    "        sum += scores[i];\n"
                    "    }\n"
                    "    return (double)sum / (double)count;\n"
                    "}\n\n"
                    "int main(void) {\n"
                    "    int ratings[3] = {4, 5, 3};\n"
                    "    printf(\"Average rating: %.2f\\n\", calculate_average(ratings, 3));\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Average rating: 4.00"
            }
        ]
    },
    "cpp": {
        "id": "cpp",
        "name": "C++",
        "icon": "🚀",
        "category": "Compiled (Native)",
        "difficulty": "Advanced",
        "short_description": "High-performance language pairing direct memory access with object-oriented abstractions and STL containers.",
        "paradigm": "Multi-paradigm: Procedural, Functional, Generic, OOP",
        "starter_code": "// Welcome to the C++ Workspace!\n#include <iostream>\n#include <vector>\n\nint main() {\n    std::cout << \"Hello, C++ Learner!\" << std::endl;\n    return 0;\n}\n",
        "file_ext": ".cpp",
        "monaco_lang": "cpp",
        "setup_guide": {
            "title": "C++ Compiler (G++ / Clang++) Setup",
            "instructions": (
                "C++ requires G++ or Clang++. On Windows, install MinGW-w64 (with g++) or Visual Studio C++ build tools "
                "and ensure 'g++' is available on your system PATH."
            ),
            "command": "g++ --version"
        },
        "lessons": [
            {
                "id": "cpp_lesson_1",
                "title": "1. Standard Template Library (vector)",
                "summary": "Dynamic contiguous arrays with std::vector.",
                "explanation": "std::vector handles dynamic memory management safely compared to raw C-style arrays.",
                "example": "#include <vector>\nstd::vector<int> nums = {10, 20, 30};\nnums.push_back(40);"
            },
            {
                "id": "cpp_lesson_2",
                "title": "2. Binary Search & Midpoint Arithmetic",
                "summary": "Preventing integer overflow when calculating midpoint.",
                "explanation": "Calculating mid as left + (right - left) / 2 prevents 32-bit integer overflow.",
                "example": "int mid = left + (right - left) / 2;"
            }
        ],
        "examples": [
            {
                "id": "cpp_hello",
                "category": "hello",
                "title": "Hello, world",
                "description": "Outputs text streams to standard output using std::cout from the <iostream> library.",
                "explanation": "Outputs text streams to standard output using std::cout from the <iostream> library.",
                "filename": "hello.cpp",
                "code": (
                    "// 1. Hello, world in C++\n"
                    "#include <iostream>\n\n"
                    "int main() {\n"
                    "    std::cout << \"Hello, World!\" << std::endl;\n"
                    "    std::cout << \"Welcome to C++ in Code Wizard.\" << std::endl;\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Hello, World!\nWelcome to C++ in Code Wizard."
            },
            {
                "id": "cpp_variables",
                "category": "variables",
                "title": "Variables and basic data",
                "description": "Uses std::string, int, double, and bool variables and prints them with std::cout.",
                "explanation": "Uses std::string, int, double, and bool variables and prints them with std::cout.",
                "filename": "variables.cpp",
                "code": (
                    "// 2. Variables and basic data types in C++\n"
                    "#include <iostream>\n"
                    "#include <string>\n\n"
                    "int main() {\n"
                    "    std::string track = \"Algorithms\";\n"
                    "    int solved_problems = 7;\n"
                    "    double accuracy = 96.4;\n"
                    "    bool verified = true;\n\n"
                    "    std::cout << \"Track: \" << track << \"\\n\";\n"
                    "    std::cout << \"Solved: \" << solved_problems << \"\\n\";\n"
                    "    std::cout << \"Accuracy: \" << accuracy << \"%\\n\";\n"
                    "    std::cout << \"Verified: \" << (verified ? \"yes\" : \"no\") << \"\\n\";\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": (
                    "Track: Algorithms\n"
                    "Solved: 7\n"
                    "Accuracy: 96.4%\n"
                    "Verified: yes"
                )
            },
            {
                "id": "cpp_condition",
                "category": "condition",
                "title": "A condition",
                "description": "Evaluates a student's point total with if, else if, and else to assign a badge tier.",
                "explanation": "Evaluates a student's point total with if, else if, and else to assign a badge tier.",
                "filename": "condition.cpp",
                "code": (
                    "// 3. Conditional statements in C++\n"
                    "#include <iostream>\n\n"
                    "int main() {\n"
                    "    int xp = 240;\n\n"
                    "    if (xp >= 300) {\n"
                    "        std::cout << \"Tier: Gold Badge\\n\";\n"
                    "    } else if (xp >= 150) {\n"
                    "        std::cout << \"Tier: Silver Badge\\n\";\n"
                    "    } else {\n"
                    "        std::cout << \"Tier: Bronze Badge\\n\";\n"
                    "    }\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Tier: Silver Badge"
            },
            {
                "id": "cpp_loop",
                "category": "loop",
                "title": "A loop",
                "description": "Iterates over a dynamic std::vector<int> using a range-based for loop.",
                "explanation": "Iterates over a dynamic std::vector<int> using a range-based for loop.",
                "filename": "loop.cpp",
                "code": (
                    "// 4. Looping through a std::vector in C++\n"
                    "#include <iostream>\n"
                    "#include <vector>\n\n"
                    "int main() {\n"
                    "    std::vector<int> values = {5, 10, 15, 20};\n"
                    "    int sum = 0;\n\n"
                    "    for (int v : values) {\n"
                    "        sum += v;\n"
                    "        std::cout << \"Value: \" << v << \"\\n\";\n"
                    "    }\n"
                    "    std::cout << \"Total sum: \" << sum << \"\\n\";\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": (
                    "Value: 5\n"
                    "Value: 10\n"
                    "Value: 15\n"
                    "Value: 20\n"
                    "Total sum: 50"
                )
            },
            {
                "id": "cpp_function",
                "category": "function",
                "title": "A simple function",
                "description": "Writes a function that squares an integer and calls it for multiple values.",
                "explanation": "Writes a function that squares an integer and calls it for multiple values.",
                "filename": "function.cpp",
                "code": (
                    "// 5. Defining and calling a function in C++\n"
                    "#include <iostream>\n\n"
                    "int square(int n) {\n"
                    "    return n * n;\n"
                    "}\n\n"
                    "int main() {\n"
                    "    std::cout << \"6 squared = \" << square(6) << \"\\n\";\n"
                    "    std::cout << \"9 squared = \" << square(9) << \"\\n\";\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "6 squared = 36\n9 squared = 81"
            },
            {
                "id": "cpp_practical",
                "category": "practical",
                "title": "Practical example: Binary search in a sorted vector",
                "description": "Searches a sorted std::vector<int> in O(log n) time and prints the index of the target.",
                "explanation": "Searches a sorted std::vector<int> in O(log n) time and prints the index of the target.",
                "filename": "binary_search.cpp",
                "code": (
                    "// 6. Practical example: Binary search in C++\n"
                    "#include <iostream>\n"
                    "#include <vector>\n\n"
                    "int binarySearch(const std::vector<int>& nums, int target) {\n"
                    "    int left = 0;\n"
                    "    int right = static_cast<int>(nums.size()) - 1;\n"
                    "    while (left <= right) {\n"
                    "        int mid = left + (right - left) / 2;\n"
                    "        if (nums[mid] == target) return mid;\n"
                    "        if (nums[mid] < target) left = mid + 1;\n"
                    "        else right = mid - 1;\n"
                    "    }\n"
                    "    return -1;\n"
                    "}\n\n"
                    "int main() {\n"
                    "    std::vector<int> sorted_ids = {101, 204, 309, 412, 518};\n"
                    "    int index = binarySearch(sorted_ids, 309);\n"
                    "    std::cout << \"Found 309 at index: \" << index << \"\\n\";\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "expected_output": "Found 309 at index: 2"
            }
        ]
    }
}


def _enrich_examples_for_language(lang_id: str, examples: List[Dict[str, Any]], rt_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    is_avail = bool(rt_info.get("available"))
    enriched = []
    for ex in examples:
        item = dict(ex)
        item["language"] = lang_id
        item["runnable"] = is_avail
        item["status_label"] = "Available" if is_avail else "Not installed"
        item["mode_label"] = "Runnable" if is_avail else "View only"
        enriched.append(item)
    return enriched


def get_all_languages_summary(challenges_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Returns summary list of all languages with real-time host toolchain status
    and challenge counts for the Language Home Page catalog.
    """
    challenges = challenges_list or []
    catalog = []

    for lang_id, data in LANGUAGES_CATALOG.items():
        rt_info = check_language_runtime(lang_id)

        matching_challenges = sum(
            1 for ch in challenges
            if (ch.get("execution_language") or "python").lower() == lang_id
        )

        catalog.append({
            "id": data["id"],
            "name": data["name"],
            "icon": data["icon"],
            "category": data["category"],
            "difficulty": data["difficulty"],
            "short_description": data["short_description"],
            "paradigm": data["paradigm"],
            "available": rt_info["available"],
            "status_label": rt_info.get("status_label", "Available" if rt_info["available"] else "Not installed"),
            "mode_label": rt_info.get("mode_label", "Runnable" if rt_info["available"] else "View only"),
            "runtime_label": rt_info.get("runtime_label", data["name"]),
            "version": rt_info.get("version"),
            "toolchain_status": "Available" if rt_info["available"] else "Not installed",
            "runtime_description": rt_info.get("description", "Execution unavailable"),
            "file_ext": data["file_ext"],
            "challenges_count": matching_challenges,
            "lessons_count": len(data.get("lessons", [])),
            "examples_count": len(data.get("examples", [])),
        })

    return catalog


def get_language_details(lang_id: str, challenges_list: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Returns detailed roadmap, lessons, examples, and setup for a specific language."""
    norm_id = lang_id.lower().strip()
    if norm_id not in LANGUAGES_CATALOG:
        return None

    data = dict(LANGUAGES_CATALOG[norm_id])
    rt_info = check_language_runtime(norm_id)
    data["available"] = rt_info["available"]
    data["status_label"] = rt_info.get("status_label", "Available" if rt_info["available"] else "Not installed")
    data["mode_label"] = rt_info.get("mode_label", "Runnable" if rt_info["available"] else "View only")
    data["runtime_label"] = rt_info.get("runtime_label", data["name"])
    data["version"] = rt_info.get("version")
    data["toolchain_status"] = "Available" if rt_info["available"] else "Not installed"
    data["runtime_description"] = rt_info.get("description", "Execution unavailable")
    data["examples"] = _enrich_examples_for_language(norm_id, data.get("examples", []), rt_info)

    # Only show labs whose source code is actually written for this language.
    challenges = challenges_list or []
    lang_challenges = [
        ch for ch in challenges
        if (ch.get("execution_language") or "python").lower() == norm_id
    ]
    difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    lang_challenges.sort(key=lambda ch: (
        difficulty_order.get((ch.get("difficulty") or "").lower(), 3),
        (ch.get("title") or "").lower()
    ))

    data["challenges"] = lang_challenges
    return data


def get_all_examples_catalog() -> List[Dict[str, Any]]:
    """Returns the built-in Code Examples library for all 7 catalog languages with runtime availability."""
    result = []
    for lang_id, data in LANGUAGES_CATALOG.items():
        rt_info = check_language_runtime(lang_id)
        result.append({
            "id": data["id"],
            "name": data["name"],
            "icon": data["icon"],
            "file_ext": data["file_ext"],
            "monaco_lang": data["monaco_lang"],
            "available": rt_info["available"],
            "status_label": rt_info.get("status_label", "Available" if rt_info["available"] else "Not installed"),
            "mode_label": rt_info.get("mode_label", "Runnable" if rt_info["available"] else "View only"),
            "runtime_label": rt_info.get("runtime_label", data["name"]),
            "version": rt_info.get("version"),
            "runtime_description": rt_info.get("description", ""),
            "setup_guide": data.get("setup_guide", rt_info.get("setup_guide", {})),
            "examples": _enrich_examples_for_language(lang_id, data.get("examples", []), rt_info),
        })
    return result


PROGRAM_LANGUAGE_ALIASES = {
    "py": "python",
    "python3": "python",
    "sqlite": "sql",
    "sqlite3": "sql",
    "html/css": "html",
    "html & css": "html",
    "html_css": "html",
    "css": "html",
    "web": "html",
    "js": "javascript",
    "node": "javascript",
    "c++": "cpp",
    "cplusplus": "cpp",
}


def normalize_program_language_id(lang_id: str) -> str:
    """Normalizes a language identifier and returns canonical catalog key or empty string if invalid."""
    raw = (lang_id or "").strip().lower()
    norm = PROGRAM_LANGUAGE_ALIASES.get(raw, raw)
    return norm if norm in LANGUAGES_CATALOG else ""


def get_student_assigned_programs(conn, student_id: str) -> List[Dict[str, Any]]:
    """
    Returns the learning programs assigned to `student_id` from `student_programs`,
    enriched with language catalog metadata, lab counts, progress percentage, and status.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT language_id, assigned_by, assigned_at
        FROM student_programs
        WHERE student_id = ?
        ORDER BY assigned_at ASC, language_id ASC
    """, (student_id,))
    assigned_rows = cursor.fetchall()

    # Load active challenges grouped by execution_language
    cursor.execute("""
        SELECT id, title, execution_language, xp_reward
        FROM challenges
        WHERE active = 1
    """)
    all_challenges = [dict(r) for r in cursor.fetchall()]

    # Load student's completed challenges
    cursor.execute("""
        SELECT challenge_id
        FROM challenge_progress
        WHERE student_id = ?
    """, (student_id,))
    completed_ids = {r["challenge_id"] for r in cursor.fetchall()}

    # Load student's attempts per challenge
    cursor.execute("""
        SELECT challenge_id, COUNT(*) as cnt
        FROM attempts
        WHERE student_id = ?
        GROUP BY challenge_id
    """, (student_id,))
    attempt_counts_by_ch = {r["challenge_id"]: int(r["cnt"] or 0) for r in cursor.fetchall()}

    catalog_order = list(LANGUAGES_CATALOG.keys())
    programs: List[Dict[str, Any]] = []
    for row in assigned_rows:
        lang_id = normalize_program_language_id(row["language_id"])
        if not lang_id or lang_id not in LANGUAGES_CATALOG:
            continue
        meta = LANGUAGES_CATALOG[lang_id]
        lang_challenges = [
            ch for ch in all_challenges
            if (ch.get("execution_language") or "python").lower() == lang_id
        ]
        total_labs = len(lang_challenges)
        completed_labs = sum(1 for ch in lang_challenges if ch["id"] in completed_ids)
        attempts_count = sum(attempt_counts_by_ch.get(ch["id"], 0) for ch in lang_challenges)

        if total_labs > 0:
            progress_percent = round((completed_labs / total_labs) * 100)
            if completed_labs >= total_labs:
                status = "Completed"
            elif completed_labs > 0 or attempts_count > 0:
                status = "In Progress"
            else:
                status = "Assigned"
        else:
            progress_percent = 0
            status = "Assigned"

        programs.append({
            "language_id": lang_id,
            "id": lang_id,
            "name": meta["name"],
            "icon": meta["icon"],
            "category": meta["category"],
            "difficulty": meta["difficulty"],
            "short_description": meta["short_description"],
            "lessons_count": len(meta.get("lessons", [])),
            "examples_count": len(meta.get("examples", [])),
            "total_labs": total_labs,
            "completed_labs": completed_labs,
            "attempts_count": attempts_count,
            "progress_percent": progress_percent,
            "status": status,
            "assigned_by": row["assigned_by"],
            "assigned_at": row["assigned_at"],
        })

    programs.sort(key=lambda p: catalog_order.index(p["language_id"]) if p["language_id"] in catalog_order else 99)
    return programs

