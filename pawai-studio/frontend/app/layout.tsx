import type { Metadata } from "next";
import { Inter, Fira_Code, Noto_Sans_TC } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
});

const notoSansTC = Noto_Sans_TC({
  variable: "--font-noto-sans-tc",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "PawAI Studio",
  description: "Embodied AI 機器狗控制中樞",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hant" className="dark">
      <body
        className={`${inter.variable} ${firaCode.variable} ${notoSansTC.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
