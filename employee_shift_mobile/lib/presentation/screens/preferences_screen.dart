import 'package:flutter/material.dart';

class PreferencesScreen extends StatefulWidget {
  const PreferencesScreen({super.key});

  @override
  State<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends State<PreferencesScreen> {
  // Haftalık izin günü
  String _selectedOffDay = 'saturday';
  
  // Çalışma modeli
  String _workModel = 'hybrid';
  
  // Ofis ve uzaktan çalışma günleri
  int _officeDays = 3;
  int _remoteDays = 2;
  
  // Tercih edilen vardiya
  String _preferredShift = 'morning';
  
  // Ek notlar
  final TextEditingController _notesController = TextEditingController();
  
  // Özel izin günleri
  List<String> _blockedDays = [];
  
  bool _isLoading = false;

  final List<Map<String, String>> _weekDays = [
    {'key': 'monday', 'label': 'Pazartesi'},
    {'key': 'tuesday', 'label': 'Salı'},
    {'key': 'wednesday', 'label': 'Çarşamba'},
    {'key': 'thursday', 'label': 'Perşembe'},
    {'key': 'friday', 'label': 'Cuma'},
    {'key': 'saturday', 'label': 'Cumartesi'},
    {'key': 'sunday', 'label': 'Pazar'},
  ];

  final List<Map<String, dynamic>> _shiftTypes = [
    {'key': 'morning', 'label': 'Sabah Vardiyası', 'time': '06:00 - 14:00', 'icon': Icons.wb_sunny},
    {'key': 'day', 'label': 'Gündüz Vardiyası', 'time': '09:00 - 17:00', 'icon': Icons.light_mode},
    {'key': 'afternoon', 'label': 'Akşam Vardiyası', 'time': '14:00 - 22:00', 'icon': Icons.wb_twilight},
    {'key': 'night', 'label': 'Gece Vardiyası', 'time': '22:00 - 06:00', 'icon': Icons.nightlight},
    {'key': 'flexible', 'label': 'Esnek', 'time': 'Herhangi bir saat', 'icon': Icons.schedule},
  ];

  final List<Map<String, dynamic>> _workModels = [
    {'key': 'office', 'label': 'Tam Zamanlı Ofis', 'icon': Icons.business, 'description': 'Her gün ofisten çalışma'},
    {'key': 'remote', 'label': 'Tam Zamanlı Uzaktan', 'icon': Icons.home, 'description': 'Her gün evden çalışma'},
    {'key': 'hybrid', 'label': 'Hibrit', 'icon': Icons.compare_arrows, 'description': 'Hem ofis hem uzaktan'},
  ];

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  void _savePreferences() async {
    setState(() {
      _isLoading = true;
    });

    // Simüle edilmiş API çağrısı
    await Future.delayed(const Duration(seconds: 2));

    final preferences = {
      'weeklyOffDay': _selectedOffDay,
      'workModel': _workModel,
      'officeDays': _officeDays,
      'remoteDays': _remoteDays,
      'preferredShift': _preferredShift,
      'blockedDays': _blockedDays,
      'notes': _notesController.text,
    };

    debugPrint('Tercihler kaydedildi: $preferences');

    setState(() {
      _isLoading = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tercihleriniz başarıyla kaydedildi!'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text('Çalışma Tercihlerim'),
        backgroundColor: const Color(0xFF1E3A5F),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Tercihleriniz Hakkında'),
                  content: const Text(
                    'Burada belirlediğiniz tercihler, AI vardiya optimizasyonunda dikkate alınır. '
                    'Yöneticiniz bu tercihleri görebilir ve vardiya planlamasında kullanabilir.\n\n'
                    'Not: Tercihler kesin garanti değildir, iş yoğunluğuna göre değişiklik olabilir.',
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Anladım'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info Banner
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1E3A5F), Color(0xFF2E5077)],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.psychology,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'AI Destekli Planlama',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Tercihleriniz AI vardiya optimizasyonunda kullanılır',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),

            // Haftalık İzin Günü
            _buildSectionCard(
              title: 'Haftalık İzin Günü',
              icon: Icons.event_available,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Hangi gün haftalık izninizi tercih edersiniz?',
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _weekDays.map((day) {
                      final isSelected = _selectedOffDay == day['key'];
                      return ChoiceChip(
                        label: Text(day['label']!),
                        selected: isSelected,
                        selectedColor: const Color(0xFF1E3A5F),
                        labelStyle: TextStyle(
                          color: isSelected ? Colors.white : Colors.black87,
                        ),
                        onSelected: (selected) {
                          if (selected) {
                            setState(() {
                              _selectedOffDay = day['key']!;
                            });
                          }
                        },
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Çalışma Modeli
            _buildSectionCard(
              title: 'Çalışma Modeli',
              icon: Icons.work_outline,
              child: Column(
                children: _workModels.map((model) {
                  final isSelected = _workModel == model['key'];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: InkWell(
                      onTap: () {
                        setState(() {
                          _workModel = model['key'];
                          if (model['key'] == 'office') {
                            _officeDays = 5;
                            _remoteDays = 0;
                          } else if (model['key'] == 'remote') {
                            _officeDays = 0;
                            _remoteDays = 5;
                          } else {
                            _officeDays = 3;
                            _remoteDays = 2;
                          }
                        });
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isSelected ? const Color(0xFF1E3A5F).withOpacity(0.1) : Colors.grey[50],
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: isSelected ? const Color(0xFF1E3A5F) : Colors.grey[300]!,
                            width: isSelected ? 2 : 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              model['icon'],
                              color: isSelected ? const Color(0xFF1E3A5F) : Colors.grey,
                              size: 28,
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    model['label'],
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: isSelected ? const Color(0xFF1E3A5F) : Colors.black87,
                                    ),
                                  ),
                                  Text(
                                    model['description'],
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            if (isSelected)
                              const Icon(
                                Icons.check_circle,
                                color: Color(0xFF1E3A5F),
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),

            // Hibrit Çalışma Detayları
            if (_workModel == 'hybrid') ...[
              const SizedBox(height: 16),
              _buildSectionCard(
                title: 'Hibrit Çalışma Detayları',
                icon: Icons.tune,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Haftalık çalışma dağılımınızı belirleyin',
                      style: TextStyle(color: Colors.grey, fontSize: 13),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF1E3A5F).withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Column(
                                  children: [
                                    const Icon(Icons.business, color: Color(0xFF1E3A5F)),
                                    const SizedBox(height: 8),
                                    const Text('Ofis Günü', style: TextStyle(fontSize: 12)),
                                    const SizedBox(height: 8),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        IconButton(
                                          icon: const Icon(Icons.remove_circle_outline),
                                          onPressed: _officeDays > 0
                                              ? () {
                                                  setState(() {
                                                    _officeDays--;
                                                    _remoteDays++;
                                                  });
                                                }
                                              : null,
                                        ),
                                        Text(
                                          '$_officeDays',
                                          style: const TextStyle(
                                            fontSize: 24,
                                            fontWeight: FontWeight.bold,
                                            color: Color(0xFF1E3A5F),
                                          ),
                                        ),
                                        IconButton(
                                          icon: const Icon(Icons.add_circle_outline),
                                          onPressed: _officeDays < 5
                                              ? () {
                                                  setState(() {
                                                    _officeDays++;
                                                    _remoteDays--;
                                                  });
                                                }
                                              : null,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.green.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Column(
                                  children: [
                                    const Icon(Icons.home, color: Colors.green),
                                    const SizedBox(height: 8),
                                    const Text('Uzaktan Gün', style: TextStyle(fontSize: 12)),
                                    const SizedBox(height: 8),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        IconButton(
                                          icon: const Icon(Icons.remove_circle_outline),
                                          onPressed: _remoteDays > 0
                                              ? () {
                                                  setState(() {
                                                    _remoteDays--;
                                                    _officeDays++;
                                                  });
                                                }
                                              : null,
                                        ),
                                        Text(
                                          '$_remoteDays',
                                          style: const TextStyle(
                                            fontSize: 24,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.green,
                                          ),
                                        ),
                                        IconButton(
                                          icon: const Icon(Icons.add_circle_outline),
                                          onPressed: _remoteDays < 5
                                              ? () {
                                                  setState(() {
                                                    _remoteDays++;
                                                    _officeDays--;
                                                  });
                                                }
                                              : null,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Tercih Edilen Vardiya
            _buildSectionCard(
              title: 'Tercih Edilen Vardiya',
              icon: Icons.access_time,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Hangi vardiya saatlerini tercih edersiniz?',
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  ..._shiftTypes.map((shift) {
                    final isSelected = _preferredShift == shift['key'];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: InkWell(
                        onTap: () {
                          setState(() {
                            _preferredShift = shift['key'];
                          });
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(
                            color: isSelected ? const Color(0xFF1E3A5F).withOpacity(0.1) : Colors.transparent,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: isSelected ? const Color(0xFF1E3A5F) : Colors.grey[300]!,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                shift['icon'],
                                color: isSelected ? const Color(0xFF1E3A5F) : Colors.grey,
                                size: 20,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      shift['label'],
                                      style: TextStyle(
                                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                        color: isSelected ? const Color(0xFF1E3A5F) : Colors.black87,
                                      ),
                                    ),
                                    Text(
                                      shift['time'],
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: Colors.grey[600],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              if (isSelected)
                                const Icon(Icons.check, color: Color(0xFF1E3A5F), size: 20),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Ek Notlar
            _buildSectionCard(
              title: 'Ek Notlar',
              icon: Icons.note_alt_outlined,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Yöneticinize iletmek istediğiniz ek notlar',
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _notesController,
                    maxLines: 3,
                    decoration: InputDecoration(
                      hintText: 'Örn: Cuma günleri erken çıkmak istiyorum, çocuğumu okuldan almam gerekiyor...',
                      hintStyle: TextStyle(color: Colors.grey[400], fontSize: 13),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.grey[300]!),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: Color(0xFF1E3A5F), width: 2),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 32),

            // Kaydet Butonu
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _savePreferences,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1E3A5F),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 2,
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.save, color: Colors.white),
                          SizedBox(width: 8),
                          Text(
                            'Tercihlerimi Kaydet',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
              ),
            ),

            const SizedBox(height: 16),

            // Bilgi Notu
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.amber.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber.withOpacity(0.3)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline, color: Colors.amber, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Tercihleriniz AI tarafından değerlendirilir ancak iş gereksinimleri nedeniyle her zaman tam olarak karşılanamayabilir.',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[700],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: const Color(0xFF1E3A5F), size: 20),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3A5F),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}
