import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
  // ⚠️ غير هذا العنوان إلى IP جهازك الحالي
  static const String baseUrl = "http://192.168.100.38:8000";
  // =============================
  // 🔍 Analyze QR from Image File (للمسح بالكاميرا)
  // =============================
  static Future<Map<String, dynamic>?> analyzeImage(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
      );

      var response = await request.send();
      final body = await response.stream.bytesToString();

      print("📡 Status: ${response.statusCode}");
      print("📦 Response: $body");

      if (response.statusCode == 200) {
        return jsonDecode(body);
      } else {
        print("❌ API Error: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("❌ Connection error: $e");
      return null;
    }
  }

  // =============================
  // 🔍 Analyze Payload Directly (للنص المباشر)
  // =============================
  static Future<Map<String, dynamic>?> analyzePayload(String payload) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/analyze-text-json'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'payload': payload}),
      );

      print("📡 Status: ${response.statusCode}");
      print("📦 Response: ${response.body}");

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print("❌ API Error: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("❌ Connection error: $e");
      return null;
    }
  }

  // =============================
  // 🩺 Health Check
  // =============================
  static Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}