import 'package:flutter/material.dart';

class AnalysisResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;
  final String payload;

  const AnalysisResultScreen({
    super.key,
    required this.result,
    required this.payload,
  });

  Color _getColor(String verdict) {
    switch (verdict.toUpperCase()) {
      case "MALICIOUS":
      case "HIGH":
        return Colors.red;
      case "SUSPICIOUS":
      case "MEDIUM":
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  IconData _getIcon(String verdict) {
    switch (verdict.toUpperCase()) {
      case "MALICIOUS":
      case "HIGH":
        return Icons.dangerous;
      case "SUSPICIOUS":
      case "MEDIUM":
        return Icons.warning_amber_rounded;
      default:
        return Icons.verified;
    }
  }

  String _getLabel(String verdict) {
    switch (verdict.toUpperCase()) {
      case "MALICIOUS":
      case "HIGH":
        return "MALICIOUS";
      case "SUSPICIOUS":
      case "MEDIUM":
        return "SUSPICIOUS";
      default:
        return "SAFE";
    }
  }

  @override
  Widget build(BuildContext context) {
    final verdict = (result["verdict"] ?? "SAFE").toString();

    // ✅ FIX: API returns "risk_score" (0–100), not "final_score" (0.0–1.0)
    final score = (result["risk_score"] as num? ?? 0).toInt();

    final findings = result["findings"] as List<dynamic>? ?? [];
    final confidence = result["confidence"] as num? ?? 0;
    final color = _getColor(verdict);
    final label = _getLabel(verdict);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        title: const Text("QR Security Result"),
        centerTitle: true,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [

            // ── HEADER CARD ───────────────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [color, color.withOpacity(0.6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Icon(_getIcon(verdict), size: 64, color: Colors.white),
                  const SizedBox(height: 12),
                  Text(
                    label,
                    style: const TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Risk score bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: LinearProgressIndicator(
                      value: score / 100,
                      minHeight: 10,
                      color: Colors.white,
                      backgroundColor: Colors.white24,
                    ),
                  ),

                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        "Risk Score: $score / 100",
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        "Confidence: ${(confidence * 100).toInt()}%",
                        style: const TextStyle(color: Colors.white70),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // ── FINDINGS ─────────────────────────────────────────────────
            if (findings.isNotEmpty) ...[
              _sectionTitle("⚠️ Threat Indicators"),
              const SizedBox(height: 8),
              Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: findings.map((f) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          children: [
                            Icon(Icons.circle, size: 8, color: color),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                f.toString(),
                                style: const TextStyle(fontSize: 14),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // ── INFO CARDS ────────────────────────────────────────────────
            _sectionTitle("📋 QR Content"),
            const SizedBox(height: 8),
            _infoCard(payload, icon: Icons.qr_code),
            const SizedBox(height: 12),

            if ((result["what_it_is"] ?? "").toString().isNotEmpty) ...[
              _sectionTitle("🔍 What it is"),
              const SizedBox(height: 8),
              _infoCard(result["what_it_is"].toString()),
              const SizedBox(height: 12),
            ],

            if ((result["what_happens"] ?? "").toString().isNotEmpty) ...[
              _sectionTitle("⚡ What happens"),
              const SizedBox(height: 8),
              _infoCard(result["what_happens"].toString()),
              const SizedBox(height: 12),
            ],

            if ((result["why_dangerous"] ?? "").toString().isNotEmpty) ...[
              _sectionTitle("☠️ Why dangerous"),
              const SizedBox(height: 8),
              _infoCard(result["why_dangerous"].toString(), highlight: true, color: color),
              const SizedBox(height: 12),
            ],

            if ((result["what_to_do"] ?? "").toString().isNotEmpty) ...[
              _sectionTitle("✅ What to do"),
              const SizedBox(height: 8),
              _infoCard(result["what_to_do"].toString()),
              const SizedBox(height: 24),
            ],

          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.bold,
          color: Color(0xFF444444),
        ),
      ),
    );
  }

  Widget _infoCard(
    String content, {
    IconData? icon,
    bool highlight = false,
    Color color = Colors.red,
  }) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 2,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: highlight
            ? BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                color: color.withOpacity(0.06),
                border: Border.all(color: color.withOpacity(0.3)),
              )
            : null,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (icon != null) ...[
              Icon(icon, color: Colors.grey, size: 20),
              const SizedBox(width: 10),
            ],
            Expanded(
              child: Text(
                content,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.5,
                  color: highlight ? color.withOpacity(0.9) : Colors.black87,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}