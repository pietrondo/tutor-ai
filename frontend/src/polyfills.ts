/**
 * Polyfills for modern JavaScript features
 * This file ensures compatibility across different browser environments
 */

// Promise.withResolvers polyfill (ES2023 feature)
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/withResolvers
if (!Promise.withResolvers) {
  Promise.withResolvers = function <T>() {
    let resolve: (value: T | PromiseLike<T>) => void;
    let reject: (reason?: any) => void;
    const promise = new Promise<T>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve: resolve!, reject: reject! };
  };
}

// Export to ensure TypeScript recognizes the polyfill
export {};