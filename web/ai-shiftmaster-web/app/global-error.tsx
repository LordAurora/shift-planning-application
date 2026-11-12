'use client';

import ErrorScreen from './components/ErrorScreen';

/** Replaces the root layout when the layout itself fails, so it renders its own <html>. */
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>
        <ErrorScreen
          code="500"
          title="ShiftMaster AI is temporarily unavailable"
          message="The application failed to load. Please try again in a moment."
          detail={error.digest ? `Reference: ${error.digest}` : undefined}
          actions={[{ label: 'Reload', onClick: reset, primary: true }]}
        />
      </body>
    </html>
  );
}
