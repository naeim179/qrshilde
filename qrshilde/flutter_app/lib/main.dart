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
    final verdict = (result['verdict'] ?? 'SAFE').toString().toUpperCase();

    // ✅ يدعم HIGH/MEDIUM/LOW و MALICIOUS/SUSPICIOUS/SAFE
    final isMalicious  = verdict == "MALICIOUS" || verdict == "HIGH";
    final isSuspicious = verdict == "SUSPICIOUS" || verdict == "MEDIUM";

    if (isMalicious) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text("🚨 خطر عالي"),
          content: const Text("هذا الـ QR Code خطير. تم حظر الوصول."),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("موافق"),
            ),
          ],
        ),
      );
    } else if (isSuspicious) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text("⚠️ تحذير"),
          content: const Text("هذا الـ QR قد يكون غير آمن. هل تريد المتابعة؟"),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("إلغاء"),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _openPayload(payload);
              },
              child: const Text("متابعة"),
            ),
          ],
        ),
      );
    } else {
      _openPayload(payload);
    }
  }

  // =============================
  // 🔗 OPEN PAYLOAD
  // =============================
  Future<void> _openPayload(String payload) async {
    if (payload.startsWith("http")) {
      await Clipboard.setData(ClipboardData(text: payload));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("تم نسخ الرابط بأمان")),
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
        _error = 'الرجاء إدخال محتوى الـ QR أولاً.';
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

      if (data != null) {
        await HistoryService.saveEntry(payload: payload, result: data);
        await _loadHistory();

        setState(() {
          _result = data;
        });

        _handleSecurityDecision(data, payload);
      } else {
        setState(() {
          _error = "لم يتم استقبال نتيجة من الـ API";
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

        if (data != null) {
          await HistoryService.saveEntry(payload: payload, result: data);
          await _loadHistory();

          setState(() {
            _result = data;
          });

          _handleSecurityDecision(data, payload);
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

  // =============================
  // 🎨 COLORS & ICONS
  // =============================
  Color _verdictColor(String verdict) {
    switch (verdict.toUpperCase()) {
      case 'MALICIOUS':
      case 'HIGH':
        return Colors.red;
      case 'SUSPICIOUS':
      case 'MEDIUM':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  IconData _verdictIcon(String verdict) {
    switch (verdict.toUpperCase()) {
      case 'MALICIOUS':
      case 'HIGH':
        return Icons.dangerous;
      case 'SUSPICIOUS':
      case 'MEDIUM':
        return Icons.warning_amber;
      default:
        return Icons.verified;
    }
  }

  String _verdictLabel(String verdict) {
    switch (verdict.toUpperCase()) {
      case 'MALICIOUS':
      case 'HIGH':
        return 'MALICIOUS';
      case 'SUSPICIOUS':
      case 'MEDIUM':
        return 'SUSPICIOUS';
      default:
        return 'SAFE';
    }
  }

  // =============================
  // 🧱 UI WIDGETS
  // =============================
  Widget _buildSummary(Map<String, dynamic> result) {
    final verdict = (result['verdict'] ?? 'SAFE').toString();

    // ✅ FIX: API returns "risk_score" (int 0–100), not "final_score" (double 0.0–1.0)
    final score = (result['risk_score'] as num? ?? 0).toInt();

    final color = _verdictColor(verdict);
    final label = _verdictLabel(verdict);

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(_verdictIcon(verdict), size: 48, color: color),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: score / 100,
              color: color,
              backgroundColor: Colors.grey.shade200,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 6),
            Text("Risk Score: $score / 100"),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(String title, String content, IconData icon) {
    if (content.isEmpty) return const SizedBox.shrink();
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 22, color: Colors.indigo),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 4),
                  Text(content, style: const TextStyle(fontSize: 13)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;

    return Scaffold(
      appBar: AppBar(
        title: const Text("QRShilde"),
        actions: [
          if (result != null)
            IconButton(
              icon: const Icon(Icons.clear),
              onPressed: _clearAll,
            )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: "QR Payload",
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: _clearAll,
                ),
              ),
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _loading ? null : _analyze,
                    icon: _loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.search),
                    label: const Text("Analyze"),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _openScanner,
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text("Scan"),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 10),

            if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(_error!,
                          style: const TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              ),

            if (result != null) ...[
              const SizedBox(height: 10),
              _buildSummary(result),
              const SizedBox(height: 10),
              _buildInfoCard("What it is",    result["what_it_is"]    ?? "", Icons.info_outline),
              _buildInfoCard("What happens",  result["what_happens"]  ?? "", Icons.play_circle_outline),
              _buildInfoCard("Why dangerous", result["why_dangerous"] ?? "", Icons.security),
              _buildInfoCard("What to do",    result["what_to_do"]    ?? "", Icons.check_circle_outline),
            ],
          ],
        ),
      ),
    );
  }
}