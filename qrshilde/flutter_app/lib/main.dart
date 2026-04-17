import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'screens/qr_scanner_screen.dart';
import 'services/api_service.dart';
import 'services/history_service.dart';

// ══════════════════════════════════════════════════════
// THEME SYSTEM
// ══════════════════════════════════════════════════════

enum AppThemeMode { dark, light, eyeCare }

class AppThemes {
  // Dark
  static const darkBg         = Color(0xFF0A0E1A);
  static const darkSurface    = Color(0xFF111827);
  static const darkCard       = Color(0xFF1A2235);
  static const darkBorder     = Color(0xFF2A3450);
  static const darkAccent     = Color(0xFF3B82F6);
  static const darkAccentGlow = Color(0x333B82F6);
  static const darkText       = Color(0xFFE2E8F0);
  static const darkTextSub    = Color(0xFF94A3B8);
  // Light
  static const lightBg         = Color(0xFFF0F4FF);
  static const lightSurface    = Color(0xFFFFFFFF);
  static const lightCard       = Color(0xFFFFFFFF);
  static const lightBorder     = Color(0xFFDDE3F0);
  static const lightAccent     = Color(0xFF2563EB);
  static const lightAccentGlow = Color(0x222563EB);
  static const lightText       = Color(0xFF1E293B);
  static const lightTextSub    = Color(0xFF64748B);
  // Eye Care
  static const eyeBg         = Color(0xFF1C1610);
  static const eyeSurface    = Color(0xFF261E13);
  static const eyeCard       = Color(0xFF2E2416);
  static const eyeBorder     = Color(0xFF3D3020);
  static const eyeAccent     = Color(0xFFD4A017);
  static const eyeAccentGlow = Color(0x33D4A017);
  static const eyeText       = Color(0xFFF5E6C8);
  static const eyeTextSub    = Color(0xFFB8956A);
}

class TC {
  final Color bg, surface, card, border, accent, ag, text, sub;
  const TC({required this.bg, required this.surface, required this.card,
    required this.border, required this.accent, required this.ag,
    required this.text, required this.sub});

  static TC of(AppThemeMode m) {
    switch (m) {
      case AppThemeMode.light:
        return const TC(bg: AppThemes.lightBg, surface: AppThemes.lightSurface,
          card: AppThemes.lightCard, border: AppThemes.lightBorder,
          accent: AppThemes.lightAccent, ag: AppThemes.lightAccentGlow,
          text: AppThemes.lightText, sub: AppThemes.lightTextSub);
      case AppThemeMode.eyeCare:
        return const TC(bg: AppThemes.eyeBg, surface: AppThemes.eyeSurface,
          card: AppThemes.eyeCard, border: AppThemes.eyeBorder,
          accent: AppThemes.eyeAccent, ag: AppThemes.eyeAccentGlow,
          text: AppThemes.eyeText, sub: AppThemes.eyeTextSub);
      default:
        return const TC(bg: AppThemes.darkBg, surface: AppThemes.darkSurface,
          card: AppThemes.darkCard, border: AppThemes.darkBorder,
          accent: AppThemes.darkAccent, ag: AppThemes.darkAccentGlow,
          text: AppThemes.darkText, sub: AppThemes.darkTextSub);
    }
  }
}

// ══════════════════════════════════════════════════════
// APP
// ══════════════════════════════════════════════════════

void main() => runApp(const QRShildeApp());

class QRShildeApp extends StatefulWidget {
  const QRShildeApp({super.key});
  @override State<QRShildeApp> createState() => _QRShildeAppState();
}

class _QRShildeAppState extends State<QRShildeApp> {
  AppThemeMode _mode = AppThemeMode.dark;

  @override
  Widget build(BuildContext context) {
    final c = TC.of(_mode);
    return MaterialApp(
      title: 'QRShilde',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: c.bg,
        colorScheme: ColorScheme.dark(primary: c.accent, surface: c.surface),
      ),
      home: AnalyzeScreen(mode: _mode, onMode: (m) => setState(() => _mode = m)),
    );
  }
}

// ══════════════════════════════════════════════════════
// ANALYZE SCREEN
// ══════════════════════════════════════════════════════

