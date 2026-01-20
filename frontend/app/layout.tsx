import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from "./components/ClientLayout";

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
      <body
        className="font-display bg-[#050507] text-slate-300 overflow-hidden antialiased selection:bg-primary/30 selection:text-white"
        suppressHydrationWarning={true}
      >
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}

