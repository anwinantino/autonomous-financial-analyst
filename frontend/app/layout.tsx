import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Autonomous Financial Analyst | ML + AI Price Forecasting",
  description:
    "Predict stock and crypto trends with Prophet ML, then validate against live news using Gemini AI. Educational tool only — not financial advice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col antialiased">{children}</body>
    </html>
  );
}