class AnalyzeScreen extends StatefulWidget {
  final AppThemeMode mode;
  final ValueChanged<AppThemeMode> onMode;
  const AnalyzeScreen({super.key, required this.mode, required this.onMode});
  @override State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> with TickerProviderStateMixin {
  final _ctrl = TextEditingController();
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;
  late AnimationController _pulse, _reveal;
  late Animation<double> _revealAnim;

  @override
  void initState() {
    super.initState();
    _pulse  = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);
    _reveal = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _revealAnim = CurvedAnimation(parent: _reveal, curve: Curves.easeOutCubic);
    _ctrl.addListener(() => setState(() {}));
  }

  @override void dispose() { _pulse.dispose(); _reveal.dispose(); _ctrl.dispose(); super.dispose(); }

  TC get c => TC.of(widget.mode);

  // Verdict helpers
  Color _vc(String v) {
    switch (v.toUpperCase()) {
      case 'MALICIOUS': case 'HIGH':    return const Color(0xFFEF4444);
      case 'SUSPICIOUS': case 'MEDIUM': return const Color(0xFFF97316);
      default:                          return const Color(0xFF22C55E);
    }
  }
  IconData _vi(String v) {
    switch (v.toUpperCase()) {
      case 'MALICIOUS': case 'HIGH':    return Icons.gpp_bad_rounded;
      case 'SUSPICIOUS': case 'MEDIUM': return Icons.gpp_maybe_rounded;
      default:                          return Icons.verified_user_rounded;
    }
  }
  String _vl(String v) {
    switch (v.toUpperCase()) {
      case 'MALICIOUS': case 'HIGH':    return 'MALICIOUS';
      case 'SUSPICIOUS': case 'MEDIUM': return 'SUSPICIOUS';
      default:                          return 'SAFE';
    }
  }
  String _vd(String v) {
    switch (v.toUpperCase()) {
      case 'MALICIOUS': case 'HIGH':    return 'Threat Detected — Do Not Proceed';
      case 'SUSPICIOUS': case 'MEDIUM': return 'Proceed with Caution';
      default:                          return 'No Threats Found';
    }
  }

  // Decision
  void _decide(Map<String, dynamic> result, String payload) {
    final v = (result['verdict'] ?? 'SAFE').toString().toUpperCase();
    if (v == 'MALICIOUS' || v == 'HIGH') {
      _dialog(Icons.gpp_bad_rounded, const Color(0xFFEF4444), "Threat Detected",
        "This QR code is dangerous. Access has been blocked.",
        [_dBtn("Understood", () => Navigator.pop(context), c.accent)]);
    } else if (v == 'SUSPICIOUS' || v == 'MEDIUM') {
      _dialog(Icons.gpp_maybe_rounded, const Color(0xFFF97316), "Warning",
        "This QR code may be unsafe. Proceed anyway?",
        [_dBtn("Cancel", () => Navigator.pop(context), c.sub),
         _dBtn("Proceed", () { Navigator.pop(context); _open(payload); },
           const Color(0xFFF97316))]);
    } else {
      _open(payload);
    }
  }

