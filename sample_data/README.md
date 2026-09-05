# Demo enrollment data

This directory contains fictional, synthetic records for local development only.
The SVG files are illustrations, not biometric photographs, and must not be used
to evaluate a face-recognition model.

- `schools.csv` contains the school roster.
- `teachers.csv` contains teacher-to-school assignments.
- `students.csv` contains student records and image filenames.
- `student_images/` contains one synthetic illustration per student.

Run the importer seed to load the records into the local database:

```bash
PYTHONPATH=. .venv/bin/python backend/scripts/seed_demo.py
```
