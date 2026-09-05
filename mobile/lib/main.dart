import 'dart:convert';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

const configuredApiBaseUrl = String.fromEnvironment('API_BASE_URL');

String get apiBaseUrl {
  if (configuredApiBaseUrl.isNotEmpty) {
    return configuredApiBaseUrl.replaceFirst(RegExp(r'/$'), '');
  }
  return kIsWeb ? 'http://127.0.0.1:8000' : 'http://10.0.2.2:8000';
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final cameras = await availableCameras();
  runApp(AttendanceApp(camera: cameras.first));
}

class AttendanceApp extends StatelessWidget {
  const AttendanceApp({super.key, required this.camera});

  final CameraDescription camera;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Attendly',
      theme: ThemeData(colorSchemeSeed: const Color(0xff1769e0)),
      home: CapturePage(camera: camera),
    );
  }
}

class CapturePage extends StatefulWidget {
  const CapturePage({super.key, required this.camera});

  final CameraDescription camera;

  @override
  State<CapturePage> createState() => _CapturePageState();
}

class _CapturePageState extends State<CapturePage> {
  late final CameraController _controller;
  Future<void>? _initialization;
  bool _recording = false;
  String _message = 'Pan slowly across the classroom, then stop the scan.';
  List<int> _validStudentIds = [];
  List<int> _rejectedStudentIds = [];
  bool _hasVerificationResult = false;

  @override
  void initState() {
    super.initState();
    _controller = CameraController(widget.camera, ResolutionPreset.medium);
    _initialization = _controller.initialize();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _toggleScan() async {
    await _initialization;
    if (_recording) {
      final video = await _controller.stopVideoRecording();
      setState(() {
        _recording = false;
        _message = 'Scan captured. Reviewing detected students...';
      });
      await _verifyDetectedStudents(video);
      return;
    }
    await _controller.startVideoRecording();
    setState(() {
      _recording = true;
      _message = 'Scanning... pan slowly across all student desks.';
    });
  }

  Future<void> _verifyDetectedStudents(XFile video) async {
    // Replace this adapter with the on-device face detector. The backend
    // receives candidate IDs, then enforces the teacher-school boundary.
    final candidateStudentIds = <int>[];
    final response = await http.post(
      Uri.parse('$apiBaseUrl/api/attendance/verify-capture'),
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'change-me-in-production',
      },
      body: jsonEncode({'teacher_id': 1, 'student_ids': candidateStudentIds}),
    );
    if (!mounted) return;
    if (response.statusCode == 200) {
      final result = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        _validStudentIds = List<int>.from(result['valid_student_ids'] as List);
        _rejectedStudentIds =
            List<int>.from(result['rejected_student_ids'] as List);
        _hasVerificationResult = true;
        _message = 'Review matched and rejected students before submitting.';
      });
      return;
    }
    setState(() {
      _message = 'Verification failed. Please try the scan again.';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Capture attendance')),
      body: FutureBuilder<void>(
        future: _initialization,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          return Column(
            children: [
              Expanded(child: CameraPreview(_controller)),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(_message, textAlign: TextAlign.center),
                    if (_hasVerificationResult) ...[
                      const SizedBox(height: 16),
                      _StudentReview(
                        title: 'Accepted students',
                        ids: _validStudentIds,
                        color: Colors.green,
                      ),
                      const SizedBox(height: 8),
                      _StudentReview(
                        title: 'Rejected / unmatched students',
                        ids: _rejectedStudentIds,
                        color: Colors.red,
                      ),
                    ],
                    const SizedBox(height: 14),
                    FilledButton.icon(
                      onPressed: _toggleScan,
                      icon: Icon(_recording ? Icons.stop : Icons.videocam),
                      label: Text(_recording ? 'Stop scan' : 'Start scan'),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _StudentReview extends StatelessWidget {
  const _StudentReview({
    required this.title,
    required this.ids,
    required this.color,
  });

  final String title;
  final List<int> ids;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        '$title (${ids.length}): ${ids.isEmpty ? "None" : ids.join(", ")}',
        style: TextStyle(color: color, fontWeight: FontWeight.w600),
      ),
    );
  }
}
