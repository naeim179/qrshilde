import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class HistoryService {
  static const String _key = 'qrshilde_history_v1';
  static const int _maxItems = 50;

  static Future<List<Map<String, dynamic>>> loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_key) ?? [];

    return raw
        .map((item) => Map<String, dynamic>.from(jsonDecode(item)))
        .toList();
  }

  static Future<void> saveEntry({
    required String payload,
    required Map<String, dynamic> result,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await loadHistory();

    final entry = <String, dynamic>{
      'id': DateTime.now().millisecondsSinceEpoch.toString(),
      'saved_at': DateTime.now().toIso8601String(),
      'payload': payload,
      'result': result,
    };

    final filtered = current.where((item) {
      final itemPayload = (item['payload'] ?? '').toString();
      final itemResult = item['result'] as Map<String, dynamic>?;
      final itemScore = itemResult?['risk_score'];
      final newScore = result['risk_score'];
      return !(itemPayload == payload && itemScore == newScore);
    }).toList();

    filtered.insert(0, entry);

    if (filtered.length > _maxItems) {
      filtered.removeRange(_maxItems, filtered.length);
    }

    await prefs.setStringList(
      _key,
      filtered.map((e) => jsonEncode(e)).toList(),
    );
  }

  static Future<void> deleteEntry(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await loadHistory();
    final updated =
        current.where((item) => (item['id'] ?? '').toString() != id).toList();

    await prefs.setStringList(
      _key,
      updated.map((e) => jsonEncode(e)).toList(),
    );
  }

  static Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}