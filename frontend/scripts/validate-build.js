#!/usr/bin/env node

/**
 * Build Validation Script
 * Validates that PDF.js worker is properly included in production builds
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Tutor-AI Production Build...\n');

// Check if we're in production mode
const isProduction = process.env.NODE_ENV === 'production';
if (!isProduction) {
  console.log('⚠️ Not running in production mode. Set NODE_ENV=production for production validation.');
}

// Paths to check for PDF worker
const workerPaths = [
  'public/pdf.worker.min.js',
  '.next/static/pdf.worker.min.js',
  '.next/static/chunks/pdf.worker.min.js',
  '.next/static/worker/pdf.worker.min.js',
  '.next/standalone/public/pdf.worker.min.js',
];

// Check Next.js build output
console.log('📦 Checking Next.js build output...');
const nextDir = '.next';
if (!fs.existsSync(nextDir)) {
  console.log('❌ Next.js build directory not found. Run `npm run build` first.');
  process.exit(1);
}

// Validate PDF worker file
console.log('\n🔧 Validating PDF.js worker...');
let workerFound = false;
let workerSize = 0;
const MIN_WORKER_SIZE = 1_000; // sanity check against empty/corrupt files
const MAX_WORKER_SIZE = 3_000_000; // warn if unexpectedly large but do not fail

for (const workerPath of workerPaths) {
  if (fs.existsSync(workerPath)) {
    const stats = fs.statSync(workerPath);
    workerSize = stats.size;
    workerFound = true;
    console.log(`✅ PDF worker found: ${workerPath} (${workerSize} bytes)`);
    break;
  }
}

if (!workerFound) {
  console.log('❌ PDF worker not found in any expected location:');
  workerPaths.forEach(path => console.log(`   - ${path}`));
  process.exit(1);
}

// Check for common issues
console.log('\n🚨 Checking for common issues...');

// Check worker file size (should be reasonable)
if (workerSize < MIN_WORKER_SIZE) {
  console.log('❌ PDF worker file seems too small, might be corrupted');
  workerFound = false; // force failure in summary
} else if (workerSize > MAX_WORKER_SIZE) {
  console.log(`⚠️ PDF worker file is larger than expected (${workerSize} bytes). Continuing, but verify if needed.`);
} else {
  console.log(`✅ PDF worker file size looks good (${workerSize} bytes)`);
}

// Check standalone build
console.log('\n🏗️ Checking standalone build...');
const standaloneDir = '.next/standalone';
if (fs.existsSync(standaloneDir)) {
  console.log('✅ Standalone build found');

  // Check standalone public directory
  const standalonePublic = path.join(standaloneDir, 'public');
  if (fs.existsSync(standalonePublic)) {
    console.log('✅ Standalone public directory found');

    const standaloneWorker = path.join(standalonePublic, 'pdf.worker.min.js');
    if (fs.existsSync(standaloneWorker)) {
      console.log('✅ PDF worker found in standalone build');
    } else {
      console.log('⚠️ PDF worker not found in standalone build');
    }
  } else {
    console.log('⚠️ Standalone public directory not found');
  }
} else {
  console.log('⚠️ Standalone build not found');
}

// Docker-specific checks
console.log('\n🐳 Docker-specific checks...');
const dockerfile = 'Dockerfile';
if (fs.existsSync(dockerfile)) {
  const dockerfileContent = fs.readFileSync(dockerfile, 'utf8');

  // Check for public directory volume mount in production
  if (dockerfileContent.includes('public') || dockerfileContent.includes('COPY.*public')) {
    console.log('✅ Dockerfile references public directory');
  } else {
    console.log('⚠️ Dockerfile doesn\'t explicitly copy public directory');
  }
}

// Check environment variables
console.log('\n🔧 Environment configuration...');
console.log(`NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL || 'not set'}`);
console.log(`NODE_ENV: ${process.env.NODE_ENV || 'not set'}`);

// Summary
console.log('\n📊 Validation Summary:');
console.log(workerFound ? '✅ PDF worker found' : '❌ PDF worker missing or invalid');
console.log(workerSize >= MIN_WORKER_SIZE ? '✅ Worker file size valid' : '❌ Worker file size too small');
console.log(fs.existsSync('.next/standalone') ? '✅ Standalone build available' : '⚠️ Standalone build missing');

if (workerFound && workerSize >= MIN_WORKER_SIZE) {
  console.log('\n🎉 Build validation PASSED! Ready for production deployment.');
  process.exit(0);
} else {
  console.log('\n❌ Build validation FAILED. Please address the issues above.');
  process.exit(1);
}
