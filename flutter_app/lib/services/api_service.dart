import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // ⚠️ غيّر حسب البيئة
  static const String baseUrl = "http://127.0.0.1:8000";

  // =============================
  // 📤 Upload Image
  // =============================
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
      } else {
        print("Upload failed: ${res.statusCode}");
      }
    } catch (e) {
      print("Upload error: $e");
    }
    return null;
  }

  // =============================
  // 🔍 Analyze (NEW CLEAN API)
  // =============================
  static Future<Map<String, dynamic>?> analyze(
      String payload, String? imagePath) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "payload": payload,
          if (imagePath != null) "image_path": imagePath, // 🔥 optional clean
        }),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);

        // 🔥 مهم: رجّع data مباشرة (بدون result)
        return data;
      } else {
        print("Analyze failed: ${res.statusCode}");
      }
    } catch (e) {
      print("Analyze error: $e");
    }
    return null;
  }

  // =============================
  // 🔄 Backward Compatibility
  // =============================
  static Future<Map<String, dynamic>?> analyzePayload(
      String payload) async {
    return await analyze(payload, null);
  }
}