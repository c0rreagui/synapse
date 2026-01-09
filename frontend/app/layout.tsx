import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Synapse | Automação de Conteúdo",
  description: "Plataforma de orquestração e distribuição de mídia automatizada",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
          rel="stylesheet"
        />
      </head>
      {/* 
        Updates:
        1. bg-[#02040a]: Matches the 'deep space' background of page.tsx
        2. text-slate-300: Standard text color for the app
        3. suppressHydrationWarning: Fixes the 'data-jetski-tab-id' mismatch error from extensions
      */}
      <body
        className="font-display bg-[#050507] text-slate-300 overflow-hidden antialiased selection:bg-primary/30 selection:text-white"
        suppressHydrationWarning={true}
      >
        {children}
      </body>
    </html>
  );
}
