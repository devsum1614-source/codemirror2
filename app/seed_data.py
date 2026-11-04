import json
import sqlite3
from app.database import get_db

MISSIONS = [
    {
        "mission_id": "web-validate-title",
        "title": "Prevent Empty & Invalid Resource Titles",
        "track": "Web Development",
        "language": "javascript",
        "difficulty": "Beginner",
        "file_path": "campus_portal/frontend/validator.js",
        "scenario": (
            "Students submitting resources on the Campus Resource Portal are accidentally creating blank "
            "or 1-character entries. Write a robust client validation function 'validateResourceTitle(title)' "
            "that trims whitespace, ensures length is between 3 and 50 characters, and returns an object: "
            "{ valid: boolean, error: string | null }."
        ),
        "impact_summary": (
            "Impacts: Form submission handler (portal.js), Error banner DOM element (#title-error), "
            "and prevents invalid payloads from reaching POST /api/resources."
        ),
        "starter_code": """/**
 * Validates a resource title before submission.
 * @param {string} title - The input title from the user
 * @returns {{ valid: boolean, error: string | null }}
 */
function validateResourceTitle(title) {
  // TODO: Fix validation bug. Currently allows empty or whitespace-only strings!
  if (!title) {
    return { valid: true, error: null }; // BUG: should be invalid!
  }
  
  // Return validation result
  return {
    valid: true,
    error: null
  };
}

// Export for runner
if (typeof module !== 'undefined') {
  module.exports = { validateResourceTitle };
}
""",
        "solution_code": """function validateResourceTitle(title) {
  if (typeof title !== 'string') {
    return { valid: false, error: 'Title must be a text string.' };
  }
  const trimmed = title.trim();
  if (trimmed.length === 0) {
    return { valid: false, error: 'Title cannot be empty.' };
  }
  if (trimmed.length < 3) {
    return { valid: false, error: 'Title must be at least 3 characters long.' };
  }
  if (trimmed.length > 50) {
    return { valid: false, error: 'Title cannot exceed 50 characters.' };
  }
  return { valid: true, error: null };
}

if (typeof module !== 'undefined') {
  module.exports = { validateResourceTitle };
}
""",
        "acceptance_criteria": (
            "- Rejects null, undefined, or empty strings with an informative error message.\n"
            "- Trims whitespace so '   ' is treated as empty.\n"
            "- Enforces minimum length of 3 characters.\n"
            "- Enforces maximum length of 50 characters.\n"
            "- Returns { valid: true, error: null } for valid titles like 'Robotics Club Workshop'."
        ),
        "rubric_json": json.dumps({
            "functional_correctness": 50,
            "edge_case_handling": 15,
            "testing_practice": 15,
            "code_quality": 10,
            "technical_explanation": 10
        })
    },
    {
        "mission_id": "sql-resource-search",
        "title": "SQL Resource Search with Category Joins",
        "track": "SQL Databases",
        "language": "sql",
        "difficulty": "Intermediate",
        "file_path": "campus_portal/database/search_query.sql",
        "scenario": (
            "The Campus Portal needs to display all active resources alongside their category name, "
            "newest first. Write a SQL query selecting resource id, title, category_name, and created_at. "
            "Join the 'resources' table with the 'categories' table on category_id, filter by status = 'active', "
            "and order by created_at DESC."
        ),
        "impact_summary": (
            "Impacts: SQLite database tables ('resources', 'categories'), Backend endpoint "
            "GET /api/catalog, and Portal home feed."
        ),
        "starter_code": """-- Write your SQL query below to select:
-- resources.id, resources.title, categories.name AS category_name, resources.created_at
-- FROM resources
-- JOIN categories ON ...
-- WHERE resources.status = 'active'
-- ORDER BY resources.created_at DESC;

SELECT 
    resources.id, 
    resources.title
FROM resources;
""",
        "solution_code": """SELECT 
    resources.id, 
    resources.title, 
    categories.name AS category_name, 
    resources.created_at
FROM resources
INNER JOIN categories ON resources.category_id = categories.id
WHERE resources.status = 'active'
ORDER BY resources.created_at DESC;
""",
        "acceptance_criteria": (
            "- Selects resources.id, resources.title, categories.name AS category_name, and resources.created_at.\n"
            "- Correctly joins resources with categories using foreign key category_id.\n"
            "- Only includes rows where resources.status = 'active'.\n"
            "- Results are sorted newest first (created_at DESC)."
        ),
        "rubric_json": json.dumps({
            "functional_correctness": 50,
            "edge_case_handling": 15,
            "testing_practice": 15,
            "code_quality": 10,
            "technical_explanation": 10
        })
    },
    {
        "mission_id": "py-api-filter",
        "title": "REST API Endpoint: Category & Status Filtering",
        "track": "Python Backend",
        "language": "python",
        "difficulty": "Intermediate",
        "file_path": "campus_portal/backend/api_filter.py",
        "scenario": (
            "Implement a function 'filter_resources(items, category=None, status='active')' that filters "
            "a list of resource dicts. If status is provided but not in ['active', 'archived', 'all'], "
            "raise a ValueError('Invalid status filter'). If category is specified, match case-insensitively. "
            "Ensure returned list does not mutate the original data."
        ),
        "impact_summary": (
            "Impacts: FastAPI routing layer in app.py, Catalog search UI, and JSON response serialization."
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
    # TODO: Validate status parameter
    # TODO: Apply category filter (case-insensitive)
    # TODO: Apply status filter ('all' includes all statuses)
    return items  # BUG: returns everything unfiltered!
""",
        "solution_code": """from typing import List, Dict, Optional

VALID_STATUSES = {"active", "archived", "all"}

def filter_resources(
    items: List[Dict], 
    category: Optional[str] = None, 
    status: str = "active"
) -> List[Dict]:
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status filter")
        
    filtered = []
    cat_lower = category.lower().strip() if category else None
    
    for item in items:
        # Check status
        if status != "all" and item.get("status") != status:
            continue
        # Check category
        if cat_lower and item.get("category", "").lower().strip() != cat_lower:
            continue
        filtered.append(dict(item))
        
    return filtered
""",
        "acceptance_criteria": (
            "- Raises ValueError('Invalid status filter') for invalid statuses like 'deleted' or 'pending'.\n"
            "- Correctly filters items by status ('active', 'archived') or returns both if 'all'.\n"
            "- Matches category case-insensitively ('STEM' matches 'stem').\n"
            "- Returns a copy of matching items without mutating inputs."
        ),
        "rubric_json": json.dumps({
            "functional_correctness": 50,
            "edge_case_handling": 15,
            "testing_practice": 15,
            "code_quality": 10,
            "technical_explanation": 10
        })
    },
    {
        "mission_id": "c-off-by-one",
        "title": "Fix Memory & Array Bounds in Event Logger",
        "track": "C / Systems",
        "language": "c",
        "difficulty": "Beginner-Intermediate",
        "file_path": "campus_portal/core/attendee_processor.c",
        "scenario": (
            "The campus check-in system has a critical off-by-one error in 'calculate_average_rating'. "
            "It iterates <= count instead of < count, accessing memory past the allocated array. "
            "Also, if count is 0, it should safely return 0.0 instead of dividing by zero. "
            "Fix the bounds and zero-check."
        ),
        "impact_summary": (
            "Impacts: Memory safety, Segmentation fault prevention, Accurate event feedback aggregation."
        ),
        "starter_code": """#include <stdio.h>

/**
 * Calculates the average score of attendees.
 * @param scores Array of attendee rating scores (1 to 5)
 * @param count Number of elements in scores array
 * @return Average rating, or 0.0 if count is 0
 */
double calculate_average_rating(const int scores[], int count) {
    // BUG 1: Does not handle count <= 0 safely (division by zero)
    // BUG 2: Loop condition i <= count accesses scores[count], which is out of bounds!
    double sum = 0.0;
    for (int i = 0; i <= count; i++) {
        sum += scores[i];
    }
    return sum / count;
}
""",
        "solution_code": """#include <stdio.h>

double calculate_average_rating(const int scores[], int count) {
    if (count <= 0 || scores == NULL) {
        return 0.0;
    }
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += scores[i];
    }
    return sum / (double)count;
}
""",
        "acceptance_criteria": (
            "- Safely returns 0.0 when count is 0 or negative.\n"
            "- Loop terminates strictly at i < count to prevent out-of-bounds memory read.\n"
            "- Returns accurate floating point average (e.g., [4, 5] -> 4.5).\n"
            "- Handles null pointer check gracefully."
        ),
        "rubric_json": json.dumps({
            "functional_correctness": 50,
            "edge_case_handling": 15,
            "testing_practice": 15,
            "code_quality": 10,
            "technical_explanation": 10
        })
    },
    {
        "mission_id": "cpp-dsa-search",
        "title": "Implement Binary Search for Fast Resource ID Lookup",
        "track": "C++ / DSA",
        "language": "cpp",
        "difficulty": "Intermediate",
        "file_path": "campus_portal/core/resource_catalog.cpp",
        "scenario": (
            "Students need to lookup resource IDs in O(log N) time. Implement 'binarySearchResourceId' "
            "given a sorted std::vector<int> and a target ID. Return the zero-based index if found, "
            "or -1 if not found. Prevent integer overflow when computing the midpoint (use left + (right - left) / 2)."
        ),
        "impact_summary": (
            "Impacts: Catalog indexing speed, algorithmic efficiency, prevents integer overflow on large datasets."
        ),
        "starter_code": """#include <vector>

/**
 * Performs binary search on a sorted vector of IDs.
 * @param ids Sorted ascending vector of unique resource IDs
 * @param target ID to search for
 * @return Zero-based index if found, -1 if not found
 */
int binarySearchResourceId(const std::vector<int>& ids, int target) {
    // TODO: Implement O(log N) binary search
    // Make sure to avoid integer overflow when calculating mid!
    return -1; // Unimplemented
}
""",
        "solution_code": """#include <vector>

int binarySearchResourceId(const std::vector<int>& ids, int target) {
    int left = 0;
    int right = static_cast<int>(ids.size()) - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (ids[mid] == target) {
            return mid;
        } else if (ids[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}
""",
        "acceptance_criteria": (
            "- Returns correct index for elements located at start, middle, and end.\n"
            "- Returns -1 when target is absent or vector is empty.\n"
            "- Uses left + (right - left) / 2 to avoid overflow.\n"
            "- Operates in O(log N) logarithmic iterations."
        ),
        "rubric_json": json.dumps({
            "functional_correctness": 50,
            "edge_case_handling": 15,
            "testing_practice": 15,
            "code_quality": 10,
            "technical_explanation": 10
        })
    }
]

def seed_database():
    conn = get_db()
    cursor = conn.cursor()

    # Create default user if not exists
    cursor.execute("SELECT user_id FROM users WHERE email = 'alex.vance@campus.edu'")
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Alex Vance", "alex.vance@campus.edu")
        )
        user_id = cursor.lastrowid
    else:
        user_id = user["user_id"]

    # Create default project
    cursor.execute("SELECT project_id FROM projects WHERE title = 'Campus Resource Portal'")
    proj = cursor.fetchone()
    if not proj:
        cursor.execute(
            "INSERT INTO projects (user_id, title, language_set) VALUES (?, ?, ?)",
            (user_id, "Campus Resource Portal", "HTML, CSS, JavaScript, SQL, Python, C/C++")
        )
        project_id = cursor.lastrowid
    else:
        project_id = proj["project_id"]

    # Insert or update missions
    for m in MISSIONS:
        cursor.execute("""
            INSERT INTO missions (
                mission_id, title, track, language, difficulty, scenario, 
                starter_code, file_path, acceptance_criteria, impact_summary, 
                solution_code, rubric_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(mission_id) DO UPDATE SET
                title=excluded.title,
                track=excluded.track,
                language=excluded.language,
                difficulty=excluded.difficulty,
                scenario=excluded.scenario,
                starter_code=excluded.starter_code,
                file_path=excluded.file_path,
                acceptance_criteria=excluded.acceptance_criteria,
                impact_summary=excluded.impact_summary,
                solution_code=excluded.solution_code,
                rubric_json=excluded.rubric_json
        """, (
            m["mission_id"], m["title"], m["track"], m["language"], m["difficulty"],
            m["scenario"], m["starter_code"], m["file_path"], m["acceptance_criteria"],
            m["impact_summary"], m["solution_code"], m["rubric_json"]
        ))

        # Check project_missions record
        cursor.execute(
            "SELECT id FROM project_missions WHERE project_id = ? AND mission_id = ?",
            (project_id, m["mission_id"])
        )
        pm = cursor.fetchone()
        if not pm:
            cursor.execute(
                "INSERT INTO project_missions (project_id, mission_id, status, student_code) VALUES (?, ?, 'in_progress', ?)",
                (project_id, m["mission_id"], m["starter_code"])
            )

    conn.commit()
    conn.close()
    print("Database seeded with sample user, project, and 5 missions.")

if __name__ == "__main__":
    seed_database()
