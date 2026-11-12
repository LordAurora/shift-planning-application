import type { Metadata } from 'next';
import ErrorScreen from './components/ErrorScreen';

export const metadata: Metadata = { title: 'Page not found · ShiftMaster AI' };

export default function NotFound() {
  return (
    <ErrorScreen
      code="404"
      title="This shift doesn’t exist"
      message="The page you’re looking for has moved, been removed, or never made it onto the schedule. Check the address or head back to familiar ground."
      actions={[
        { label: 'Go to dashboard', href: '/dashboard', primary: true },
        { label: 'Back to home', href: '/landing' },
      ]}
    />
  );
}
