import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

interface QueryProviderProps {
  children: React.ReactNode;
}

const createClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
        staleTime: 60_000,
      },
      mutations: {
        retry: 0,
      },
    },
  });

const QueryProvider: React.FC<QueryProviderProps> = ({ children }) => {
  const [client] = React.useState(createClient);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
};

export default QueryProvider;
