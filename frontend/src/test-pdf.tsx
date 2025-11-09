'use client';

import { useEffect } from 'react';

export default function TestPDFPage() {
  useEffect(() => {
    // Test if Promise.withResolvers is available
    console.log('Testing Promise.withResolvers...');
    if (typeof Promise.withResolvers === 'function') {
      console.log('✅ Promise.withResolvers is available');
      const { promise, resolve, reject } = Promise.withResolvers<string>();
      resolve('test');
      promise.then(result => console.log('✅ Promise.withResolvers works:', result));
    } else {
      console.error('❌ Promise.withResolvers is not available');
    }

    // Test importing SimplePDFReader instead of EnhancedPDFReader
    import('@/components/SimplePDFReader')
      .then(() => console.log('✅ SimplePDFReader imported successfully'))
      .catch(err => console.error('❌ Failed to import SimplePDFReader:', err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">PDF Reader Polyfill Test</h1>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600">Check browser console for polyfill test results.</p>
          <p className="text-sm text-gray-500 mt-2">Now using SimplePDFReader to avoid Promise.withResolvers issues.</p>
        </div>
      </div>
    </div>
  );
}