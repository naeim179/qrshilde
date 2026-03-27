import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'screens/qr_scanner_screen.dart';
import 'services/api_service.dart';
import 'services/history_service.dart';

void main() {
  runApp(const QRShildeApp());
}

class QRShildeApp extends StatelessWidget {
  const QRShildeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'QRShilde',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
      ),
      home: const AnalyzeScreen(),
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
  String? _error;
  Map<String, dynamic>? _result;
  List<Map<String, dynamic>> _history = [];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final items = await HistoryService.loadHistory();
    if (!mounted) return;

    setState(() {
      _history = items;
    });
  }

  // =============================
  // 🔥 SECURITY DECISION ENGINE
  // =============================
  void _handleSecurityDecision(Map<String, dynamic> result, String payload) {
    final verdict = (result['verdict'] ?? 'LOW').toString().toUpperCase();

    if (verdict == "HIGH") {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text("🚨 High Risk"),
          content: const Text("This QR code is dangerous. Access blocked."),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("OK"),
            )
          ],
        ),
      );
    } else if (verdict == "MEDIUM") {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text("⚠️ Warning"),
          content: const Text("This QR may be unsafe. Continue?"),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel"),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _openPayload(payload);
              },
              child: const Text("Continue"),
            ),
          ],
        ),
      );
    } else {
      _openPayload(payload);
    }
  }

  // =============================
  // 🔗 OPEN PAYLOAD (SAFE)
  // =============================
  Future<void> _openPayload(String payload) async {
    if (payload.startsWith("http")) {
      await Clipboard.setData(ClipboardData(text: payload));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Link copied safely")),
      );
    }
  }

  // =============================
  // 🔍 ANALYZE
  // =============================
  Future<void> _analyze() async {
    final payload = _controller.text.trim();

    if (payload.isEmpty) {
      setState(() {
        _error = 'Please enter or scan a QR payload first.';
        _result = null;
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final data = await ApiService.analyzePayload(payload);

      if (data != null && data["result"] != null) {
        final result = data["result"] as Map<String, dynamic>;

        await HistoryService.saveEntry(payload: payload, result: result);
        await _loadHistory();

        setState(() {
          _result = result;
        });

        // 🔥 SECURITY DECISION
        _handleSecurityDecision(result, payload);
      } else {
        setState(() {
          _error = "No result returned from API";
        });
      }
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

  // =============================
  // 📷 SCANNER
  // =============================
  Future<void> _openScanner() async {
    final scannedPayload = await Navigator.push<String>(
      context,
      MaterialPageRoute(
        builder: (_) => const QRScannerScreen(),
      ),
    );

    if (scannedPayload != null && scannedPayload.trim().isNotEmpty) {
      final payload = scannedPayload.trim();
      _controller.text = payload;

      setState(() {
        _loading = true;
        _error = null;
        _result = null;
      });

      try {
        final data = await ApiService.analyzePayload(payload);

        if (data != null && data["result"] != null) {
          final result = data;

          await HistoryService.saveEntry(payload: payload, result: result);
          await _loadHistory();

          setState(() {
            _result = result;
          });

          // 🔥 SECURITY DECISION
          _handleSecurityDecision(result, payload);
        }
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
  }

  void _clearAll() {
    setState(() {
      _controller.clear();
      _error = null;
      _result = null;
    });
  }

  Color _verdictColor(String verdict) {
    switch (verdict.toUpperCase()) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  Widget _buildSummary(Map<String, dynamic> result) {
    final verdict = result['verdict'] ?? 'LOW';
    final score = result['risk_score'] ?? 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              verdict,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: _verdictColor(verdict),
              ),
            ),
            const SizedBox(height: 8),
            Text("Risk Score: $score / 100"),
          ],
        ),
      ),
    );
  }

  Widget _buildFakeQR(Map<String, dynamic> result) {
    if (!result.containsKey("fake_qr")) return const SizedBox();

    final fake = result["fake_qr"];

    return Card(
      color: Colors.red.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text("Fake QR Detection",
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text("Score: ${fake["fake_qr_score"]}"),
            Text("Risk: ${fake["risk_level"]}"),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;

    return Scaffold(
      appBar: AppBar(title: const Text("QRShilde")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: "QR Payload",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _loading ? null : _analyze,
                    child: const Text("Analyze"),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _openScanner,
                    child: const Text("Scan"),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 10),

            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),

            if (result != null) ...[
              _buildSummary(result),
              _buildFakeQR(result),
            ],
          ],
        ),
      ),
    );
  }
}