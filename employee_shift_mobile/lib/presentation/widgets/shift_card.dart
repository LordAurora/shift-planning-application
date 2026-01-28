import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../data/models/shift_model.dart';
import 'package:intl/intl.dart';

/// Vardiya kartı widget'ı
class ShiftCard extends StatelessWidget {
  final Shift shift;
  final VoidCallback? onTap;
  final bool showDate;
  final bool isCompact;

  const ShiftCard({
    super.key,
    required this.shift,
    this.onTap,
    this.showDate = true,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(
        horizontal: 16,
        vertical: isCompact ? 4 : 8,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(isCompact ? 12 : 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _buildStatusIndicator(),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (showDate)
                          Text(
                            _formatDate(shift.startTime),
                            style: TextStyle(
                              fontSize: isCompact ? 12 : 13,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        Text(
                          shift.departmentName ?? 'Departman',
                          style: TextStyle(
                            fontSize: isCompact ? 15 : 16,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _buildStatusChip(),
                ],
              ),
              if (!isCompact) ...[
                const SizedBox(height: 12),
                const Divider(height: 1),
                const SizedBox(height: 12),
              ],
              if (isCompact)
                const SizedBox(height: 8),
              Row(
                children: [
                  _buildTimeInfo(
                    icon: Icons.play_arrow_rounded,
                    label: 'Başlangıç',
                    time: shift.startTime,
                  ),
                  const SizedBox(width: 24),
                  _buildTimeInfo(
                    icon: Icons.stop_rounded,
                    label: 'Bitiş',
                    time: shift.endTime,
                  ),
                  const Spacer(),
                  _buildDuration(),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusIndicator() {
    return Container(
      width: 4,
      height: 40,
      decoration: BoxDecoration(
        color: _getStatusColor(),
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }

  Widget _buildStatusChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: _getStatusColor().withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        shift.status.displayName,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: _getStatusColor(),
        ),
      ),
    );
  }

  Widget _buildTimeInfo({
    required IconData icon,
    required String label,
    required DateTime time,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: AppColors.textSecondary,
        ),
        const SizedBox(width: 4),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isCompact)
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textLight,
                ),
              ),
            Text(
              DateFormat('HH:mm').format(time),
              style: TextStyle(
                fontSize: isCompact ? 13 : 14,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDuration() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.schedule,
            size: 14,
            color: AppColors.textSecondary,
          ),
          const SizedBox(width: 4),
          Text(
            shift.formattedDuration,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor() {
    switch (shift.status) {
      case ShiftStatus.scheduled:
        return AppColors.shiftScheduled;
      case ShiftStatus.completed:
        return AppColors.shiftCompleted;
      case ShiftStatus.cancelled:
        return AppColors.shiftCancelled;
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final tomorrow = today.add(const Duration(days: 1));
    final dateOnly = DateTime(date.year, date.month, date.day);

    if (dateOnly == today) {
      return 'Bugün';
    } else if (dateOnly == tomorrow) {
      return 'Yarın';
    } else {
      return DateFormat('d MMMM EEEE', 'tr_TR').format(date);
    }
  }
}
