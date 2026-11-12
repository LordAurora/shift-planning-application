import type { Metadata } from 'next';
import ErrorScreen from '../components/ErrorScreen';

export const metadata: Metadata = { title: 'Access denied · ShiftMaster AI' };

export default function Forbidden() {
  return (
    <ErrorScreen
      code="403"
      title="You don’t have access to this page"
      message="This area is limited to administrators or managers in your workspace. If you think you should have access, ask your administrator to update your role."
      actions={[
        { label: 'Go to dashboard', href: '/dashboard', primary: true },
        { label: 'Sign in with another account', href: '/login' },
      ]}
    />
  );
}
