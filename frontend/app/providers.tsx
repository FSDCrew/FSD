'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PropsWithChildren, useState } from 'react';

export default function Providers({ children }: PropsWithChildren) {
    // One client per browser session
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 5 * 60 * 1000,   // 5 min fresh
                        gcTime: 30 * 60 * 1000,     // garbage collect after 30 min
                        refetchOnWindowFocus: false,
                        retry: 2,
                    },
                    mutations: {
                        retry: 0,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
}
