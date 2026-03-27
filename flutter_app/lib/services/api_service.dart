import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://127.0.0.1:8000";

  // رفع صورة
  static Future<String?> uploadImage(File file) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/upload'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', file.path),
      );

      var res = await request.send();

      if (res.statusCode == 200) {
        final body = await res.stream.bytesToString();
        final data = jsonDecode(body);
        return data["image_path"];
      }
    } catch (e) {
      print("Upload error: $e");
    }
    return null;
  }

  // تحليل QR
  static Future<Map<String, dynamic>?> analyze(
      String payload, String? imagePath) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "payload": payload,
          "image_path": imagePath
        }),
      );

      if (res.statusCode == 200) {
        return jsonDecode(res.body);
      }
    } catch (e) {
      print("Analyze error: $e");
    }
    return null;
  }

  // دعم الكود القديم (مهم عشان ما يكسر main.dart)
  static Future<Map<String, dynamic>?> analyzePayload(
      String payload) async {
    return await analyze(payload, null);
  }
}