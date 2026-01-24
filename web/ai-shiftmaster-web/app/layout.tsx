import type { Metadata } from "next";
import "./globals.css";
import ThemeProvider from "./theme/ThemeProvider";

export const metadata: Metadata = {
  title: "ShiftMaster AI - Shift Planning System",
  description: "AI-powered shift planning and optimization system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
