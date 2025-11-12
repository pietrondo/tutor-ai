/**
 * Development Performance Optimizations
 *
 * These utilities help improve INP (Interaction to Next Paint) in development mode
 */

import React, { useEffect, useRef } from 'react';

// Debounce hook for expensive operations
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const debouncedCallback = ((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => callback(...args), delay);
  }) as T;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}

// Throttle hook for high-frequency events
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now());

  const throttledCallback = ((...args: Parameters<T>) => {
    if (Date.now() - lastRun.current >= delay) {
      callback(...args);
      lastRun.current = Date.now();
    }
  }) as T;

  return throttledCallback;
}

// Optimized scroll handler
export function useOptimizedScroll(
  callback: () => void,
  delay: number = 16 // ~60fps
) {
  const throttledCallback = useThrottle(callback, delay);

  useEffect(() => {
    window.addEventListener('scroll', throttledCallback, { passive: true });
    return () => window.removeEventListener('scroll', throttledCallback);
  }, [throttledCallback]);
}

// Intersection Observer for lazy loading
export function useIntersectionObserver(
  ref: React.RefObject<Element>,
  callback: IntersectionObserverCallback,
  options?: IntersectionObserverInit
) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(callback, {
      threshold: 0.1,
      rootMargin: '50px',
      ...options,
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, [ref, callback, options]);
}

// Development-only performance monitoring
export function useDevPerformanceMonitor(componentName: string) {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      console.log(`[Performance] ${componentName} render time: ${endTime - startTime}ms`);
    };
  });
}

// Memoized component wrapper for development
export function withDevOptimization<P extends object>(
  Component: React.ComponentType<P>,
  componentName: string
) {
  const OptimizedComponent = (props: P) => {
    useDevPerformanceMonitor(componentName);
    return React.createElement(Component, { ...props });
  };

  OptimizedComponent.displayName = `withDevOptimization(${componentName})`;
  return OptimizedComponent;
}
