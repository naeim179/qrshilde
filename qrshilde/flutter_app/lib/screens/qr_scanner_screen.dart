import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:typed_data';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  final MobileScannerController controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
    torchEnabled: false,
  );

  bool _handled = false;

  void _handleDetection(BarcodeCapture capture) async {
    if (_handled) return;
    if (capture.barcodes.isEmpty) return;

    final barcode = capture.barcodes.first;
    final String? rawValue = barcode.rawValue;

    if (rawValue == null || rawValue.trim().isEmpty) return;

    _handled = true;
    controller.stop();

    if (!mounted) return;

    // ✅ رجّع الـ payload مباشرة للـ main screen يحلله
    Navigator.pop(context, rawValue.trim());
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final helperText = kIsWeb
        ? 'Web camera preview may be unstable. Android is recommended.'
        : 'وجّه الكاميرا على الـ QR Code';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan QR Code'),
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: controller,
            onDetect: _handleDetection,
          ),
          Align(
            alignment: Alignment.topCenter,
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.55),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                helperText,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white),
              ),
            ),
          ),
          // إطار توجيه للمستخدم
          Center(
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.green, width: 3),
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  backgroundColor: Colors.black54,
                  foregroundColor: Colors.white,
                ),
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.keyboard_return),
                label: const Text('Back'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}