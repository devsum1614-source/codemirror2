"""
Seeds the challenges catalog and initial pseudonymous student profiles for Student Coding Quest.
Stores private test cases that are NEVER exposed to the frontend browser.
Supports multiple languages with rigorous runtime checks and concept recaps.
"""

import json
import sqlite3
from app.database import get_db

CHALLENGES = [
    {
        "id": "ch_py_first_steps",
        "title": "Your First Function: Double a Number",
        "skill_tag": "python-basics",
        "execution_language": "python",
        "difficulty": "Beginner",
        "prompt": (
            "Write a function named double_value(number) that returns twice the number it receives. "
            "Think about what should happen for zero, a negative number, and a decimal."
        ),
        "starter_code": "def double_value(number):\n    # Write the function body yourself.\n    pass\n",
        "xp_reward": 25,
        "active": 1,
        "concept_recap": "A function receives an input, performs an operation, and returns a result. Testing zero, negative, and decimal inputs helps confirm the behavior is consistent.",
        "related_challenge_id": "ch_py_filter",
        "tests": json.dumps({
            "challenge_id": "ch_py_first_steps",
            "tests": [
                {"type": "function_call", "name": "zero", "function": "double_value", "args": [0], "expected": 0},
                {"type": "function_call", "name": "positive", "function": "double_value", "args": [6], "expected": 12},
                {"type": "function_call", "name": "negative", "function": "double_value", "args": [-3], "expected": -6},
                {"type": "function_call", "name": "decimal", "function": "double_value", "args": [2.5], "expected": 5.0}
            ]
        })
    },
    {
        "id": "ch_web_validator",
        "title": "Prevent Empty & Whitespace Resource Titles",
        "skill_tag": "web-validation",
        "execution_language": "python",
        "difficulty": "Beginner",
        "prompt": (
            "Write a robust validation function 'validate_resource_title(title)' "
            "that trims leading/trailing whitespace, ensures length is between 3 and 50 characters, and returns: "
            "{'valid': True/False, 'error': str or None}. "
            "Empty or whitespace-only strings must return {'valid': False, 'error': 'Title cannot be empty.'}."
        ),
        "starter_code": """def validate_resource_title(title: str) -> dict:
    \"\"\"
    Validates a resource title before submission.
    @param title: User input title string
    @return: {'valid': bool, 'error': str | None}
    \"\"\"
    # TODO: Fix validation bug. Currently allows empty or whitespace-only strings!
    if not title:
        return {"valid": True, "error": None}  # BUG: should be invalid!
    
    return {
        "valid": True,
        "error": None
    }
""",
        "xp_reward": 50,
        "active": 1,
        "concept_recap": "Client-side validation provides immediate feedback to users and prevents malformed payloads before they reach the backend API. Trimming whitespace is vital because whitespace-only strings evaluate to a positive length unless stripped.",
        "related_challenge_id": "ch_py_filter",
        "tests": json.dumps({
            "challenge_id": "ch_web_validator",
            "tests": [
                {
                    "type": "function_call",
                    "name": "empty_string_rejection",
                    "function": "validate_resource_title",
                    "args": [""],
                    "expected": {"valid": False, "error": "Title cannot be empty."}
                },
                {
                    "type": "function_call",
                    "name": "whitespace_only_trimming",
                    "function": "validate_resource_title",
                    "args": ["     "],
                    "expected": {"valid": False, "error": "Title cannot be empty."}
                },
                {
                    "type": "function_call",
                    "name": "minimum_length_requirement",
                    "function": "validate_resource_title",
                    "args": ["AI"],
                    "expected": {"valid": False, "error": "Title must be at least 3 characters."}
                },
                {
                    "type": "function_call",
                    "name": "valid_title_acceptance",
                    "function": "validate_resource_title",
                    "args": ["Robotics Lab Workshop"],
                    "expected": {"valid": True, "error": None}
                }
            ]
        })
    },
    {
        "id": "ch_sql_search",
        "title": "SQL Resource Search with Category Joins",
        "skill_tag": "sql-databases",
        "execution_language": "sql",
        "difficulty": "Intermediate",
        "prompt": (
            "Write a SQL query selecting resource id, title, category name as 'category_name', and created_at. "
            "Join 'resources' with 'categories' on category_id, filter by status = 'active', and order by created_at DESC."
        ),
        "starter_code": """-- Write your SQL query below:
SELECT 
    resources.id, 
    resources.title
FROM resources;
""",
        "xp_reward": 75,
        "active": 1,
        "concept_recap": "Relational databases connect foreign keys with INNER JOIN clauses to eliminate duplicate data. Using ORDER BY created_at DESC ensures students always see the newest submissions first.",
        "related_challenge_id": "ch_py_filter",
        "tests": json.dumps({
            "challenge_id": "ch_sql_search",
            "tests": [
                {
                    "type": "sql_query",
                    "name": "category_join_and_filter",
                    "setup_sql": """
                        CREATE TABLE categories (id INT PRIMARY KEY, name TEXT);
                        CREATE TABLE resources (id INT PRIMARY KEY, title TEXT, category_id INT, status TEXT, created_at TEXT);
                        INSERT INTO categories VALUES (1, 'STEM & Robotics'), (2, 'Arts & Media');
                        INSERT INTO resources VALUES 
                            (101, '3D Printer Lab Access', 1, 'active', '2026-10-01 10:00:00'),
                            (102, 'Archived Camera', 2, 'archived', '2026-09-01 12:00:00'),
                            (103, 'VR Development Kit', 1, 'active', '2026-10-20 09:30:00');
                    """,
                    "required_cols": ["id", "title", "category_name", "created_at"],
                    "expected_rows": [
                        [103, "VR Development Kit", "STEM & Robotics", "2026-10-20 09:30:00"],
                        [101, "3D Printer Lab Access", "STEM & Robotics", "2026-10-01 10:00:00"]
                    ]
                }
            ]
        })
    },
    {
        "id": "ch_py_filter",
        "title": "REST API Endpoint: Category & Status Filtering",
        "skill_tag": "python-backend",
        "execution_language": "python",
        "difficulty": "Intermediate",
        "prompt": (
            "Implement a function 'filter_resources(items, category=None, status=\"active\")' that filters "
            "a list of resource dicts. If status is not in ['active', 'archived', 'all'], raise a "
            "ValueError('Invalid status filter'). If category is specified, match case-insensitively. "
            "Ensure returned list does not mutate the original data."
        ),
        "starter_code": """from typing import List, Dict, Optional

VALID_STATUSES = {"active", "archived", "all"}

def filter_resources(
    items: List[Dict], 
    category: Optional[str] = None, 
    status: str = "active"
) -> List[Dict]:
    \"\"\"
    Filters resources by category and status.
    Raises ValueError('Invalid status filter') if status is not valid.
    \"\"\"
    return items  # BUG: returns everything unfiltered!
""",
        "xp_reward": 75,
        "active": 1,
        "concept_recap": "Defensive API parameter validation protects your server from malformed queries. Case-insensitive normalization using .lower() or .casefold() ensures search queries match reliably across platforms.",
        "related_challenge_id": "ch_sql_search",
        "tests": json.dumps({
            "challenge_id": "ch_py_filter",
            "tests": [
                {
                    "type": "function_call",
                    "name": "invalid_status_exception",
                    "function": "filter_resources",
                    "args": [[{"id": 1, "status": "active"}]],
                    "kwargs": {"status": "unsupported"},
                    "expect_exception": "ValueError"
                },
                {
                    "type": "function_call",
                    "name": "default_active_status",
                    "function": "filter_resources",
                    "args": [[
                        {"id": 1, "title": "A", "status": "active"},
                        {"id": 2, "title": "B", "status": "archived"}
                    ]],
                    "kwargs": {},
                    "expected": [{"id": 1, "title": "A", "status": "active"}]
                },
                {
                    "type": "function_call",
                    "name": "case_insensitive_category",
                    "function": "filter_resources",
                    "args": [[
                        {"id": 1, "title": "Lab", "category": "STEM", "status": "active"},
                        {"id": 2, "title": "Paint", "category": "Arts", "status": "active"}
                    ]],
                    "kwargs": {"category": "stem", "status": "all"},
                    "expected": [{"id": 1, "title": "Lab", "category": "STEM", "status": "active"}]
                }
            ]
        })
    },
    {
        "id": "ch_c_bounds",
        "title": "Guard Empty Lists Before Averaging",
        "skill_tag": "python-basics",
        "execution_language": "python",
        "difficulty": "Beginner",
        "prompt": (
            "Implement the Python function 'calculate_average_rating(scores)' to return the average of a list. "
            "If scores is None or empty, return 0.0. Think through how to avoid dividing by zero."
        ),
        "starter_code": """from typing import List, Optional

def calculate_average_rating(scores: Optional[List[int]]) -> float:
    \"\"\"
    Calculates average attendee feedback rating.
    Safely returns 0.0 if scores is empty or None.
    \"\"\"
    # BUG: Division by zero when scores is empty!
    sum_val = 0.0
    for score in scores:
        sum_val += score
    return sum_val / len(scores)
""",
        "xp_reward": 50,
        "active": 1,
        "concept_recap": "Python lists can be empty, so check the input before dividing by its length. A clear guard handles both None and an empty list.",
        "related_challenge_id": "ch_cpp_binary_search",
        "tests": json.dumps({
            "challenge_id": "ch_c_bounds",
            "tests": [
                {
                    "type": "function_call",
                    "name": "empty_scores_zero_guard",
                    "function": "calculate_average_rating",
                    "args": [[]],
                    "expected": 0.0
                },
                {
                    "type": "function_call",
                    "name": "none_scores_zero_guard",
                    "function": "calculate_average_rating",
                    "args": [None],
                    "expected": 0.0
                },
                {
                    "type": "function_call",
                    "name": "accurate_average_calculation",
                    "function": "calculate_average_rating",
                    "args": [[4, 5]],
                    "expected": 4.5
                }
            ]
        })
    },
    {
        "id": "ch_cpp_binary_search",
        "title": "Build Binary Search on a Sorted List",
        "skill_tag": "python-algorithms",
        "execution_language": "python",
        "difficulty": "Intermediate",
        "prompt": (
            "Implement 'binary_search_resource_id(ids, target)' in Python. Return the zero-based index of "
            "target in a sorted list of unique integers, or -1 if it is missing. Narrow the search range "
            "on each comparison so the algorithm runs in logarithmic time."
        ),
        "starter_code": """from typing import List

def binary_search_resource_id(ids: List[int], target: int) -> int:
    \"\"\"
    Performs logarithmic binary search on sorted IDs list.
    Returns 0-based index if found, or -1 if target is absent.
    \"\"\"
    # TODO: Implement O(log N) binary search
    return -1
""",
        "xp_reward": 100,
        "active": 1,
        "concept_recap": "Binary search works on sorted lists and halves the remaining search range after each comparison, giving O(log N) time.",
        "related_challenge_id": "ch_c_bounds",
        "tests": json.dumps({
            "challenge_id": "ch_cpp_binary_search",
            "tests": [
                {
                    "type": "function_call",
                    "name": "find_middle_element",
                    "function": "binary_search_resource_id",
                    "args": [[10, 20, 30, 40, 50], 30],
                    "expected": 2
                },
                {
                    "type": "function_call",
                    "name": "find_first_element",
                    "function": "binary_search_resource_id",
                    "args": [[10, 20, 30, 40, 50], 10],
                    "expected": 0
                },
                {
                    "type": "function_call",
                    "name": "find_last_element",
                    "function": "binary_search_resource_id",
                    "args": [[10, 20, 30, 40, 50], 50],
                    "expected": 4
                },
                {
                    "type": "function_call",
                    "name": "absent_element_returns_minus_one",
                    "function": "binary_search_resource_id",
                    "args": [[10, 20, 30, 40, 50], 99],
                    "expected": -1
                },
                {
                    "type": "function_call",
                    "name": "empty_list_returns_minus_one",
                    "function": "binary_search_resource_id",
                    "args": [[], 42],
                    "expected": -1
                }
            ]
        })
    },
    {
        "id": "ch_java_grade_calculator",
        "title": "Calculate a Grade Average in Python",
        "skill_tag": "python-basics",
        "execution_language": "python",
        "difficulty": "Beginner",
        "prompt": (
            "Write the Python function 'calculate_grade_average(scores)' to calculate the average of a "
            "list of test scores. Return 0.0 for None or an empty list."
        ),
        "starter_code": """def calculate_grade_average(scores):
    \"\"\"
    Calculates grade average.
    Guards against empty or None scores returning 0.0.
    \"\"\"
    # TODO: Implement safe average calculation
    return 0.0
""",
        "xp_reward": 60,
        "active": 1,
        "concept_recap": "Check for None and empty lists before using len(scores) as a divisor. This avoids runtime errors and makes the function predictable. ",
        "related_challenge_id": "ch_py_filter",
        "tests": json.dumps({
            "challenge_id": "ch_java_grade_calculator",
            "tests": [
                {
                    "type": "function_call",
                    "name": "empty_scores_guard",
                    "function": "calculate_grade_average",
                    "args": [[]],
                    "expected": 0.0
                },
                {
                    "type": "function_call",
                    "name": "valid_scores_average",
                    "function": "calculate_grade_average",
                    "args": [[80, 90, 100]],
                    "expected": 90.0
                }
            ]
        })
    },
    {
        "id": "ch_html_profile_card",
        "title": "Accessible Student Profile Card",
        "skill_tag": "web-markup",
        "execution_language": "html",
        "difficulty": "Beginner",
        "prompt": (
            "Construct a clean, accessible HTML student card using semantic elements. "
            "Must include an <article> container, a <header> with an <h2> heading, and a <p> description."
        ),
        "starter_code": "<!-- Build your semantic profile card from scratch. -->\n",
        "xp_reward": 50,
        "active": 1,
        "concept_recap": "Semantic HTML tags (<article>, <header>, <section>) provide semantic meaning for accessibility assistive technology and search engines.",
        "related_challenge_id": "ch_web_validator",
        "tests": json.dumps({
            "challenge_id": "ch_html_profile_card",
            "tests": [
                {
                    "name": "semantic_card_structure",
                    "required_tags": ["article", "header", "h2", "p"]
                }
            ]
        })
    }
]

def seed_quest_data():
    conn = get_db()
    cursor = conn.cursor()

    # Seed challenges with private tests and concept recaps
    for ch in CHALLENGES:
        cursor.execute("""
            INSERT INTO challenges (id, title, skill_tag, execution_language, difficulty, prompt, starter_code, tests, xp_reward, active, concept_recap, related_challenge_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                skill_tag=excluded.skill_tag,
                execution_language=excluded.execution_language,
                difficulty=excluded.difficulty,
                prompt=excluded.prompt,
                starter_code=excluded.starter_code,
                tests=excluded.tests,
                xp_reward=excluded.xp_reward,
                active=excluded.active,
                concept_recap=excluded.concept_recap,
                related_challenge_id=excluded.related_challenge_id
        """, (
            ch["id"], ch["title"], ch["skill_tag"], ch.get("execution_language", "python"), ch["difficulty"],
            ch["prompt"], ch["starter_code"], ch["tests"], ch["xp_reward"], ch["active"],
            ch.get("concept_recap"), ch.get("related_challenge_id")
        ))

    conn.commit()
    conn.close()
    print("Challenges seeded successfully with concept recaps.")

if __name__ == "__main__":
    seed_quest_data()
