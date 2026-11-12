'use client';

import { useEffect } from 'react';
import ErrorScreen from './components/ErrorScreen';

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <ErrorScreen
      code="500"
      title="Something went wrong"
      message="An unexpected error interrupted this page. Your data is safe. Try again, and if the problem keeps happening, contact your administrator."
      detail={error.digest ? `Reference: ${error.digest}` : undefined}
      actions={[
        { label: 'Try again', onClick: reset, primary: true },
        { label: 'Go to dashboard', href: '/dashboard' },
      ]}
    />
  );
}
