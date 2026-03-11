import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:http/http.dart' as http;

// ignore: invalid_use_of_internal_member  // Or use this if the lint persists
class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();  // Keep private
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  final String backendUrl = 'http://localhost:8000/analyze';  // Your backend URL

  Future<void> _sendImageToBackend(Uint8List imageBytes) async {
    try {
      final response = await http.post(
        Uri.parse(backendUrl),
        headers: {'Content-Type': 'application/octet-stream'},
        body: imageBytes,
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (!mounted) return;  // Check if mounted before using context
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Analysis Result'),
            content: Text(
              'Threat: ${result['analysis']}\n'
              'Payload: ${result['payload'] ?? 'None'}\n'
              'Type: ${result['payload_type'] ?? 'Unknown'}\n'
              'Stego: ${result['stego_detected'] ? 'Yes' : 'No'}',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('OK'),
              ),
            ],
          ),
        );
      } else {
        if (!mounted) return;
        _showError('Error: ${response.statusCode}');
      }
    } catch (e) {
      if (!mounted) return;
      _showError('Failed to send image: $e');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('QR Scanner')),
      body: MobileScanner(
        onDetect: (capture) {
          final Uint8List? imageBytes = capture.image;
          if (imageBytes != null) {
            _sendImageToBackend(imageBytes);
          } else {
            _showError('No image captured');
          }
        },
      ),
    );
  }
}