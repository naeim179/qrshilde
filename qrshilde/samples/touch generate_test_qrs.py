import qrcode
import os

# 1. QR نظيف (Clean)
img1 = qrcode.make("https://google.com")
img1.save("test_clean.png")

# 2. QR خبيث (SQL Injection) - عشان نفحص Pattern Detector
# هذا الكود يحاول يسرق قاعدة البيانات
img2 = qrcode.make("http://example.com/login?user=' OR 1=1; DROP TABLE users; --")
img2.save("test_sqli.png")

# 3. QR واي فاي خطير (No Password) - عشان نفحص Wifi Detector
img3 = qrcode.make("WIFI:S:Free_Internet;T:nopass;;")
img3.save("test_wifi.png")

print("✅ تم إنشاء 3 صور QR للاختبار: test_clean.png, test_sqli.png, test_wifi.png")