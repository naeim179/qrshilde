import 'package:flutter/material.dart';
import 'services/api_service.dart';

void main() {
  runApp(const QRShildeApp());
}

class QRShildeApp extends StatelessWidget {
  const QRShildeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'QRShilde',
      theme: ThemeData(useMaterial3: true),
      home: const AnalyzeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key});

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _loading = false;
  Map<String, dynamic>? _result;
  String? _error;

  Future<void> _analyze() async {
    final payload = _controller.text.trim();
    if (payload.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final data = await ApiService.analyzePayload(payload);
      setState(() {
        _result = data;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Widget _buildResultCard(Map<String, dynamic> result) {
    final findings = (result['findings'] as List?) ?? [];
    final benign = (result['benign'] as List?) ?? [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Verdict: ${result['verdict'] ?? '-'}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Risk Score: ${result['risk_score'] ?? '-'} / 100'),
            Text('Payload Type: ${result['payload_type'] ?? '-'}'),
            Text('Confidence: ${result['confidence'] ?? '-'}'),
            const SizedBox(height: 12),
            const Text('Findings',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            if (findings.isEmpty) const Text('- None'),
            ...findings.map((e) => Text('- $e')),
            const SizedBox(height: 12),
            const Text('Benign Signals',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            if (benign.isEmpty) const Text('- None'),
            ...benign.map((e) => Text('- $e')),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final result = _result?['result'] as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(
        title: const Text('QRShilde Analyzer'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'QR Payload',
                hintText: 'Paste decoded QR content here',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _loading ? null : _analyze,
                child: _loading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Analyze'),
              ),
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            if (result != null)
              Expanded(
                child: SingleChildScrollView(
                  child: _buildResultCard(result),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
