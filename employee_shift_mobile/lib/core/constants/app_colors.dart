import 'package:flutter/material.dart';

/// Kurumsal renk paleti - Sade ve profesyonel
class AppColors {
  // Ana Renkler
  static const Color primary = Color(0xFF1E3A5F);      // Koyu mavi - kurumsal
  static const Color primaryLight = Color(0xFF2E5077); // Açık koyu mavi
  static const Color primaryDark = Color(0xFF0D1F33);  // Çok koyu mavi
  
  // İkincil Renkler
  static const Color secondary = Color(0xFF3D7EA6);    // Orta mavi
  static const Color secondaryLight = Color(0xFF5A9BC2);
  
  // Arka Plan Renkleri
  static const Color background = Color(0xFFF5F7FA);   // Açık gri
  static const Color surface = Color(0xFFFFFFFF);      // Beyaz
  static const Color surfaceLight = Color(0xFFFAFBFC);
  
  // Metin Renkleri
  static const Color textPrimary = Color(0xFF1A1A2E);   // Koyu lacivert
  static const Color textSecondary = Color(0xFF6B7280); // Gri
  static const Color textLight = Color(0xFF9CA3AF);     // Açık gri
  static const Color textOnPrimary = Color(0xFFFFFFFF); // Beyaz
  
  // Durum Renkleri
  static const Color success = Color(0xFF059669);       // Yeşil
  static const Color successLight = Color(0xFFD1FAE5);
  static const Color warning = Color(0xFFD97706);       // Turuncu
  static const Color warningLight = Color(0xFFFEF3C7);
  static const Color error = Color(0xFFDC2626);         // Kırmızı
  static const Color errorLight = Color(0xFFFEE2E2);
  static const Color info = Color(0xFF0284C7);          // Mavi
  static const Color infoLight = Color(0xFFE0F2FE);
  
  // Kenarlık ve Ayırıcı
  static const Color border = Color(0xFFE5E7EB);
  static const Color divider = Color(0xFFF3F4F6);
  
  // Vardiya Durumları
  static const Color shiftScheduled = Color(0xFF3D7EA6);
  static const Color shiftCompleted = Color(0xFF059669);
  static const Color shiftCancelled = Color(0xFFDC2626);
  
  // İzin Durumları
  static const Color leavePending = Color(0xFFD97706);
  static const Color leaveApproved = Color(0xFF059669);
  static const Color leaveRejected = Color(0xFFDC2626);
  
  // Devre Dışı
  static const Color disabled = Color(0xFFD1D5DB);
  
  // Gölgeler
  static const Color shadow = Color(0x1A000000);
}
