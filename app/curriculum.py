"""
Beginner course curriculum for Code Wizard.

Seven courses (C, C++, Java, Python, JavaScript, TypeScript, HTML/CSS), each with the
same ordered path of eight lessons:

    1. Introduction            5. Conditions
    2. Hello, world!           6. Loops
    3. Variables               7. Functions
    4. Input and output        8. Small project

This module is pure content. It is additive: it does not touch LANGUAGES_CATALOG in
app/languages.py (the existing language pages, examples and labs keep working as-is).
Learner progress (not started / in progress / completed) is stored in the
`lesson_progress` table and served by app/routes_courses.py.
"""

from textwrap import dedent
from typing import Any, Dict, List, Optional

LESSON_STATUSES = ("not_started", "in_progress", "completed")

# Lesson order and titles shared by every course.
LESSON_PATH = [
    ("intro", "Introduction"),
    ("hello", "Hello, world!"),
    ("variables", "Variables"),
    ("io", "Input and output"),
    ("conditions", "Conditions"),
    ("loops", "Loops"),
    ("functions", "Functions"),
    ("project", "Small project"),
]


def _code(text: str) -> str:
    return dedent(text).strip("\n") + "\n"


def _lesson(
    topic: str,
    summary: str,
    explanation: str,
    example: str,
    expected_output: str,
    exercise_prompt: str,
    exercise_starter: str,
    sample_input: str = "",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    default_title = dict(LESSON_PATH)[topic]
    return {
        "topic": topic,
        "title": title or default_title,
        "summary": summary,
        "explanation": explanation.strip(),
        "example": _code(example),
        "expected_output": expected_output.strip("\n"),
        "sample_input": sample_input,
        "exercise": {"prompt": exercise_prompt, "starter": _code(exercise_starter)},
    }


# ---------------------------------------------------------------------------
# PYTHON
# ---------------------------------------------------------------------------
_PYTHON = [
    _lesson(
        "intro",
        "See what a Python program is and how it runs.",
        "A program is a list of instructions. Python reads your file from the top to the bottom and runs one line at a time. "
        "Lines that start with # are comments: Python ignores them, so you can leave notes for yourself.",
        """
        # Python runs this file from top to bottom.
        print("I am learning Python!")
        """,
        "I am learning Python!",
        "Change the message so it says your own name.",
        """
        print("I am learning Python!")
        """,
    ),
    _lesson(
        "hello",
        "Write and run your first program.",
        "print() shows text on the screen. Text must be inside quotation marks. Each print() call starts a new line.",
        """
        print("Hello, world!")
        """,
        "Hello, world!",
        "Print Hello, world! on the first line and Welcome to Python on the second line.",
        """
        # Add a second print() below
        print("Hello, world!")
        """,
    ),
    _lesson(
        "variables",
        "Store values with names.",
        "A variable is a named box that holds a value. Use = to store a value. Python works out the type for you: "
        "text (str), whole numbers (int), decimals (float) and True/False (bool).",
        """
        name = "Sam"
        age = 12
        height = 1.5
        is_student = True
        print(name, "is", age, "years old")
        print("Height:", height)
        print("Student?", is_student)
        """,
        "Sam is 12 years old\nHeight: 1.5\nStudent? True",
        "Make variables for your favourite food and your lucky number, then print them in one sentence.",
        """
        food = "pizza"
        # Add a lucky_number variable and print a sentence using both
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "input() waits for the user to type a line and gives it back as text. Use int() to turn text into a number "
        "before doing maths. In the workspace, type your input in the Custom Input box before you press Run.",
        """
        name = input("What is your name? ")
        print("Nice to meet you,", name)
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a number, then print the number multiplied by 2. Hint: wrap input() in int().",
        """
        number = int(input("Pick a number: "))
        # Print number * 2
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if checks a condition. If it is True, the indented block runs. elif adds another check and else runs when "
        "nothing above matched. Python uses indentation (4 spaces) to mark which lines belong to the block.",
        """
        score = 72
        if score >= 90:
            print("Grade A")
        elif score >= 70:
            print("Grade B")
        else:
            print("Keep practicing")
        """,
        "Grade B",
        "Change score to 95, then to 40, and check the output each time.",
        """
        score = 72
        if score >= 90:
            print("Grade A")
        elif score >= 70:
            print("Grade B")
        else:
            print("Keep practicing")
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "A for loop repeats once for each item in a range or list. range(1, 4) gives 1, 2 and 3 (the end number is "
        "not included). A while loop keeps going as long as its condition is True, so make sure something inside "
        "it changes, or it will never stop.",
        """
        for i in range(1, 4):
            print("Count", i)

        total = 0
        n = 1
        while n <= 3:
            total = total + n
            n = n + 1
        print("Total", total)
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to print the numbers 1 to 5.",
        """
        # Print 1, 2, 3, 4, 5 with a for loop
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "A function is a named block of code. def creates it, parameters go in the brackets, and return sends a result "
        "back. Call the function by writing its name with values in brackets.",
        """
        def greet(name):
            return "Hello, " + name + "!"

        print(greet("Sam"))
        print(greet("Alex"))
        """,
        "Hello, Sam!\nHello, Alex!",
        "Write a function double(n) that returns n * 2, then print double(21).",
        """
        def double(n):
            # return n * 2
            pass

        print(double(21))
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses a list, a function, a loop and conditions together. Read it line by line, run it, then "
        "extend it with the challenge below.",
        """
        def grade(score):
            if score >= 90:
                return "A"
            elif score >= 70:
                return "B"
            return "C"

        scores = [95, 72, 58]
        for s in scores:
            print(s, "->", grade(s))
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a score of 65 to the list.",
        """
        def grade(score):
            if score >= 90:
                return "A"
            elif score >= 70:
                return "B"
            return "C"

        scores = [95, 72, 58]
        for s in scores:
            print(s, "->", grade(s))
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# JAVASCRIPT
# ---------------------------------------------------------------------------
_JAVASCRIPT = [
    _lesson(
        "intro",
        "See what a JavaScript program is and where it runs.",
        "JavaScript runs in web browsers and, with Node.js, on your computer. A program is a list of instructions "
        "that run from top to bottom. Lines that start with // are comments and are ignored.",
        """
        // JavaScript runs this file from top to bottom.
        console.log("I am learning JavaScript!");
        """,
        "I am learning JavaScript!",
        "Change the message so it says your own name.",
        """
        console.log("I am learning JavaScript!");
        """,
    ),
    _lesson(
        "hello",
        "Write and run your first program.",
        "console.log() prints a value to the output. Text goes inside quotes, and each statement ends with a semicolon.",
        """
        console.log("Hello, world!");
        """,
        "Hello, world!",
        "Print Hello, world! and then Welcome to JavaScript on a second line.",
        """
        // Add a second console.log below
        console.log("Hello, world!");
        """,
    ),
    _lesson(
        "variables",
        "Store values with names.",
        "Use const for values that will not change and let for values that will. Types include string (text), number, "
        "and boolean (true/false). Template strings use backticks and ${} to insert values into text.",
        """
        const name = "Sam";
        let age = 12;
        age = age + 1;
        const isStudent = true;
        console.log(`${name} is ${age} years old`);
        console.log("Student?", isStudent);
        """,
        "Sam is 13 years old\nStudent? true",
        "Create a const for your favourite food and a let for a lucky number, then log one sentence using both.",
        """
        const food = "pizza";
        // Add a let luckyNumber and log a sentence using both
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "In a browser you would use a form or prompt(). In Node.js, the readline module reads a line typed by the "
        "user. In the workspace, type your input in the Custom Input box before you press Run.",
        """
        const readline = require("readline");
        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

        rl.question("What is your name? ", (name) => {
          console.log("Nice to meet you, " + name);
          rl.close();
        });
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a number and log the number multiplied by 2. Hint: Number(text) turns text into a number.",
        """
        const readline = require("readline");
        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

        rl.question("Pick a number: ", (text) => {
          const n = Number(text);
          // log n * 2
          rl.close();
        });
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if runs a block when its condition is true. else if adds more checks and else catches everything else. "
        "Use === to compare values (three equals signs).",
        """
        const score = 72;
        if (score >= 90) {
          console.log("Grade A");
        } else if (score >= 70) {
          console.log("Grade B");
        } else {
          console.log("Keep practicing");
        }
        """,
        "Grade B",
        "Change score to 95, then to 40, and check the output each time.",
        """
        const score = 72;
        if (score >= 90) {
          console.log("Grade A");
        } else if (score >= 70) {
          console.log("Grade B");
        } else {
          console.log("Keep practicing");
        }
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "A for loop has three parts: a start, a condition and a step. A while loop repeats while its condition is true. "
        "Make sure something changes inside a while loop, or it will never stop.",
        """
        for (let i = 1; i <= 3; i++) {
          console.log("Count " + i);
        }

        let total = 0;
        let n = 1;
        while (n <= 3) {
          total = total + n;
          n++;
        }
        console.log("Total " + total);
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to log the numbers 1 to 5.",
        """
        // Log 1, 2, 3, 4, 5 with a for loop
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "A function is a named block of code. function creates it, parameters go in brackets, and return sends a "
        "result back. Arrow functions (=>) are a shorter way to write small functions.",
        """
        function greet(name) {
          return "Hello, " + name + "!";
        }

        const shout = (text) => text.toUpperCase();

        console.log(greet("Sam"));
        console.log(shout(greet("Alex")));
        """,
        "Hello, Sam!\nHELLO, ALEX!",
        "Write a function double(n) that returns n * 2, then log double(21).",
        """
        function double(n) {
          // return n * 2;
        }

        console.log(double(21));
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses an array, a function, a loop and conditions together. Read it line by line, run it, then "
        "extend it with the challenge below.",
        """
        function grade(score) {
          if (score >= 90) return "A";
          if (score >= 70) return "B";
          return "C";
        }

        const scores = [95, 72, 58];
        for (const s of scores) {
          console.log(s + " -> " + grade(s));
        }
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a score of 65 to the array.",
        """
        function grade(score) {
          if (score >= 90) return "A";
          if (score >= 70) return "B";
          return "C";
        }

        const scores = [95, 72, 58];
        for (const s of scores) {
          console.log(s + " -> " + grade(s));
        }
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# TYPESCRIPT  (view-only on servers without a TypeScript runner)
# ---------------------------------------------------------------------------
_TYPESCRIPT = [
    _lesson(
        "intro",
        "See what TypeScript adds to JavaScript.",
        "TypeScript is JavaScript with types. You write types such as string and number, and the TypeScript compiler "
        "checks them before your program runs, so many mistakes are caught early. TypeScript files end in .ts and "
        "are compiled to plain JavaScript.",
        """
        // TypeScript is JavaScript plus type annotations.
        const message: string = "I am learning TypeScript!";
        console.log(message);
        """,
        "I am learning TypeScript!",
        "Change the message so it says your own name.",
        """
        const message: string = "I am learning TypeScript!";
        console.log(message);
        """,
    ),
    _lesson(
        "hello",
        "Write your first TypeScript program.",
        "console.log() works exactly as in JavaScript. The file is compiled with tsc (the TypeScript compiler) and "
        "the result runs with Node.js.",
        """
        console.log("Hello, world!");
        """,
        "Hello, world!",
        "Print Hello, world! and then Welcome to TypeScript on a second line.",
        """
        // Add a second console.log below
        console.log("Hello, world!");
        """,
    ),
    _lesson(
        "variables",
        "Store values and give them types.",
        "After the name, write a colon and the type: string, number or boolean. TypeScript reports an error if you "
        "store the wrong kind of value, for example a string in a number variable.",
        """
        const name: string = "Sam";
        let age: number = 12;
        age = age + 1;
        const isStudent: boolean = true;
        console.log(`${name} is ${age} years old`);
        console.log("Student?", isStudent);
        """,
        "Sam is 13 years old\nStudent? true",
        "Create a string for your favourite food and a number for a lucky number, then log one sentence using both.",
        """
        const food: string = "pizza";
        // Add a luckyNumber: number and log a sentence using both
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "With Node.js you can read a line using the readline module (install the Node type definitions with "
        "npm install --save-dev @types/node). The callback parameter gets a type too.",
        """
        import * as readline from "readline";

        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

        rl.question("What is your name? ", (name: string) => {
          console.log("Nice to meet you, " + name);
          rl.close();
        });
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a number and log the number multiplied by 2. Hint: Number(text) returns a number.",
        """
        import * as readline from "readline";

        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

        rl.question("Pick a number: ", (text: string) => {
          const n: number = Number(text);
          // log n * 2
          rl.close();
        });
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if, else if and else work as in JavaScript. TypeScript also checks that you compare values of compatible types.",
        """
        const score: number = 72;
        if (score >= 90) {
          console.log("Grade A");
        } else if (score >= 70) {
          console.log("Grade B");
        } else {
          console.log("Keep practicing");
        }
        """,
        "Grade B",
        "Change score to 95, then to 40, and predict the output before you run it.",
        """
        const score: number = 72;
        if (score >= 90) {
          console.log("Grade A");
        } else if (score >= 70) {
          console.log("Grade B");
        } else {
          console.log("Keep practicing");
        }
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "for and while loops work as in JavaScript. A loop counter such as i is inferred to be a number, so you usually "
        "do not need to write the type.",
        """
        for (let i = 1; i <= 3; i++) {
          console.log("Count " + i);
        }

        let total: number = 0;
        let n: number = 1;
        while (n <= 3) {
          total = total + n;
          n++;
        }
        console.log("Total " + total);
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to log the numbers 1 to 5.",
        """
        // Log 1, 2, 3, 4, 5 with a for loop
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "Give each parameter a type and write the return type after the brackets. Calling the function with the wrong "
        "type is a compile error, which helps you find bugs early.",
        """
        function greet(name: string): string {
          return "Hello, " + name + "!";
        }

        console.log(greet("Sam"));
        console.log(greet("Alex"));
        """,
        "Hello, Sam!\nHello, Alex!",
        "Write a function double(n: number): number that returns n * 2, then log double(21).",
        """
        function double(n: number): number {
          // return n * 2;
          return 0;
        }

        console.log(double(21));
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses an array type, a typed function, a loop and conditions together. Read it, then extend it "
        "with the challenge below.",
        """
        function grade(score: number): string {
          if (score >= 90) return "A";
          if (score >= 70) return "B";
          return "C";
        }

        const scores: number[] = [95, 72, 58];
        for (const s of scores) {
          console.log(s + " -> " + grade(s));
        }
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a score of 65 to the array.",
        """
        function grade(score: number): string {
          if (score >= 90) return "A";
          if (score >= 70) return "B";
          return "C";
        }

        const scores: number[] = [95, 72, 58];
        for (const s of scores) {
          console.log(s + " -> " + grade(s));
        }
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# JAVA
# ---------------------------------------------------------------------------
_JAVA = [
    _lesson(
        "intro",
        "See what a Java program looks like.",
        "Java code lives inside a class. The program starts at the main method. Java is compiled first (javac turns "
        "your file into bytecode) and then run on the Java Virtual Machine. Every statement ends with a semicolon.",
        """
        public class Main {
            public static void main(String[] args) {
                System.out.println("I am learning Java!");
            }
        }
        """,
        "I am learning Java!",
        "Change the message so it says your own name.",
        """
        public class Main {
            public static void main(String[] args) {
                System.out.println("I am learning Java!");
            }
        }
        """,
    ),
    _lesson(
        "hello",
        "Write and run your first program.",
        "System.out.println() prints a line of text. The class name (Main) must match the file name, and main is the "
        "method Java runs first.",
        """
        public class Main {
            public static void main(String[] args) {
                System.out.println("Hello, world!");
            }
        }
        """,
        "Hello, world!",
        "Print Hello, world! and then Welcome to Java on a second line.",
        """
        public class Main {
            public static void main(String[] args) {
                System.out.println("Hello, world!");
                // Add a second println below
            }
        }
        """,
    ),
    _lesson(
        "variables",
        "Store values with names and types.",
        "Java needs you to say the type when you create a variable: int for whole numbers, double for decimals, "
        "boolean for true/false and String for text. Adding a String and a number with + joins them into text.",
        """
        public class Main {
            public static void main(String[] args) {
                String name = "Sam";
                int age = 12;
                double height = 1.5;
                boolean isStudent = true;
                System.out.println(name + " is " + age + " years old");
                System.out.println("Height: " + height);
                System.out.println("Student? " + isStudent);
            }
        }
        """,
        "Sam is 12 years old\nHeight: 1.5\nStudent? true",
        "Create a String for your favourite food and an int for a lucky number, then print one sentence using both.",
        """
        public class Main {
            public static void main(String[] args) {
                String food = "pizza";
                // Add an int luckyNumber and print a sentence using both
            }
        }
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "A Scanner reads input from the keyboard. nextLine() reads a whole line of text and nextInt() reads a whole "
        "number. In the workspace, type your input in the Custom Input box before you press Run.",
        """
        import java.util.Scanner;

        public class Main {
            public static void main(String[] args) {
                Scanner input = new Scanner(System.in);
                System.out.print("What is your name? ");
                String name = input.nextLine();
                System.out.println("Nice to meet you, " + name);
            }
        }
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a whole number with nextInt() and print the number multiplied by 2.",
        """
        import java.util.Scanner;

        public class Main {
            public static void main(String[] args) {
                Scanner input = new Scanner(System.in);
                System.out.print("Pick a number: ");
                int n = input.nextInt();
                // Print n * 2
            }
        }
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if runs a block when its condition is true; else if and else handle the other cases. Conditions go in "
        "brackets and blocks use curly braces. Use == to compare numbers and .equals() to compare Strings.",
        """
        public class Main {
            public static void main(String[] args) {
                int score = 72;
                if (score >= 90) {
                    System.out.println("Grade A");
                } else if (score >= 70) {
                    System.out.println("Grade B");
                } else {
                    System.out.println("Keep practicing");
                }
            }
        }
        """,
        "Grade B",
        "Change score to 95, then to 40, and predict the output before you run it.",
        """
        public class Main {
            public static void main(String[] args) {
                int score = 72;
                if (score >= 90) {
                    System.out.println("Grade A");
                } else if (score >= 70) {
                    System.out.println("Grade B");
                } else {
                    System.out.println("Keep practicing");
                }
            }
        }
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "A for loop has a start, a condition and a step. A while loop repeats while its condition is true, so make "
        "sure something inside changes or it will never stop.",
        """
        public class Main {
            public static void main(String[] args) {
                for (int i = 1; i <= 3; i++) {
                    System.out.println("Count " + i);
                }

                int total = 0;
                int n = 1;
                while (n <= 3) {
                    total = total + n;
                    n++;
                }
                System.out.println("Total " + total);
            }
        }
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to print the numbers 1 to 5.",
        """
        public class Main {
            public static void main(String[] args) {
                // Print 1, 2, 3, 4, 5 with a for loop
            }
        }
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "In Java, functions are called methods. Write the return type, the name and the parameters with their types. "
        "static lets main call the method directly.",
        """
        public class Main {
            static String greet(String name) {
                return "Hello, " + name + "!";
            }

            public static void main(String[] args) {
                System.out.println(greet("Sam"));
                System.out.println(greet("Alex"));
            }
        }
        """,
        "Hello, Sam!\nHello, Alex!",
        "Write a method static int twice(int n) that returns n * 2, then print twice(21).",
        """
        public class Main {
            // Add: static int twice(int n) { ... }

            public static void main(String[] args) {
                // System.out.println(twice(21));
            }
        }
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses an array, a method, a loop and conditions together. Read it, run it, then extend it with "
        "the challenge below.",
        """
        public class Main {
            static String grade(int score) {
                if (score >= 90) return "A";
                if (score >= 70) return "B";
                return "C";
            }

            public static void main(String[] args) {
                int[] scores = {95, 72, 58};
                for (int s : scores) {
                    System.out.println(s + " -> " + grade(s));
                }
            }
        }
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a score of 65 to the array.",
        """
        public class Main {
            static String grade(int score) {
                if (score >= 90) return "A";
                if (score >= 70) return "B";
                return "C";
            }

            public static void main(String[] args) {
                int[] scores = {95, 72, 58};
                for (int s : scores) {
                    System.out.println(s + " -> " + grade(s));
                }
            }
        }
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# C
# ---------------------------------------------------------------------------
_C = [
    _lesson(
        "intro",
        "See what a C program looks like.",
        "C is a compiled language: a compiler turns your source file into a program the computer can run. Every C "
        "program starts at main(). #include brings in code libraries; stdio.h gives you printf for printing.",
        """
        #include <stdio.h>

        int main(void) {
            printf("I am learning C!\\n");
            return 0;
        }
        """,
        "I am learning C!",
        "Change the message so it says your own name.",
        """
        #include <stdio.h>

        int main(void) {
            printf("I am learning C!\\n");
            return 0;
        }
        """,
    ),
    _lesson(
        "hello",
        "Write and run your first program.",
        "printf() prints text. \\n at the end of the text is a new line. return 0 tells the computer the program "
        "finished without errors. Every statement ends with a semicolon.",
        """
        #include <stdio.h>

        int main(void) {
            printf("Hello, world!\\n");
            return 0;
        }
        """,
        "Hello, world!",
        "Print Hello, world! and then Welcome to C on a second line.",
        """
        #include <stdio.h>

        int main(void) {
            printf("Hello, world!\\n");
            /* Add a second printf below */
            return 0;
        }
        """,
    ),
    _lesson(
        "variables",
        "Store values with names and types.",
        "C needs a type for every variable: int for whole numbers, double for decimals and char for a single "
        "character. printf uses format codes to show them: %d for int, %f for double and %c for char.",
        """
        #include <stdio.h>

        int main(void) {
            int age = 12;
            double height = 1.5;
            char grade = 'A';
            printf("Age: %d\\n", age);
            printf("Height: %.1f\\n", height);
            printf("Grade: %c\\n", grade);
            return 0;
        }
        """,
        "Age: 12\nHeight: 1.5\nGrade: A",
        "Create an int for a lucky number and print it with printf and %d.",
        """
        #include <stdio.h>

        int main(void) {
            /* Add an int luckyNumber and print it */
            return 0;
        }
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "scanf() reads input. The format code says what to read (%d for int, %s for a word) and & gives scanf the "
        "address of the variable to fill. Numbers need &; arrays like name do not. In the workspace, type your input "
        "in the Custom Input box before you press Run.",
        """
        #include <stdio.h>

        int main(void) {
            char name[50];
            printf("What is your name? ");
            scanf("%49s", name);
            printf("Nice to meet you, %s\\n", name);
            return 0;
        }
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a whole number with scanf and %d, then print the number multiplied by 2.",
        """
        #include <stdio.h>

        int main(void) {
            int n;
            printf("Pick a number: ");
            scanf("%d", &n);
            /* Print n * 2 */
            return 0;
        }
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if, else if and else choose which block runs. Conditions go in brackets and blocks use curly braces. Use == "
        "to compare (two equals signs) because a single = stores a value.",
        """
        #include <stdio.h>

        int main(void) {
            int score = 72;
            if (score >= 90) {
                printf("Grade A\\n");
            } else if (score >= 70) {
                printf("Grade B\\n");
            } else {
                printf("Keep practicing\\n");
            }
            return 0;
        }
        """,
        "Grade B",
        "Change score to 95, then to 40, and predict the output before you run it.",
        """
        #include <stdio.h>

        int main(void) {
            int score = 72;
            if (score >= 90) {
                printf("Grade A\\n");
            } else if (score >= 70) {
                printf("Grade B\\n");
            } else {
                printf("Keep practicing\\n");
            }
            return 0;
        }
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "A for loop has a start, a condition and a step. A while loop repeats while its condition is true, so make "
        "sure something inside it changes or it will never stop.",
        """
        #include <stdio.h>

        int main(void) {
            for (int i = 1; i <= 3; i++) {
                printf("Count %d\\n", i);
            }

            int total = 0;
            int n = 1;
            while (n <= 3) {
                total = total + n;
                n++;
            }
            printf("Total %d\\n", total);
            return 0;
        }
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to print the numbers 1 to 5.",
        """
        #include <stdio.h>

        int main(void) {
            /* Print 1, 2, 3, 4, 5 with a for loop */
            return 0;
        }
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "A function has a return type, a name and typed parameters. Define it above main (or declare it first) so "
        "main can call it.",
        """
        #include <stdio.h>

        int twice(int n) {
            return n * 2;
        }

        int main(void) {
            printf("%d\\n", twice(21));
            printf("%d\\n", twice(5));
            return 0;
        }
        """,
        "42\n10",
        "Write a function int square(int n) that returns n * n, then print square(7).",
        """
        #include <stdio.h>

        /* Add: int square(int n) { ... } */

        int main(void) {
            /* printf("%d\\n", square(7)); */
            return 0;
        }
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses an array, a function, a loop and conditions together. Read it, run it, then extend it with "
        "the challenge below.",
        """
        #include <stdio.h>

        char grade(int score) {
            if (score >= 90) return 'A';
            if (score >= 70) return 'B';
            return 'C';
        }

        int main(void) {
            int scores[] = {95, 72, 58};
            for (int i = 0; i < 3; i++) {
                printf("%d -> %c\\n", scores[i], grade(scores[i]));
            }
            return 0;
        }
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a fourth score of 65 (remember to change the loop limit).",
        """
        #include <stdio.h>

        char grade(int score) {
            if (score >= 90) return 'A';
            if (score >= 70) return 'B';
            return 'C';
        }

        int main(void) {
            int scores[] = {95, 72, 58};
            for (int i = 0; i < 3; i++) {
                printf("%d -> %c\\n", scores[i], grade(scores[i]));
            }
            return 0;
        }
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# C++
# ---------------------------------------------------------------------------
_CPP = [
    _lesson(
        "intro",
        "See what a C++ program looks like.",
        "C++ is a compiled language built on C. Every program starts at main(). #include <iostream> gives you cout "
        "for printing. std:: tells the compiler the name comes from the standard library.",
        """
        #include <iostream>

        int main() {
            std::cout << "I am learning C++!" << std::endl;
            return 0;
        }
        """,
        "I am learning C++!",
        "Change the message so it says your own name.",
        """
        #include <iostream>

        int main() {
            std::cout << "I am learning C++!" << std::endl;
            return 0;
        }
        """,
    ),
    _lesson(
        "hello",
        "Write and run your first program.",
        "std::cout sends text to the screen. The << symbols push values into it one after another, and std::endl "
        "ends the line. Every statement ends with a semicolon.",
        """
        #include <iostream>

        int main() {
            std::cout << "Hello, world!" << std::endl;
            return 0;
        }
        """,
        "Hello, world!",
        "Print Hello, world! and then Welcome to C++ on a second line.",
        """
        #include <iostream>

        int main() {
            std::cout << "Hello, world!" << std::endl;
            // Add a second line below
            return 0;
        }
        """,
    ),
    _lesson(
        "variables",
        "Store values with names and types.",
        "C++ needs a type for every variable: int for whole numbers, double for decimals, bool for true/false and "
        "std::string for text (include <string>). You can print several values in one line with <<.",
        """
        #include <iostream>
        #include <string>

        int main() {
            std::string name = "Sam";
            int age = 12;
            double height = 1.5;
            bool isStudent = true;
            std::cout << name << " is " << age << " years old" << std::endl;
            std::cout << "Height: " << height << std::endl;
            std::cout << "Student? " << isStudent << std::endl;
            return 0;
        }
        """,
        "Sam is 12 years old\nHeight: 1.5\nStudent? 1",
        "Create a std::string for your favourite food and an int for a lucky number, then print one sentence using both.",
        """
        #include <iostream>
        #include <string>

        int main() {
            std::string food = "pizza";
            // Add an int luckyNumber and print a sentence using both
            return 0;
        }
        """,
    ),
    _lesson(
        "io",
        "Read what the user types and show a result.",
        "std::cin >> variable reads a value typed by the user. It reads one word or number at a time. In the "
        "workspace, type your input in the Custom Input box before you press Run.",
        """
        #include <iostream>
        #include <string>

        int main() {
            std::string name;
            std::cout << "What is your name? ";
            std::cin >> name;
            std::cout << "Nice to meet you, " << name << std::endl;
            return 0;
        }
        """,
        "What is your name? Nice to meet you, Sam",
        "Ask for a whole number with std::cin and print the number multiplied by 2.",
        """
        #include <iostream>

        int main() {
            int n;
            std::cout << "Pick a number: ";
            std::cin >> n;
            // Print n * 2
            return 0;
        }
        """,
        sample_input="Sam",
    ),
    _lesson(
        "conditions",
        "Make the program choose between options.",
        "if, else if and else choose which block runs. Conditions go in brackets and blocks use curly braces. Use == "
        "to compare (two equals signs) because a single = stores a value.",
        """
        #include <iostream>

        int main() {
            int score = 72;
            if (score >= 90) {
                std::cout << "Grade A" << std::endl;
            } else if (score >= 70) {
                std::cout << "Grade B" << std::endl;
            } else {
                std::cout << "Keep practicing" << std::endl;
            }
            return 0;
        }
        """,
        "Grade B",
        "Change score to 95, then to 40, and predict the output before you run it.",
        """
        #include <iostream>

        int main() {
            int score = 72;
            if (score >= 90) {
                std::cout << "Grade A" << std::endl;
            } else if (score >= 70) {
                std::cout << "Grade B" << std::endl;
            } else {
                std::cout << "Keep practicing" << std::endl;
            }
            return 0;
        }
        """,
    ),
    _lesson(
        "loops",
        "Repeat actions without copying code.",
        "A for loop has a start, a condition and a step. A while loop repeats while its condition is true, so make "
        "sure something inside it changes or it will never stop.",
        """
        #include <iostream>

        int main() {
            for (int i = 1; i <= 3; i++) {
                std::cout << "Count " << i << std::endl;
            }

            int total = 0;
            int n = 1;
            while (n <= 3) {
                total = total + n;
                n++;
            }
            std::cout << "Total " << total << std::endl;
            return 0;
        }
        """,
        "Count 1\nCount 2\nCount 3\nTotal 6",
        "Use a for loop to print the numbers 1 to 5.",
        """
        #include <iostream>

        int main() {
            // Print 1, 2, 3, 4, 5 with a for loop
            return 0;
        }
        """,
    ),
    _lesson(
        "functions",
        "Package code you can reuse.",
        "A function has a return type, a name and typed parameters. Define it above main (or declare it first) so "
        "main can call it.",
        """
        #include <iostream>

        int twice(int n) {
            return n * 2;
        }

        int main() {
            std::cout << twice(21) << std::endl;
            std::cout << twice(5) << std::endl;
            return 0;
        }
        """,
        "42\n10",
        "Write a function int square(int n) that returns n * n, then print square(7).",
        """
        #include <iostream>

        // Add: int square(int n) { ... }

        int main() {
            // std::cout << square(7) << std::endl;
            return 0;
        }
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a mini grade report.",
        "This project uses a vector (a resizable list), a function, a loop and conditions together. Read it, run it, "
        "then extend it with the challenge below.",
        """
        #include <iostream>
        #include <string>
        #include <vector>

        std::string grade(int score) {
            if (score >= 90) return "A";
            if (score >= 70) return "B";
            return "C";
        }

        int main() {
            std::vector<int> scores = {95, 72, 58};
            for (int s : scores) {
                std::cout << s << " -> " << grade(s) << std::endl;
            }
            return 0;
        }
        """,
        "95 -> A\n72 -> B\n58 -> C",
        "Add a grade D for scores from 60 to 69, and add a score of 65 to the vector.",
        """
        #include <iostream>
        #include <string>
        #include <vector>

        std::string grade(int score) {
            if (score >= 90) return "A";
            if (score >= 70) return "B";
            return "C";
        }

        int main() {
            std::vector<int> scores = {95, 72, 58};
            for (int s : scores) {
                std::cout << s << " -> " << grade(s) << std::endl;
            }
            return 0;
        }
        """,
        title="Small project: grade report",
    ),
]

# ---------------------------------------------------------------------------
# HTML / CSS
# HTML and CSS are not general programming languages, so the "variables / input and
# output / conditions / loops / functions" steps use their closest real equivalents
# (CSS custom properties, forms, media queries, repeated elements, reusable classes
# and a small script). Each lesson says so in its summary.
# ---------------------------------------------------------------------------
_HTML = [
    _lesson(
        "intro",
        "See how HTML and CSS build a web page.",
        "HTML describes the content of a page using tags such as <h1> (a heading) and <p> (a paragraph). CSS describes "
        "how it looks (colours, sizes, spacing). Your browser reads the HTML and applies the CSS to draw the page. "
        "These are markup and styling languages, not programming languages, so the lessons use their closest "
        "equivalents of variables, loops and functions.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <title>My first page</title>
          </head>
          <body>
            <p>I am learning HTML and CSS!</p>
          </body>
        </html>
        """,
        "Browser preview: a page with the text \"I am learning HTML and CSS!\"",
        "Change the paragraph so it says your own name.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <title>My first page</title>
          </head>
          <body>
            <p>I am learning HTML and CSS!</p>
          </body>
        </html>
        """,
    ),
    _lesson(
        "hello",
        "Build your first web page.",
        "An <h1> tag makes a big heading. Tags usually come in pairs: an opening tag <h1> and a closing tag </h1>. "
        "The <style> element holds CSS; a rule has a selector (h1) and declarations in braces.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              h1 { color: teal; }
            </style>
          </head>
          <body>
            <h1>Hello, world!</h1>
          </body>
        </html>
        """,
        "Browser preview: a teal heading that says \"Hello, world!\"",
        "Add a paragraph under the heading that says Welcome to HTML and CSS, and make it navy blue.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              h1 { color: teal; }
            </style>
          </head>
          <body>
            <h1>Hello, world!</h1>
          </body>
        </html>
        """,
    ),
    _lesson(
        "variables",
        "Reuse values with CSS custom properties (the CSS version of variables).",
        "A CSS custom property is a named value that starts with two dashes, such as --main-color. Define it once in "
        ":root, then use it anywhere with var(--main-color). Change the value in one place and the whole page updates.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              :root {
                --main-color: teal;
                --space: 16px;
              }
              h1 { color: var(--main-color); }
              p { border-left: 4px solid var(--main-color); padding-left: var(--space); }
            </style>
          </head>
          <body>
            <h1>Colour variables</h1>
            <p>Change --main-color once to restyle everything.</p>
          </body>
        </html>
        """,
        "Browser preview: a teal heading and a paragraph with a teal left border.",
        "Change --main-color to tomato and see both the heading and the border change.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              :root {
                --main-color: teal;
                --space: 16px;
              }
              h1 { color: var(--main-color); }
              p { border-left: 4px solid var(--main-color); padding-left: var(--space); }
            </style>
          </head>
          <body>
            <h1>Colour variables</h1>
            <p>Change --main-color once to restyle everything.</p>
          </body>
        </html>
        """,
    ),
    _lesson(
        "io",
        "Collect input with a form and show output with a script.",
        "An <input> lets the visitor type, and a <button> lets them act. A small script reads the input's value and "
        "writes the result into another element. This is the web version of reading input and printing output.",
        """
        <!DOCTYPE html>
        <html>
          <body>
            <label for="name">What is your name?</label>
            <input id="name" type="text" />
            <button onclick="greet()">Say hello</button>
            <p id="output"></p>

            <script>
              function greet() {
                var name = document.getElementById("name").value;
                document.getElementById("output").textContent = "Nice to meet you, " + name;
              }
            </script>
          </body>
        </html>
        """,
        "Browser preview: type a name, press the button, and the page shows \"Nice to meet you, <name>\".",
        "Change the message so it says Hello followed by the name and an exclamation mark.",
        """
        <!DOCTYPE html>
        <html>
          <body>
            <label for="name">What is your name?</label>
            <input id="name" type="text" />
            <button onclick="greet()">Say hello</button>
            <p id="output"></p>

            <script>
              function greet() {
                var name = document.getElementById("name").value;
                document.getElementById("output").textContent = "Nice to meet you, " + name;
              }
            </script>
          </body>
        </html>
        """,
    ),
    _lesson(
        "conditions",
        "Style things only when a condition is true.",
        "CSS has no if statement, but it has conditional rules. A media query applies its styles only when the "
        "screen is narrow enough, and :hover applies styles only while the mouse is over an element.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              .box { background: lightblue; padding: 20px; }
              .box:hover { background: gold; }
              @media (max-width: 500px) {
                .box { background: lightgreen; }
              }
            </style>
          </head>
          <body>
            <div class="box">Hover over me, or make the window narrow.</div>
          </body>
        </html>
        """,
        "Browser preview: a light blue box that turns gold on hover, and light green on narrow screens.",
        "Make the box turn pink while hovered instead of gold.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              .box { background: lightblue; padding: 20px; }
              .box:hover { background: gold; }
              @media (max-width: 500px) {
                .box { background: lightgreen; }
              }
            </style>
          </head>
          <body>
            <div class="box">Hover over me, or make the window narrow.</div>
          </body>
        </html>
        """,
    ),
    _lesson(
        "loops",
        "Repeat elements in a list and with a script loop.",
        "In HTML, repeating means writing similar elements, such as the <li> items of a list. To repeat without "
        "copying, a script can use a loop to create elements for you.",
        """
        <!DOCTYPE html>
        <html>
          <body>
            <h2>Static list</h2>
            <ul>
              <li>HTML</li>
              <li>CSS</li>
            </ul>

            <h2>List made by a loop</h2>
            <ul id="counts"></ul>

            <script>
              for (var i = 1; i <= 3; i++) {
                var li = document.createElement("li");
                li.textContent = "Count " + i;
                document.getElementById("counts").appendChild(li);
              }
            </script>
          </body>
        </html>
        """,
        "Browser preview: a two-item list, then a list showing Count 1, Count 2 and Count 3.",
        "Change the loop so it creates five items instead of three.",
        """
        <!DOCTYPE html>
        <html>
          <body>
            <h2>Static list</h2>
            <ul>
              <li>HTML</li>
              <li>CSS</li>
            </ul>

            <h2>List made by a loop</h2>
            <ul id="counts"></ul>

            <script>
              for (var i = 1; i <= 3; i++) {
                var li = document.createElement("li");
                li.textContent = "Count " + i;
                document.getElementById("counts").appendChild(li);
              }
            </script>
          </body>
        </html>
        """,
    ),
    _lesson(
        "functions",
        "Reuse styles with classes and behaviour with a function.",
        "A CSS class is a reusable bundle of styles: write it once and add class=\"...\" to any element. In a script, "
        "a function bundles actions you can call whenever you need them.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; color: white; }
              .green { background: seagreen; }
              .red { background: crimson; }
            </style>
          </head>
          <body>
            <span class="badge green">Passed</span>
            <span class="badge red">Try again</span>
            <p><button onclick="shout()">Click me</button></p>
            <p id="msg"></p>
            <script>
              function shout() {
                document.getElementById("msg").textContent = "HELLO!";
              }
            </script>
          </body>
        </html>
        """,
        "Browser preview: a green Passed badge, a red Try again badge, and a button that shows HELLO!",
        "Add a third badge with a new class called blue, and give it a blue background.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; color: white; }
              .green { background: seagreen; }
              .red { background: crimson; }
            </style>
          </head>
          <body>
            <span class="badge green">Passed</span>
            <span class="badge red">Try again</span>
            <p><button onclick="shout()">Click me</button></p>
            <p id="msg"></p>
            <script>
              function shout() {
                document.getElementById("msg").textContent = "HELLO!";
              }
            </script>
          </body>
        </html>
        """,
    ),
    _lesson(
        "project",
        "Combine everything into a personal profile card.",
        "This project uses custom properties, classes, a hover rule and a small script together. Read it, run it, "
        "then make it yours with the challenge below.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              :root { --accent: teal; }
              .card { max-width: 280px; border: 2px solid var(--accent); border-radius: 12px; padding: 16px; font-family: sans-serif; }
              .card h2 { color: var(--accent); margin-top: 0; }
              .card button { background: var(--accent); color: white; border: 0; padding: 8px 14px; border-radius: 8px; }
              .card button:hover { opacity: 0.85; }
            </style>
          </head>
          <body>
            <div class="card">
              <h2>Sam Rivera</h2>
              <p>Learning to build web pages.</p>
              <button onclick="document.getElementById('hi').textContent = 'Thanks for visiting!'">Say hi</button>
              <p id="hi"></p>
            </div>
          </body>
        </html>
        """,
        "Browser preview: a teal-bordered profile card with a button that shows \"Thanks for visiting!\"",
        "Put your own name on the card, change --accent to a colour you like, and add one more paragraph about a hobby.",
        """
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              :root { --accent: teal; }
              .card { max-width: 280px; border: 2px solid var(--accent); border-radius: 12px; padding: 16px; font-family: sans-serif; }
              .card h2 { color: var(--accent); margin-top: 0; }
              .card button { background: var(--accent); color: white; border: 0; padding: 8px 14px; border-radius: 8px; }
              .card button:hover { opacity: 0.85; }
            </style>
          </head>
          <body>
            <div class="card">
              <h2>Sam Rivera</h2>
              <p>Learning to build web pages.</p>
              <button onclick="document.getElementById('hi').textContent = 'Thanks for visiting!'">Say hi</button>
              <p id="hi"></p>
            </div>
          </body>
        </html>
        """,
        title="Small project: profile card",
    ),
]


# ---------------------------------------------------------------------------
# Course registry
# `language` is the id used by the existing workspace/runner. TypeScript has no
# runner on this server, so it is None and its lessons are read-only.
# ---------------------------------------------------------------------------
COURSES: Dict[str, Dict[str, Any]] = {
    "c": {
        "id": "c", "name": "C", "icon": "🔧", "language": "c", "file_ext": ".c",
        "tagline": "Learn how computers really work: types, memory-friendly code and fast programs.",
        "lessons": _C,
    },
    "cpp": {
        "id": "cpp", "name": "C++", "icon": "⚙️", "language": "cpp", "file_ext": ".cpp",
        "tagline": "Build on C with strings, vectors and cleaner input and output.",
        "lessons": _CPP,
    },
    "java": {
        "id": "java", "name": "Java", "icon": "☕", "language": "java", "file_ext": ".java",
        "tagline": "Learn classes, types and methods in a language used everywhere.",
        "lessons": _JAVA,
    },
    "python": {
        "id": "python", "name": "Python", "icon": "🐍", "language": "python", "file_ext": ".py",
        "tagline": "The friendliest first language: clear, short and powerful.",
        "lessons": _PYTHON,
    },
    "javascript": {
        "id": "javascript", "name": "JavaScript", "icon": "🟨", "language": "javascript", "file_ext": ".js",
        "tagline": "The language of the web, running in browsers and on your computer.",
        "lessons": _JAVASCRIPT,
    },
    "typescript": {
        "id": "typescript", "name": "TypeScript", "icon": "🔷", "language": None, "file_ext": ".ts",
        "tagline": "JavaScript with types that catch mistakes before your code runs.",
        "lessons": _TYPESCRIPT,
        "read_only_note": (
            "No TypeScript runner is installed on this server yet, so you can read the lessons and copy the "
            "examples, but not run them here."
        ),
    },
    "html": {
        "id": "html", "name": "HTML & CSS", "icon": "🌐", "language": "html", "file_ext": ".html",
        "tagline": "Build and style real web pages and see the result instantly.",
        "lessons": _HTML,
    },
}

COURSE_ORDER = ["python", "javascript", "typescript", "html", "java", "c", "cpp"]

for _course in COURSES.values():
    for _index, _lesson_data in enumerate(_course["lessons"], start=1):
        _lesson_data["id"] = f"{_course['id']}_l{_index}"
        _lesson_data["order"] = _index


def normalize_course_id(course_id: str) -> str:
    norm = (course_id or "").lower().strip()
    aliases = {"py": "python", "js": "javascript", "ts": "typescript", "c++": "cpp", "css": "html", "html/css": "html"}
    return aliases.get(norm, norm)


def get_course(course_id: str) -> Optional[Dict[str, Any]]:
    return COURSES.get(normalize_course_id(course_id))


def list_courses() -> List[Dict[str, Any]]:
    return [COURSES[cid] for cid in COURSE_ORDER if cid in COURSES]


def find_lesson(course_id: str, lesson_id: str) -> Optional[Dict[str, Any]]:
    course = get_course(course_id)
    if not course:
        return None
    for lesson in course["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    return None
