import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  final MobileScannerController controller = MobileScannerController();
  bool _handled = false;

  void _handleDetection(BarcodeCapture capture) {
    if (_handled) return;

    final Barcode? barcode =
        capture.barcodes.isNotEmpty ? capture.barcodes.first : null;

    final String? value = barcode?.rawValue;

    if (value == null || value.trim().isEmpty) {
      return;
    }

    _handled = true;
    Navigator.pop(context, value.trim());
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final helperText = kIsWeb
        ? 'Web camera preview may be unstable. Android is recommended for live scanning.'
        : 'Point the camera at a QR code to scan and analyze it.';

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
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: OutlinedButton.icon(
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