"""
Language Registry & Beginner Curriculum Engine for CodeMirror 2.0
Defines supported programming languages, beginner lessons, syntax examples,
and setup guides. Designed to be easily expandable.
"""

from typing import Dict, Any, List
from app.runtimes import get_available_runtimes, check_language_runtime

LANGUAGES_CATALOG: Dict[str, Dict[str, Any]] = {
    "python": {
        "id": "python",
        "name": "Python",
        "icon": "🐍",
        "category": "Interpreted",
        "difficulty": "Beginner Friendly",
        "short_description": "Clean, readable syntax ideal for learning fundamental logic, data manipulation, and backend APIs.",
        "paradigm": "Multi-paradigm: Object-Oriented, Functional, Procedural",
        "starter_code": "# Welcome to the Python Lab!\n# Write your code below:\n\ndef main():\n    print('Hello, Python Learner!')\n\nif __name__ == '__main__':\n    main()\n",
        "file_ext": ".py",
        "monaco_lang": "python",
        "setup_guide": {
            "title": "Python 3 Setup",
            "instructions": (
                "Python is installed and active on this server. "
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
                "title": "List Filtering Pattern",
                "description": "Filtering items from a collection without mutating original data.",
                "code": "numbers = [12, -4, 25, 0, -8, 19]\npositive_numbers = [n for n in numbers if n > 0]\nprint('Positives:', positive_numbers)"
            },
            {
                "title": "Safe Dictionary Lookup",
                "description": "Using .get() with default fallbacks to avoid KeyError.",
                "code": "user = {'username': 'coder42', 'role': 'student'}\nstatus = user.get('status', 'active')\nprint(f'User status: {status}')"
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
        "starter_code": "-- Welcome to the SQL Database Lab!\n-- Write your SELECT query below:\n\nSELECT * FROM resources LIMIT 5;\n",
        "file_ext": ".sql",
        "monaco_lang": "sql",
        "setup_guide": {
            "title": "SQLite Engine Setup",
            "instructions": (
                "SQLite is built directly into Python's standard library and operates completely in-memory on this server. "
                "No external database server installation is required."
            ),
            "command": "python -c 'import sqlite3; print(sqlite3.sqlite_version)'"
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
                "title": "Aggregate Function Query",
                "description": "Counting records and calculating averages per category.",
                "code": "SELECT category_id, COUNT(*) AS total_items\nFROM resources\nGROUP BY category_id\nHAVING COUNT(*) > 1;"
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
        "starter_code": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>Student Lab</title>\n  <style>\n    body { font-family: sans-serif; padding: 20px; }\n    .card { background: #FFFFFF; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; }\n  </style>\n</head>\n<body>\n  <div class=\"card\">\n    <h2>Hello, Web Learner!</h2>\n    <p>Build your accessible user interface here.</p>\n  </div>\n</body>\n</html>\n",
        "file_ext": ".html",
        "monaco_lang": "html",
        "setup_guide": {
            "title": "Web Browser Environment",
            "instructions": "HTML and CSS render natively in your web browser with isolated iframe sandboxing.",
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
                "title": "Flexbox Layout Card",
                "description": "Aligning icon and text neatly side-by-side.",
                "code": "<div style=\"display: flex; align-items: center; gap: 12px;\">\n  <span style=\"font-size: 2rem;\">🚀</span>\n  <div>\n    <strong>Coding Mission</strong>\n    <p style=\"margin:0; color:#64748B;\">Ready to start</p>\n  </div>\n</div>"
            }
        ]
    },
    "javascript": {
        "id": "javascript",
        "name": "JavaScript",
        "icon": "⚡",
        "category": "Interpreted / JIT",
        "difficulty": "Beginner Friendly",
        "short_description": "The dynamic language of the modern web, powering client-side interaction and Node.js servers.",
        "paradigm": "Event-driven, Functional, Prototype-based",
        "starter_code": "// Welcome to the JavaScript Lab!\nfunction greet(name) {\n    return `Hello, ${name}!`;\n}\nconsole.log(greet('Student'));\n",
        "file_ext": ".js",
        "monaco_lang": "javascript",
        "setup_guide": {
            "title": "Node.js Toolchain Setup",
            "instructions": (
                "To execute JavaScript natively on the server host, install Node.js (LTS version) from https://nodejs.org. "
                "Ensure node.exe is added to your system PATH."
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
                "title": "Object Destructuring",
                "description": "Unpacking properties from JavaScript objects safely.",
                "code": "const config = { theme: 'light', xp: 450 };\nconst { theme, xp } = config;\nconsole.log(`Current theme: ${theme}, XP: ${xp}`);"
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
        "starter_code": "// Welcome to the Java Lab!\npublic class Solution {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, Java Learner!\");\n    }\n}\n",
        "file_ext": ".java",
        "monaco_lang": "java",
        "setup_guide": {
            "title": "Java Development Kit (JDK) Setup",
            "instructions": (
                "Java requires javac (compiler) and java (runtime). "
                "Download OpenJDK from https://adoptium.net and ensure the bin directory is added to your system PATH."
            ),
            "command": "javac -version"
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
                "title": "Defensive Method Validation",
                "description": "Guarding against null arguments in Java.",
                "code": "public static double safeAverage(int[] values) {\n    if (values == null || values.length == 0) return 0.0;\n    int sum = 0;\n    for (int v : values) sum += v;\n    return (double) sum / values.length;\n}"
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
        "starter_code": "// Welcome to the C Systems Lab!\n#include <stdio.h>\n\nint main(void) {\n    printf(\"Hello, C Systems Learner!\\n\");\n    return 0;\n}\n",
        "file_ext": ".c",
        "monaco_lang": "c",
        "setup_guide": {
            "title": "GCC / Clang Compiler Setup",
            "instructions": (
                "C requires GCC or Clang. On Windows, install w64devkit or MinGW-w64 from winlibs.com, "
                "or install Clang via LLVM. Ensure gcc.exe is on your system PATH."
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
                "title": "Safe Array Loop Pattern",
                "description": "Iterating through an array strictly with strict boundary checks.",
                "code": "float calculate_mean(const int *data, size_t count) {\n    if (data == NULL || count == 0) return 0.0f;\n    long sum = 0;\n    for (size_t i = 0; i < count; i++) {\n        sum += data[i];\n    }\n    return (float)sum / (float)count;\n}"
            }
        ]
    },
    "cpp": {
        "id": "cpp",
        "name": "C++",
        "icon": "🚀",
        "category": "Compiled (Native)",
        "difficulty": "Advanced",
        "short_description": "High-performance language pairing direct memory access with object-oriented abstractions and STL algorithms.",
        "paradigm": "Multi-paradigm: Procedural, Functional, Generic, OOP",
        "starter_code": "// Welcome to the C++ Algorithms Lab!\n#include <iostream>\n#include <vector>\n\nint main() {\n    std::cout << \"Hello, C++ Learner!\" << std::endl;\n    return 0;\n}\n",
        "file_ext": ".cpp",
        "monaco_lang": "cpp",
        "setup_guide": {
            "title": "G++ / Clang++ Toolchain Setup",
            "instructions": (
                "C++ requires G++ or Clang++. On Windows, install MinGW-w64 with GCC/G++ or Visual Studio C++ build tools. "
                "Ensure g++.exe is accessible from your command prompt."
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
                "title": "Logarithmic Search Function",
                "description": "Standard binary search implementation template.",
                "code": "int binarySearch(const std::vector<int>& arr, int target) {\n    int left = 0, right = static_cast<int>(arr.size()) - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (arr[mid] == target) return mid;\n        if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}"
            }
        ]
    }
}

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
            "version": rt_info.get("version"),
            "toolchain_status": "Ready to Run" if rt_info["available"] else rt_info.get("description", "Execution unavailable"),
            "runtime_description": rt_info.get("description", "Execution unavailable"),
            "file_ext": data["file_ext"],
            "challenges_count": matching_challenges,
            "lessons_count": len(data.get("lessons", []))
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
    data["version"] = rt_info.get("version")
    data["toolchain_status"] = "Active & Configured on Host" if rt_info["available"] else rt_info.get("description", "Execution unavailable")
    data["runtime_description"] = rt_info.get("description", "Execution unavailable")
    
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
