'use client';

/**
 * Component to load polyfills before the main application
 * This ensures compatibility features are available when needed
 */

import { useEffect, type ReactNode } from 'react';

// Import polyfills to ensure they're loaded
import '../polyfills';

export function PolyfillsProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    // Verify that polyfills are loaded
    if (typeof Promise !== 'undefined' && !Promise.withResolvers) {
      console.error('Promise.withResolvers polyfill failed to load');
    }
  }, []);

  return <>{children}</>;
}
