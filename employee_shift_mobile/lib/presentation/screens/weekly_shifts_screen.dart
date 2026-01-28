import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_strings.dart';
import '../../providers/auth_provider.dart';
import '../../providers/shift_provider.dart';
import '../../data/models/shift_model.dart';
import '../widgets/widgets.dart';

/// Haftalık Vardiya Ekranı
class WeeklyShiftsScreen extends StatefulWidget {
  const WeeklyShiftsScreen({super.key});

  @override
  State<WeeklyShiftsScreen> createState() => _WeeklyShiftsScreenState();
}

class _WeeklyShiftsScreenState extends State<WeeklyShiftsScreen> {
  @override
  void initState() {
    super.initState();
    _loadWeeklyShifts();
  }

  Future<void> _loadWeeklyShifts() async {
    final authProvider = context.read<AuthProvider>();
    final shiftProvider = context.read<ShiftProvider>();
    
    if (authProvider.user != null) {
      await shiftProvider.loadInitialData(employeeId: authProvider.user!.id);
    }
  }

  Future<void> _refresh() async {
    await context.read<ShiftProvider>().refreshAll();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.weeklySchedule),
        actions: [
          IconButton(
            onPressed: () {
              final shiftProvider = context.read<ShiftProvider>();
              shiftProvider.currentWeek();
            },
            icon: const Icon(Icons.today),
            tooltip: 'Bu Hafta',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        color: AppColors.primary,
        child: Consumer<ShiftProvider>(
          builder: (context, shiftProvider, _) {
            if (shiftProvider.isLoading) {
              return const LoadingWidget(message: 'Vardiyalar yükleniyor...');
            }

            return Column(
              children: [
                _buildWeekNavigator(shiftProvider),
                Expanded(
                  child: _buildWeekView(shiftProvider),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildWeekNavigator(ShiftProvider shiftProvider) {
    final weekStart = shiftProvider.selectedWeekStart;
    final weekEnd = weekStart.add(const Duration(days: 6));

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(
          bottom: BorderSide(color: AppColors.border),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            onPressed: () => shiftProvider.previousWeek(),
            icon: const Icon(Icons.chevron_left),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.surfaceLight,
            ),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  _formatWeekRange(weekStart, weekEnd),
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                if (_isCurrentWeek(weekStart))
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'Bu Hafta',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => shiftProvider.nextWeek(),
            icon: const Icon(Icons.chevron_right),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.surfaceLight,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeekView(ShiftProvider shiftProvider) {
    final weekStart = shiftProvider.selectedWeekStart;
    final days = List.generate(7, (index) => weekStart.add(Duration(days: index)));

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: 7,
      itemBuilder: (context, index) {
        final day = days[index];
        final shifts = shiftProvider.getShiftsForDay(day);
        final isToday = _isToday(day);

        return _buildDaySection(day, shifts, isToday);
      },
    );
  }

  Widget _buildDaySection(DateTime day, List<Shift> shifts, bool isToday) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isToday ? AppColors.primary : AppColors.border,
          width: isToday ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Gün başlığı
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isToday ? AppColors.primary.withOpacity(0.05) : null,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(11),
                topRight: Radius.circular(11),
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: isToday ? AppColors.primary : AppColors.surfaceLight,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        day.day.toString(),
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: isToday ? Colors.white : AppColors.textPrimary,
                        ),
                      ),
                      Text(
                        AppStrings.weekDaysShort[day.weekday - 1],
                        style: TextStyle(
                          fontSize: 10,
                          color: isToday ? Colors.white70 : AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        AppStrings.weekDays[day.weekday - 1],
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: isToday ? FontWeight.w600 : FontWeight.w500,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      Text(
                        DateFormat('d MMMM', 'tr_TR').format(day),
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                if (isToday)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'BUGÜN',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          // Vardiyalar
          if (shifts.isEmpty)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(
                    Icons.event_busy_outlined,
                    size: 18,
                    color: AppColors.textLight,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Vardiya yok',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.textLight,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            )
          else
            ...shifts.map((shift) => _buildShiftItem(shift)),
        ],
      ),
    );
  }

  Widget _buildShiftItem(Shift shift) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: AppColors.divider),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 4,
            height: 40,
            decoration: BoxDecoration(
              color: _getStatusColor(shift.status),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  shift.departmentName ?? 'Departman',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.schedule,
                      size: 14,
                      color: AppColors.textSecondary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${DateFormat('HH:mm').format(shift.startTime)} - ${DateFormat('HH:mm').format(shift.endTime)}',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceLight,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        shift.formattedDuration,
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: _getStatusColor(shift.status).withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              shift.status.displayName,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: _getStatusColor(shift.status),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(ShiftStatus status) {
    switch (status) {
      case ShiftStatus.scheduled:
        return AppColors.shiftScheduled;
      case ShiftStatus.completed:
        return AppColors.shiftCompleted;
      case ShiftStatus.cancelled:
        return AppColors.shiftCancelled;
    }
  }

  String _formatWeekRange(DateTime start, DateTime end) {
    if (start.month == end.month) {
      return '${start.day} - ${end.day} ${AppStrings.months[start.month - 1]}';
    }
    return '${start.day} ${AppStrings.months[start.month - 1]} - ${end.day} ${AppStrings.months[end.month - 1]}';
  }

  bool _isCurrentWeek(DateTime weekStart) {
    final now = DateTime.now();
    final currentWeekStart = now.subtract(Duration(days: now.weekday - 1));
    return weekStart.year == currentWeekStart.year &&
        weekStart.month == currentWeekStart.month &&
        weekStart.day == currentWeekStart.day;
  }

  bool _isToday(DateTime day) {
    final now = DateTime.now();
    return day.year == now.year && day.month == now.month && day.day == now.day;
  }
}
