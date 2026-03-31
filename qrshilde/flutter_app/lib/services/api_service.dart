import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // 🔥 IP اللابتوب الصحيح
  static const String baseUrl = "http://192.168.100.38:8000";

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

      print("UPLOAD STATUS: ${res.statusCode}");

      if (res.statusCode == 200) {
        final body = await res.stream.bytesToString();
        print("UPLOAD BODY: $body");

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
  // 🔍 Analyze
  // =============================
  static Future<Map<String, dynamic>?> analyze(
      String payload, String? imagePath) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "payload": payload,
          if (imagePath != null) "image_path": imagePath,
        }),
      );

      // 🔥 Debug
      print("ANALYZE STATUS: ${res.statusCode}");
      print("ANALYZE BODY: ${res.body}");

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);

        print("API DATA: $data");

        // ✅ رجّع البيانات مباشرة بدون شروط
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
  // 🔄 Analyze Payload Only
  // =============================
  static Future<Map<String, dynamic>?> analyzePayload(
      String payload) async {
    return await analyze(payload, null);
  }
}