  void _dialog(IconData icon, Color color, String title, String msg, List<Widget> actions) {
    showDialog(context: context, builder: (_) => Dialog(
      backgroundColor: c.card,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: Padding(padding: const EdgeInsets.all(28), child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 64, height: 64,
            decoration: BoxDecoration(color: color.withOpacity(0.15), shape: BoxShape.circle),
            child: Icon(icon, color: color, size: 36)),
          const SizedBox(height: 16),
          Text(title, style: TextStyle(color: c.text, fontSize: 20, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          Text(msg, textAlign: TextAlign.center,
            style: TextStyle(color: c.sub, fontSize: 14, height: 1.5)),
          const SizedBox(height: 24),
          Row(mainAxisAlignment: MainAxisAlignment.end, children: actions),
        ],
      )),
    ));
  }

  Widget _dBtn(String label, VoidCallback onTap, Color color) => TextButton(
    onPressed: onTap,
    style: TextButton.styleFrom(foregroundColor: color,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
    child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600)));

  Future<void> _open(String payload) async {
    if (payload.startsWith("http")) {
      await Clipboard.setData(ClipboardData(text: payload));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text("Link copied safely to clipboard"),
        backgroundColor: const Color(0xFF22C55E),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))));
    }
  }

  Future<void> _analyze() async {
    final payload = _ctrl.text.trim();
    if (payload.isEmpty) { setState(() { _error = 'Please enter QR content first.'; _result = null; }); return; }
    setState(() { _loading = true; _error = null; _result = null; });
    _reveal.reset();
    try {
      final data = await ApiService.analyzePayload(payload);
      if (data != null) {
        await HistoryService.saveEntry(payload: payload, result: data);
        setState(() { _result = data; });
        _reveal.forward();
        _decide(data, payload);
      } else { setState(() { _error = "No response received from server"; }); }
    } catch (e) { setState(() { _error = e.toString(); }); }
    finally { setState(() { _loading = false; }); }
  }

  Future<void> _scan() async {
    final p = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const QRScannerScreen()));
    if (p != null && p.trim().isNotEmpty) {
      _ctrl.text = p.trim();
      setState(() { _loading = true; _error = null; _result = null; });
      _reveal.reset();
      try {
        final data = await ApiService.analyzePayload(p.trim());
        if (data != null) {
          await HistoryService.saveEntry(payload: p.trim(), result: data);
          setState(() { _result = data; });
          _reveal.forward();
          _decide(data, p.trim());
        }
      } catch (e) { setState(() { _error = e.toString(); }); }
      finally { setState(() { _loading = false; }); }
    }
  }

  void _clear() { setState(() { _ctrl.clear(); _error = null; _result = null; }); _reveal.reset(); }

  // ══════════════════════════════════════════════════
  // BUILD
  // ══════════════════════════════════════════════════
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: c.bg,
      body: SafeArea(child: Column(children: [
        _topBar(),
        Expanded(child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _hero(),
            const SizedBox(height: 20),
            _input(),
            const SizedBox(height: 14),
            _buttons(),
            if (_error != null) ...[const SizedBox(height: 14), _errorCard()],
            if (_result != null) ...[const SizedBox(height: 24), _results()],
          ]),
        )),
      ])),
    );
  }

  // Top Bar
  Widget _topBar() => Container(
    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
    decoration: BoxDecoration(color: c.surface, border: Border(bottom: BorderSide(color: c.border))),
    child: Row(children: [
      Container(width: 34, height: 34,
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: [c.accent, c.accent.withOpacity(0.6)]),
          borderRadius: BorderRadius.circular(10)),
        child: const Icon(Icons.shield_rounded, color: Colors.white, size: 18)),
      const SizedBox(width: 10),
      Text("QRShilde", style: TextStyle(color: c.text, fontSize: 17, fontWeight: FontWeight.w800)),
      const Spacer(),
      _themeToggle(),
      if (_result != null) ...[
        const SizedBox(width: 8),
        GestureDetector(onTap: _clear, child: Container(width: 34, height: 34,
          decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(10),
            border: Border.all(color: c.border)),
          child: Icon(Icons.refresh_rounded, size: 16, color: c.sub))),
      ],
    ]),
  );

  Widget _themeToggle() => Container(
    padding: const EdgeInsets.all(3),
    decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(12),
      border: Border.all(color: c.border)),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      _tmBtn(Icons.dark_mode_rounded,  AppThemeMode.dark,    "Dark"),
      _tmBtn(Icons.light_mode_rounded, AppThemeMode.light,   "Light"),
      _tmBtn(Icons.visibility_rounded, AppThemeMode.eyeCare, "Eye Care"),
    ]),
  );

  Widget _tmBtn(IconData icon, AppThemeMode mode, String tip) {
    final active = widget.mode == mode;
    return Tooltip(message: tip, child: GestureDetector(
      onTap: () => widget.onMode(mode),
      child: AnimatedContainer(duration: const Duration(milliseconds: 200),
        width: 34, height: 28,
        decoration: BoxDecoration(
          color: active ? c.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(9)),
        child: Icon(icon, size: 15, color: active ? Colors.white : c.sub)),
    ));
  }

  // Hero
  Widget _hero() => AnimatedBuilder(animation: _pulse, builder: (_, __) {
    final p = _pulse.value;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: c.card, borderRadius: BorderRadius.circular(22),
        border: Border.all(color: c.border),
        boxShadow: [BoxShadow(color: c.ag, blurRadius: 18 + p * 12, spreadRadius: p * 2)]),
      child: Row(children: [
        Container(width: 50, height: 50,
          decoration: BoxDecoration(
            gradient: RadialGradient(colors: [c.accent, c.accent.withOpacity(0.25)]),
            borderRadius: BorderRadius.circular(14)),
          child: const Icon(Icons.qr_code_scanner_rounded, color: Colors.white, size: 26)),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text("QR Security Scanner", style: TextStyle(color: c.text, fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 3),
          Text("AI-powered threat detection engine", style: TextStyle(color: c.sub, fontSize: 11)),
        ])),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: const Color(0xFF22C55E).withOpacity(0.12),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF22C55E).withOpacity(0.35))),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 6, height: 6,
              decoration: BoxDecoration(
                color: Color.lerp(const Color(0xFF22C55E), const Color(0xFF4ADE80), p),
                shape: BoxShape.circle)),
            const SizedBox(width: 5),
            const Text("Online", style: TextStyle(
              color: Color(0xFF22C55E), fontSize: 11, fontWeight: FontWeight.w600)),
          ])),
      ]),
    );
  });

  // Input
  Widget _input() => Container(
    decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(18),
      border: Border.all(color: c.border)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(padding: const EdgeInsets.fromLTRB(14, 12, 14, 0),
        child: Row(children: [
          Icon(Icons.code_rounded, size: 13, color: c.sub),
          const SizedBox(width: 5),
          Text("QR PAYLOAD", style: TextStyle(color: c.sub, fontSize: 11,
            fontWeight: FontWeight.w700, letterSpacing: 1.0)),
        ])),
      TextField(
        controller: _ctrl,
        style: TextStyle(color: c.text, fontSize: 14, height: 1.5),
        maxLines: 3, minLines: 1,
        decoration: InputDecoration(
          hintText: "Paste QR content or tap Scan...",
          hintStyle: TextStyle(color: c.sub.withOpacity(0.45), fontSize: 13),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.fromLTRB(14, 8, 14, 10))),
      Padding(padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text("${_ctrl.text.length} chars",
            style: TextStyle(color: c.sub.withOpacity(0.35), fontSize: 10)),
          if (_ctrl.text.isNotEmpty)
            GestureDetector(onTap: _clear, child: Row(children: [
              Icon(Icons.close_rounded, size: 11, color: c.sub),
              const SizedBox(width: 3),
              Text("Clear", style: TextStyle(color: c.sub, fontSize: 11)),
            ])),
        ])),
    ]),
  );

  // Buttons
  Widget _buttons() => Row(children: [
    Expanded(flex: 3, child: GestureDetector(
      onTap: _loading ? null : _analyze,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200), height: 50,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: _loading
              ? [c.accent.withOpacity(0.4), c.accent.withOpacity(0.25)]
              : [c.accent, c.accent.withOpacity(0.72)],
            begin: Alignment.topLeft, end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(15),
          boxShadow: _loading ? [] : [BoxShadow(color: c.ag, blurRadius: 14, offset: const Offset(0, 4))]),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          if (_loading)
            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(
              strokeWidth: 2, color: Colors.white.withOpacity(0.7)))
          else
            const Icon(Icons.security_rounded, color: Colors.white, size: 19),
          const SizedBox(width: 8),
          Text(_loading ? "Analyzing..." : "Analyze",
            style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
        ]),
      ),
    )),
    const SizedBox(width: 10),
    Expanded(flex: 2, child: GestureDetector(
      onTap: _scan,
      child: Container(height: 50,
        decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(15),
          border: Border.all(color: c.border, width: 1.5)),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.qr_code_2_rounded, color: c.accent, size: 19),
          const SizedBox(width: 7),
          Text("Scan", style: TextStyle(color: c.text, fontSize: 15, fontWeight: FontWeight.w600)),
        ])),
    )),
  ]);

  // Error
  Widget _errorCard() => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: const Color(0xFFEF4444).withOpacity(0.08),
      borderRadius: BorderRadius.circular(14),
      border: Border.all(color: const Color(0xFFEF4444).withOpacity(0.3))),
    child: Row(children: [
      const Icon(Icons.error_outline_rounded, color: Color(0xFFEF4444), size: 17),
      const SizedBox(width: 8),
      Expanded(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444), fontSize: 13))),
    ]));

  // Results
  Widget _results() {
    final r       = _result!;
    final verdict = (r['verdict'] ?? 'SAFE').toString();
    final score   = (r['risk_score'] as num? ?? 0).toInt();
    final label   = _vl(verdict);
    final color   = _vc(verdict);
    final findings = r['findings'] as List<dynamic>? ?? [];
    final conf    = ((r['confidence'] as num? ?? 0) * 100).toInt();

    return FadeTransition(
      opacity: _revealAnim,
      child: SlideTransition(
        position: Tween<Offset>(begin: const Offset(0, 0.08), end: Offset.zero).animate(_revealAnim),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          _verdictCard(label, color, score, conf),
          if (findings.isNotEmpty) ...[const SizedBox(height: 12), _findingsCard(findings, color)],
          const SizedBox(height: 12),
          _infoCards(r),
        ]),
      ),
    );
  }

  Widget _verdictCard(String label, Color color, int score, int conf) => Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: c.card, borderRadius: BorderRadius.circular(22),
      border: Border.all(color: color.withOpacity(0.35), width: 1.5),
      boxShadow: [BoxShadow(color: color.withOpacity(0.10), blurRadius: 20, spreadRadius: 2)]),
    child: Column(children: [
      Row(children: [
        Container(width: 50, height: 50,
          decoration: BoxDecoration(color: color.withOpacity(0.14), borderRadius: BorderRadius.circular(15)),
          child: Icon(_vi(label), color: color, size: 26)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 0.8)),
          Text(_vd(label), style: TextStyle(color: c.sub, fontSize: 11)),
        ])),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text("$score", style: TextStyle(color: color, fontSize: 30, fontWeight: FontWeight.w900)),
          Text("/ 100", style: TextStyle(color: c.sub, fontSize: 10)),
        ]),
      ]),
      const SizedBox(height: 14),
      ClipRRect(borderRadius: BorderRadius.circular(6),
        child: LinearProgressIndicator(
          value: score / 100, minHeight: 7,
          backgroundColor: c.border,
          valueColor: AlwaysStoppedAnimation<Color>(color))),
      const SizedBox(height: 12),
      Row(children: [
        _chip("Risk Score", "$score%", color),
        const SizedBox(width: 8),
        _chip("Confidence", "$conf%", c.accent),
      ]),
    ]),
  );

  Widget _chip(String label, String value, Color color) => Expanded(child: Container(
    padding: const EdgeInsets.symmetric(vertical: 8),
    decoration: BoxDecoration(
      color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(12),
      border: Border.all(color: color.withOpacity(0.2))),
    child: Column(children: [
      Text(value, style: TextStyle(color: color, fontSize: 15, fontWeight: FontWeight.w800)),
      Text(label, style: TextStyle(color: c.sub, fontSize: 10)),
    ])));

  Widget _findingsCard(List<dynamic> findings, Color color) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(18),
      border: Border.all(color: c.border)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Icon(Icons.radar_rounded, size: 15, color: color),
        const SizedBox(width: 6),
        Text("Threat Indicators", style: TextStyle(color: c.text, fontSize: 13, fontWeight: FontWeight.w700)),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(8)),
          child: Text("${findings.length}", style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700))),
      ]),
      const SizedBox(height: 10),
      ...findings.map((f) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(padding: const EdgeInsets.only(top: 6),
            child: Container(width: 5, height: 5,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle))),
          const SizedBox(width: 9),
          Expanded(child: Text(f.toString(), style: TextStyle(color: c.sub, fontSize: 13))),
        ]))),
    ]));

  Widget _infoCards(Map<String, dynamic> r) {
    final items = [
      {"t": "What it is",    "v": r["what_it_is"]    ?? "", "i": Icons.info_rounded},
      {"t": "What happens",  "v": r["what_happens"]  ?? "", "i": Icons.play_arrow_rounded},
      {"t": "Why dangerous", "v": r["why_dangerous"] ?? "", "i": Icons.warning_rounded},
      {"t": "What to do",    "v": r["what_to_do"]    ?? "", "i": Icons.task_alt_rounded},
    ];
    return Column(children: items
      .where((item) => (item["v"] as String).isNotEmpty)
      .map((item) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(color: c.card, borderRadius: BorderRadius.circular(18),
            border: Border.all(color: c.border)),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(width: 32, height: 32,
              decoration: BoxDecoration(color: c.ag, borderRadius: BorderRadius.circular(10)),
              child: Icon(item["i"] as IconData, size: 16, color: c.accent)),
            const SizedBox(width: 11),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(item["t"] as String, style: TextStyle(color: c.text, fontSize: 13, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text(item["v"] as String, style: TextStyle(color: c.sub, fontSize: 13, height: 1.5)),
            ])),
          ]),
        ))).toList());
  }
}