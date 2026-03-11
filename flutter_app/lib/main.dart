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
      final result = data['result'] as Map<String, dynamic>?;

      if (result != null) {
        await HistoryService.saveEntry(payload: payload, result: result);
        await _loadHistory();
      }

      setState(() {
        _result = result;
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

  Future<void> _openScanner() async {
    final scannedPayload = await Navigator.push<String>(
      context,
      MaterialPageRoute(
        builder: (_) => const QRScannerScreen(),
      ),
    );

    if (scannedPayload != null && scannedPayload.trim().isNotEmpty) {
      _controller.text = scannedPayload.trim();
      await _analyze();
    }
  }

  Future<void> _copyReport() async {
    final result = _result;
    if (result == null) return;

    final report = _buildReportText(result);

    await Clipboard.setData(ClipboardData(text: report));
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Report copied')),
    );
  }

  Future<void> _clearHistory() async {
    await HistoryService.clearHistory();
    await _loadHistory();
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('History cleared')),
    );
  }

  Future<void> _deleteHistoryItem(String id) async {
    await HistoryService.deleteEntry(id);
    await _loadHistory();
  }

  void _clearAll() {
    setState(() {
      _controller.clear();
      _error = null;
      _result = null;
    });
  }

  void _loadFromHistory(Map<String, dynamic> entry) {
    final payload = (entry['payload'] ?? '').toString();
    final result = entry['result'] as Map<String, dynamic>?;

    setState(() {
      _controller.text = payload;
      _result = result != null ? Map<String, dynamic>.from(result) : null;
      _error = null;
    });
  }

  String _buildReportText(Map<String, dynamic> result) {
    final verdict = (result['verdict'] ?? '-').toString();
    final riskScore = (result['risk_score'] ?? '-').toString();
    final payloadType = (result['payload_type'] ?? '-').toString();
    final confidence = (result['confidence'] ?? '-').toString();
    final recommendation = (result['recommendation'] ?? '-').toString();
    final findings = (result['findings'] as List?) ?? [];
    final benign = (result['benign'] as List?) ?? [];
    final knownMatch = result['known_match'] as Map<String, dynamic>?;

    final lines = <String>[
      'QRShilde Report',
      'Verdict: $verdict',
      'Risk Score: $riskScore / 100',
      'Payload Type: $payloadType',
      'Confidence: $confidence',
      'Recommendation: $recommendation',
      '',
    ];

    if (knownMatch != null) {
      lines.add('Threat Memory');
      lines.add('Match Type: ${knownMatch['match_type'] ?? '-'}');
      lines.add('Matched Value: ${knownMatch['matched_value'] ?? '-'}');
      lines.add('Seen Count: ${knownMatch['seen_count'] ?? 0}');
      lines.add('Last Verdict: ${knownMatch['last_verdict'] ?? '-'}');
      lines.add('Message: ${knownMatch['message'] ?? '-'}');
      lines.add('');
    }

    lines.add('Findings:');
    if (findings.isEmpty) {
      lines.add('- None');
    } else {
      for (final item in findings) {
        lines.add('- $item');
      }
    }

    lines.add('');
    lines.add('Benign Signals:');
    if (benign.isEmpty) {
      lines.add('- None');
    } else {
      for (final item in benign) {
        lines.add('- $item');
      }
    }

    return lines.join('\n');
  }

  Color _verdictColor(String verdict) {
    switch (verdict.toUpperCase()) {
      case 'CRITICAL':
        return Colors.red.shade800;
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  String _formatDate(String? iso) {
    if (iso == null || iso.isEmpty) return '-';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }

  Widget _buildHeaderCard() {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'QRShilde Security Analyzer',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Analyze QR payloads, keep history, and warn users when a known threat appears again.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputCard() {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              minLines: 3,
              maxLines: 6,
              decoration: const InputDecoration(
                labelText: 'QR Payload',
                hintText: 'Paste decoded QR content here',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _loading ? null : _analyze,
                    icon: _loading
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.security),
                    label: const Text('Analyze'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _loading ? null : _openScanner,
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text('Scan QR'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _result == null ? null : _copyReport,
                    icon: const Icon(Icons.copy),
                    label: const Text('Copy Report'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _clearAll,
                    icon: const Icon(Icons.clear),
                    label: const Text('Clear'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKnownMatchCard(Map<String, dynamic> result) {
    final knownMatch = result['known_match'] as Map<String, dynamic>?;
    if (knownMatch == null) return const SizedBox.shrink();

    return Card(
      elevation: 0,
      color: Colors.amber.withOpacity(0.12),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.memory, color: Colors.orange),
                SizedBox(width: 8),
                Text(
                  'Known Threat Memory',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(knownMatch['message']?.toString() ?? 'Previously seen indicator'),
            const SizedBox(height: 8),
            Text('Match Type: ${knownMatch['match_type'] ?? '-'}'),
            Text('Matched Value: ${knownMatch['matched_value'] ?? '-'}'),
            Text('Seen Count: ${knownMatch['seen_count'] ?? 0}'),
            Text('Last Verdict: ${knownMatch['last_verdict'] ?? '-'}'),
            Text('Last Seen: ${knownMatch['last_seen'] ?? '-'}'),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic> result) {
    final verdict = (result['verdict'] ?? 'LOW').toString();
    final riskScore = (result['risk_score'] ?? 0) as num;
    final payloadType = (result['payload_type'] ?? '-').toString();
    final confidence = (result['confidence'] ?? '-').toString();
    final recommendation = (result['recommendation'] ?? '-').toString();

    final color = _verdictColor(verdict);
    final progress = (riskScore.toDouble().clamp(0, 100)) / 100;

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 12,
              runSpacing: 12,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Chip(
                  backgroundColor: color.withOpacity(0.12),
                  side: BorderSide(color: color.withOpacity(0.35)),
                  label: Text(
                    verdict,
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Text(
                  'Payload Type: $payloadType',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  'Confidence: $confidence',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'Risk Score: ${riskScore.toInt()} / 100',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: progress,
              minHeight: 10,
              borderRadius: BorderRadius.circular(10),
            ),
            const SizedBox(height: 16),
            Text(
              'Recommendation',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 6),
            Text(recommendation),
          ],
        ),
      ),
    );
  }

  Widget _buildListCard({
    required String title,
    required List items,
    required IconData icon,
    Color? iconColor,
  }) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: iconColor),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (items.isEmpty)
              const Text('- None')
            else
              ...items.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('• '),
                        Expanded(child: Text(item.toString())),
                      ],
                    ),
                  )),
          ],
        ),
      ),
    );
  }

  Widget _buildHistorySection() {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.history),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'History',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ),
                if (_history.isNotEmpty)
                  TextButton.icon(
                    onPressed: _clearHistory,
                    icon: const Icon(Icons.delete_sweep),
                    label: const Text('Clear History'),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            if (_history.isEmpty)
              const Text('No saved analyses yet.')
            else
              ..._history.map((entry) {
                final result = entry['result'] as Map<String, dynamic>?;
                final payload = (entry['payload'] ?? '').toString();
                final verdict = (result?['verdict'] ?? '-').toString();
                final risk = (result?['risk_score'] ?? 0).toString();
                final savedAt = _formatDate(entry['saved_at']?.toString());
                final color = _verdictColor(verdict);

                return Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: ListTile(
                    onTap: () => _loadFromHistory(entry),
                    title: Text(
                      payload,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text('Saved: $savedAt'),
                    leading: CircleAvatar(
                      backgroundColor: color.withOpacity(0.12),
                      child: Text(
                        verdict.isNotEmpty ? verdict[0] : '?',
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    trailing: Wrap(
                      spacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text('$risk/100'),
                        IconButton(
                          tooltip: 'Delete',
                          onPressed: () => _deleteHistoryItem(
                            (entry['id'] ?? '').toString(),
                          ),
                          icon: const Icon(Icons.delete_outline),
                        ),
                      ],
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildResultSection(Map<String, dynamic> result) {
    final findings = (result['findings'] as List?) ?? [];
    final benign = (result['benign'] as List?) ?? [];

    return Column(
      children: [
        _buildKnownMatchCard(result),
        if ((result['known_match'] as Map<String, dynamic>?) != null)
          const SizedBox(height: 12),
        _buildSummaryCard(result),
        const SizedBox(height: 12),
        _buildListCard(
          title: 'Findings',
          items: findings,
          icon: Icons.warning_amber_rounded,
          iconColor: Colors.orange,
        ),
        const SizedBox(height: 12),
        _buildListCard(
          title: 'Benign Signals',
          items: benign,
          icon: Icons.verified_outlined,
          iconColor: Colors.green,
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;

    return Scaffold(
      appBar: AppBar(
        title: const Text('QRShilde'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight - 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildHeaderCard(),
                    const SizedBox(height: 12),
                    _buildInputCard(),
                    const SizedBox(height: 12),
                    if (_error != null)
                      Card(
                        color: Colors.red.withOpacity(0.08),
                        elevation: 0,
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Text(
                            _error!,
                            style: const TextStyle(color: Colors.red),
                          ),
                        ),
                      ),
                    if (result != null) ...[
                      const SizedBox(height: 12),
                      _buildResultSection(result),
                    ],
                    const SizedBox(height: 12),
                    _buildHistorySection(),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}