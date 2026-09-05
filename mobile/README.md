# Attendance mobile client

This Flutter client provides the teacher's live classroom scan flow:

1. Open the camera and start a short video scan.
2. Pan slowly across the classroom.
3. Stop the scan and run on-device face detection.
4. Send candidate student IDs to `POST /api/attendance/verify-capture`.
5. Review the accepted and rejected/unmatched student IDs shown below the
   camera before submitting attendance.

The current screen uses an empty candidate list as an integration placeholder.
Connect a consented, supported on-device face detector before using real student
images. Do not use the synthetic SVG illustrations as biometric training data.

## Production backend

The Flutter app does not start the Python backend on the phone. Deploy the
FastAPI service to a reachable HTTPS host, then pass its URL when launching
the app:

```bash
flutter run --dart-define=API_BASE_URL=https://attendance-api.example.com
```

The same value can be used for release builds:

```bash
flutter build apk --dart-define=API_BASE_URL=https://attendance-api.example.com
```

## Local development

From this directory, start the API in another terminal from the repository
root:

```bash
PYTHONPATH=. .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --reload
```

Then run Flutter:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For Chrome use `http://127.0.0.1:8000`. A physical phone must use the
computer's LAN IP instead, for example
`http://192.168.1.20:8000`, and the API must listen on `0.0.0.0`.
