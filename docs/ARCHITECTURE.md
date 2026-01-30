# Shift Planning Application — Detaylı Genel Bakış

Bu doküman, monorepo içindeki tüm bileşenleri (backend, Security AI modülü, mobil uygulama, web arayüzü ve MindSpore göç planı) kapsamlı biçimde özetler.

---

## 1) Genel Mimari

- **Monorepo yapısı**: Backend (FastAPI tabanlı), Security AI modülü, Flutter mobil uygulaması, Next.js web arayüzü.
- **Veri akışı (yüksek seviye)**: Mobil/Web istemciler ⇄ REST API ⇄ Veritabanı + önbellek. Security AI, kod güvenliği / kural + ML tespiti için ayrı alt modül olarak tasarlandı.
- **Offline-first**: Flutter uygulaması lokal veritabanı + senkronizasyon servisi ile çevrimdışı çalışabiliyor.

---

## 2) Backend (FastAPI) 

- Giriş noktası: [backend/app/main.py](../backend/app/main.py)
- Konfigürasyon & DB: [backend/app/config.py](../backend/app/config.py), [backend/app/database.py](../backend/app/database.py)
- Modeller: [backend/app/models/](../backend/app/models) (department, employee, shift, notification, user, shift_rule, audit_log)
- Şemalar: [backend/app/schemas/](../backend/app/schemas)
- Routerlar: [backend/app/routers/](../backend/app/routers) (auth, employees, departments, shifts, rules, notifications, ai)
- Güvenlik yardımcıları: [backend/app/utils/security.py](../backend/app/utils/security.py)
- Alembic migrasyonları: [backend/alembic/](../backend/alembic)

### Öne çıkanlar
- JWT tabanlı kimlik doğrulama (auth router).
- Shift / departman / çalışan CRUD uçları.
- Bildirimler ve kural yönetimi uçları.

---

## 3) Security AI Modülü

Konum: [backend/app/security_ai/](../backend/app/security_ai)

### 3.1 Hybrid Engine (Kural + ML)
- **Kural motoru**: [hybrid_engine/rule_engine.py](../backend/app/security_ai/hybrid_engine/rule_engine.py) — SQL/command injection, path traversal, hardcoded credential vb. kritik kurallar.
- **ML adapter**: [hybrid_engine/ml_adapter.py](../backend/app/security_ai/hybrid_engine/ml_adapter.py) — tahmin ve güven skoru kalibrasyonu.
- **Füzyon**: [hybrid_engine/fusion_engine.py](../backend/app/security_ai/hybrid_engine/fusion_engine.py) — kural/ML sonuçlarını stratejiye göre birleştirir (Conservative/Balanced/Aggressive).
- **Giriş noktası**: [hybrid_engine/hybrid_detector.py](../backend/app/security_ai/hybrid_engine/hybrid_detector.py) — FULL, RULES_ONLY, ML_ONLY, CRITICAL_ONLY modları.
- **Tasarım dokümanı**: [hybrid_engine/HYBRID_ENGINE.md](../backend/app/security_ai/hybrid_engine/HYBRID_ENGINE.md)

### 3.2 Eğitim, Değerlendirme, Süreklilik (Module 4)
- **Metrikler**: [training/metrics.py](../backend/app/security_ai/training/metrics.py) — `SecurityMetrics`, sınıf bazlı metrikler, FPR/FNR, MCC.
- **Veri bölme**: [training/data_splitting.py](../backend/app/security_ai/training/data_splitting.py) — Random, Stratified, Temporal, CrossValidator.
- **Dengeleme**: [training/class_balancer.py](../backend/app/security_ai/training/class_balancer.py) — SMOTE, Focal Loss, sınıf ağırlıkları, eşik optimizasyonu.
- **Eğitim döngüsü**: [training/training_loop.py](../backend/app/security_ai/training/training_loop.py) — `TrainingConfig`, erken durdurma, LR scheduler, checkpoint.
- **Değerlendirme**: [training/evaluation.py](../backend/app/security_ai/training/evaluation.py) — `ModelEvaluator`, `SecurityBenchmark`, `RegressionTester`.
- **Sürekli öğrenme**: [training/continuous_learning.py](../backend/app/security_ai/training/continuous_learning.py) — yanlış sınıflandırma kaydı, feedback, retraining tetikleyici.
- **Strateji dokümanı**: [training/TRAINING_STRATEGY.md](../backend/app/security_ai/training/TRAINING_STRATEGY.md)

### 3.3 MindSpore / Huawei Göç Planı (Module 5)
- **Plan**: [migration/MIGRATION_PLAN.md](../backend/app/security_ai/migration/MIGRATION_PLAN.md) — TensorFlow → MindSpore + ModelArts yol haritası.
- **Şablonlar**: [migration/mindspore_templates.py](../backend/app/security_ai/migration/mindspore_templates.py) — model/loss/pipeline referans kodları (tasarım amaçlı).
- **Ascend optimizasyonu**: [migration/ascend_optimization.py](../backend/app/security_ai/migration/ascend_optimization.py) — NPU ayarları, mixed precision, data sink.

