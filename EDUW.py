from flask import Flask, jsonify, request

app = Flask(__name__)
# in-memory storage for students and results (replace with a database in production)
students = []
result = {} # students_id: {suject: grade}
next_student_id = 1

@app.route('/students', methods=['POST'])
def add_students():
    """Adds a new student to the system."""
    global next_student_id
    data = request.get_json()
    if not data or 'name' not in data or age not in data:
        return jsonify({"error": "Missing student name or age"}), 400
    student = {
        "id": next_student_id,
        "name": data['name'],
        "age": data['age']
    }
    students.append(student)
    next_student_id += 1
    return jsonify(student), 201

@app.route('/students', methods=['GET'])
def view_students():
    """Retrives details of a specific students."""
    return jsonify(students)

app.route('/students/<int:student_id>', methods=['GET'])
def view_students_by_id(student_id):
    """Retrives details of a specific student by ID."""
    student = next((s for s in students if s['id'] == student_id), None)
    if student:
        return jsonify(student)
    return({"error": "Student not found"}), 404

@app.route('/results/<int:student_id>', methods=['POST'])
def add_result(student_id):
    