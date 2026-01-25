'use client';

import DashboardLayout from '../components/DashboardLayout';

export default function SecurityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
