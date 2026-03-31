import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
      case "HIGH":
        return Colors.red;
      case "MEDIUM":
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  IconData _getIcon(String verdict) {
    switch (verdict.toUpperCase()) {
      case "HIGH":
        return Icons.dangerous;
      case "MEDIUM":
        return Icons.warning;
      default:
        return Icons.verified;
    }
  }

  @override
  Widget build(BuildContext context) {
    final verdict = result["verdict"] ?? "LOW";
    final score = result["risk_score"] ?? 0;
    final findings = List<String>.from(result["findings"] ?? []);

    final color = _getColor(verdict);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Security Analysis"),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [

            // 🔥 HEADER (Gradient)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    color.withOpacity(0.7),
                    color.withOpacity(0.4),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Icon(
                    _getIcon(verdict),
                    size: 60,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 10),
                  Text(
                    verdict,
                    style: const TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 15),

                  // 📊 Progress
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: LinearProgressIndicator(
                      value: score / 100,
                      minHeight: 12,
                      color: Colors.white,
                      backgroundColor: Colors.white24,
                    ),
                  ),

                  const SizedBox(height: 10),
                  Text(
                    "Risk Score: $score / 100",
                    style: const TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // 🔗 Payload
            _sectionCard(
              title: "QR Content",
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SelectableText(payload),
                  const SizedBox(height: 10),

                  Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: () async {
                          await Clipboard.setData(
                              ClipboardData(text: payload));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text("Copied to clipboard")),
                          );
                        },
                        icon: const Icon(Icons.copy),
                        label: const Text("Copy"),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 15),

            // ⚠️ Findings
            _sectionCard(
              title: "Security Findings",
              child: findings.isEmpty
                  ? const Text("No issues detected")
                  : Column(
                      children: findings.map((f) {
                        return ListTile(
                          leading: Icon(Icons.error, color: color),
                          title: Text(f),
                        );
                      }).toList(),
                    ),
            ),

            const SizedBox(height: 15),

            // 🧠 Fake QR
            if (result.containsKey("fake_qr"))
              _sectionCard(
                title: "Fake QR Detection",
                child: Column(
                  children: [
                    Text(
                        "Score: ${result["fake_qr"]["fake_qr_score"]}"),
                    Text(
                        "Risk: ${result["fake_qr"]["risk_level"]}"),
                  ],
                ),
              ),

            const SizedBox(height: 20),

            // 🔘 ACTION BUTTON
            if (verdict == "LOW")
              ElevatedButton.icon(
                onPressed: () async {
                  await Clipboard.setData(
                      ClipboardData(text: payload));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content: Text("Safe link copied")),
                  );
                },
                icon: const Icon(Icons.open_in_new),
                label: const Text("Open / Copy Link"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                ),
              ),

            if (verdict == "MEDIUM")
              ElevatedButton.icon(
                onPressed: () async {
                  await Clipboard.setData(
                      ClipboardData(text: payload));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content: Text("Proceed with caution")),
                  );
                },
                icon: const Icon(Icons.warning),
                label: const Text("Proceed Anyway"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                ),
              ),

            if (verdict == "HIGH")
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                },
                icon: const Icon(Icons.block),
                label: const Text("Blocked"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _sectionCard({required String title, required Widget child}) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            child,
          ],
        ),
      ),
    );
  }
}