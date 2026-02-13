'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // Coisas importantes para estabilidade vs UX
        staleTime: 1000 * 60, // 1 minuto de cache (dados não mudam tão rápido)
        refetchOnWindowFocus: false, // Evita refetch agressivo
        retry: 1, // Tenta apenas 1 vez em caso de falha
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
