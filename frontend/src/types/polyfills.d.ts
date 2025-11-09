/**
 * Type definitions for Promise.withResolvers polyfill
 * Ensures TypeScript recognizes the extended Promise interface
 */

interface PromiseWithResolvers<T> {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: any) => void;
}

interface PromiseConstructor {
  withResolvers<T = void>(): PromiseWithResolvers<T>;
}

declare global {
  interface PromiseConstructor {
    withResolvers<T = void>(): PromiseWithResolvers<T>;
  }
}

export {};