---

## 4) Mobil Uygulama (Flutter)

Konum: [employee_shift_mobile/](../employee_shift_mobile)

- Giriş: [lib/main.dart](../employee_shift_mobile/lib/main.dart)
- Çevrimdışı-first senkronizasyon: [lib/services/sync_service.dart](../employee_shift_mobile/lib/services/sync_service.dart)
- Paketler: `connectivity_plus`, yerel DB servisi, API istemcisi.
- Android/iOS/web/desktop platform klasörleri mevcut.

### 4.1 SyncService Özeti
- **Aralık & tekrar**: `_syncInterval = 5 dak` ve `_maxRetries = 5` deneme sınırı.
- **Durum yayını**: `Stream<SyncStatus>` ile UI bilgilendirme.
- **Akış**:
  1) Bağlantı kontrolü (`Connectivity`).
  2) Kuyruğa alınan işlemler: create/update (örn. izin talebi, shift, bildirim) sunucuya push.
  3) Sunucudan taze veri çekme ve yerelde önbellekleme (shift, leave request, notification).
  4) Çakışma çözümü: varsayılan server-wins (last-write-wins öncelikli).
- **Çevrimdışı davranış**: Bağlantı yoksa `SyncState.offline` ile bilgi verip işlemleri kuyruğa eklemeye devam eder.

### 4.2 Veri Yapıları
- `SyncStatus`: durum, mesaj, son senkron zamanı, bekleyen/başarısız sayıları.
- `SyncResult`: başarı durumu, mesaj, senkronize/başarısız adet, hata listesi.
- `SyncState`: `synced | syncing | offline | error | pending`.

---

## 5) Web Uygulama (Next.js)

Konum: [web/ai-shiftmaster-web/](../web/ai-shiftmaster-web)

- Next.js 13+ app directory yapısı.
- Yapılandırmalar: [package.json](../web/ai-shiftmaster-web/package.json), [tsconfig.json](../web/ai-shiftmaster-web/tsconfig.json), [next.config.ts](../web/ai-shiftmaster-web/next.config.ts), [eslint.config.mjs](../web/ai-shiftmaster-web/eslint.config.mjs).
- UI bileşenleri ve sayfalar: [app/](../web/ai-shiftmaster-web/app)
- Statik varlıklar: [public/](../web/ai-shiftmaster-web/public)

---

## 6) Veritabanı ve Göçler

- Alembic yapılandırması: [backend/alembic.ini](../backend/alembic.ini)
- Migrasyon scriptleri: [backend/alembic/versions/](../backend/alembic/versions)
- Şema yönetimi: Modeller [backend/app/models/](../backend/app/models) + şemalar [backend/app/schemas/](../backend/app/schemas)

---

## 7) Güvenlik Notları

- JWT ile auth; `security.py` içinde parola hash & token yardımcıları.
- Security AI kural motoru kritik güvenlik açıklarını (SQLi, command injection, path traversal vb.) yakalamak için regex/AST tabanlı kurallar içerir.
- Hybrid füzyon ile kural + ML sonuçlarının False Positive kontrolü yapılır.

---

## 8) Sürekli Öğrenme ve İzleme

- Yanlış sınıflandırma kaydı ve geri bildirim toplama: [training/continuous_learning.py](../backend/app/security_ai/training/continuous_learning.py)
- Performans eşik hedefleri: Recall ≥ %95, kritik sınıflarda ≥ %99; FPR ≤ %10 (bkz. [TRAINING_STRATEGY.md](../backend/app/security_ai/training/TRAINING_STRATEGY.md)).

---

## 9) MindSpore / ModelArts Göç Özeti

- Değişmeden kalanlar: Şema, etiketler, güvenlik kuralları, metrikler, sürekli öğrenme mantığı.
- Değişecekler: Model tanımı (`nn.Cell`), eğitim döngüsü (`Model.train`), veri hattı (MindData), loss/optimizer sözdizimi, checkpoint ve dağıtık eğitim ayarları.
- Ascend optimizasyonu: Graph mode, dataset sink, mixed precision (O2), operator fusion, gradient checkpointing.
- Güvenli inference API: TLS, API key, rate limiting, VPC izolasyonu (bkz. [MIGRATION_PLAN.md](../backend/app/security_ai/migration/MIGRATION_PLAN.md)).

---

## 10) Yapılacaklar / Öneriler

- SyncService için çakışma çözümünde (server/local wins) flag temizleme yöntemi eklenebilir.
- Continuous learning pipeline’da gerçek model entegrasyonu placeholder olarak işaretli; eğitim/evaluasyon kodları üretim ayarlarına bağlanmalı.
- Web arayüzünde güvenlik AI sonuçlarının görselleştirilmesi için API entegrasyonu doğrulanmalı.

---

Bu doküman, depo içeriğine hızlı hâkimiyet sağlamak için hazırlanmıştır. Daha derin teknik kararlar için ilgili modül dokümanlarına (HYBRID_ENGINE.md, TRAINING_STRATEGY.md, MIGRATION_PLAN.md) bakılabilir.
