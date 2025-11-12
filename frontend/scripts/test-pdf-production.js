#!/usr/bin/env node

/**
 * PDF Production Testing Script
 * Tests PDF loading functionality in production mode
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logStep(step) {
  log(`\n📋 Step ${step}:`, colors.blue);
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green);
}

function logError(message) {
  log(`❌ ${message}`, colors.red);
}

function logWarning(message) {
  log(`⚠️  ${message}`, colors.yellow);
}

function logInfo(message) {
  log(`ℹ️  ${message}`, colors.cyan);
}

function runCommand(command, description) {
  logInfo(`Running: ${description}`);
  try {
    const output = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    logSuccess(description);
    return output.trim();
  } catch (error) {
    logError(`${description} - ${error.message}`);
    return null;
  }
}

async function testPDFProduction() {
  log('🚀 PDF Production Testing Script', colors.blue);
  log('Testing PDF loading functionality in production mode...\n');

  // Step 1: Check if PDF worker exists
  logStep('1');
  const workerPath = path.join(__dirname, '../public/pdf.worker.min.js');
  if (fs.existsSync(workerPath)) {
    const stats = fs.statSync(workerPath);
    logSuccess(`PDF worker found (${Math.round(stats.size / 1024)}KB)`);
  } else {
    logError('PDF worker not found in public directory');
    return false;
  }

  // Step 2: Check Next.js configuration
  logStep('2');
  const nextConfigPath = path.join(__dirname, '../next.config.js');
  if (fs.existsSync(nextConfigPath)) {
    const nextConfig = fs.readFileSync(nextConfigPath, 'utf8');

    if (nextConfig.includes("worker-src 'self' blob: data:")) {
      logSuccess('CSP configuration includes worker support');
    } else {
      logWarning('CSP configuration may not fully support workers');
    }

    if (nextConfig.includes('pdf.worker.min.js')) {
      logSuccess('Next.js config includes PDF worker headers');
    } else {
      logWarning('Next.js config missing PDF worker headers');
    }
  } else {
    logError('Next.js config not found');
    return false;
  }

  // Step 3: Check for PDF.js configuration in components
  logStep('3');
  const componentsDir = path.join(__dirname, '../src/components');
  let enhancedComponents = 0;

  const findEnhancedComponents = (dir) => {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        findEnhancedComponents(filePath);
      } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
        const content = fs.readFileSync(filePath, 'utf8');
        if (content.includes('tryWorkerUrl') && content.includes('fallback worker')) {
          enhancedComponents++;
          logSuccess(`Enhanced PDF worker config found in ${file}`);
        }
      }
    }
  };

  findEnhancedComponents(componentsDir);

  if (enhancedComponents > 0) {
    logInfo(`Found ${enhancedComponents} components with enhanced PDF worker configuration`);
  } else {
    logWarning('No components with enhanced PDF worker configuration found');
  }

  // Step 4: Test build process
  logStep('4');
  logInfo('Testing production build...');

  // Clean previous build
  const nextDir = path.join(__dirname, '../.next');
  if (fs.existsSync(nextDir)) {
    fs.rmSync(nextDir, { recursive: true, force: true });
    logInfo('Cleaned previous build');
  }

  // Run production build
  const buildResult = runCommand('npm run build', 'Production build');
  if (!buildResult) {
    logError('Production build failed');
    return false;
  }

  // Step 5: Check if PDF worker is copied to build
  logStep('5');
  const buildWorkerPath = path.join(__dirname, '../.next/static/chunks/pdf.worker.min.js');
  const publicBuildPath = path.join(__dirname, '../.next/static/media/pdf.worker.min.js');
  const staticWorkerPath = path.join(__dirname, '../.next/public/pdf.worker.min.js');

  let workerFound = false;
  let workerLocations = [];

  if (fs.existsSync(buildWorkerPath)) {
    workerFound = true;
    workerLocations.push('.next/static/chunks/');
  }

  if (fs.existsSync(publicBuildPath)) {
    workerFound = true;
    workerLocations.push('.next/static/media/');
  }

  if (fs.existsSync(staticWorkerPath)) {
    workerFound = true;
    workerLocations.push('.next/public/');
  }

  // Also check if it's in the standalone build
  const standaloneDir = path.join(__dirname, '../.next/standalone');
  if (fs.existsSync(standaloneDir)) {
    const standaloneWorkerPath = path.join(standaloneDir, '.next', 'static', 'chunks', 'pdf.worker.min.js');
    if (fs.existsSync(standaloneWorkerPath)) {
      workerFound = true;
      workerLocations.push('standalone/.next/static/chunks/');
    }
  }

  if (workerFound) {
    logSuccess(`PDF worker found in build at: ${workerLocations.join(', ')}`);
  } else {
    logWarning('PDF worker not found in build output (may be served from public)');
  }

  // Step 6: Test production server (optional)
  logStep('6');
  logInfo('Testing production server...');
  logWarning('This will start the production server on port 3000');
  logInfo('Press Ctrl+C to stop the server after testing');

  log('\n📝 Test Instructions:', colors.cyan);
  log('1. The production server will start automatically');
  log('2. Open http://localhost:3000 in your browser');
  log('3. Navigate to a course and try to load a PDF');
  log('4. Check browser console for PDF worker messages');
  log('5. Press Ctrl+C to stop the server');

  log('\n🔍 Things to check:', colors.yellow);
  log('• Network tab for PDF worker loading');
  log('• Console for PDF.js worker messages');
  log('• CSP headers in Network tab');
  log('• PDF rendering performance');

  // Start production server
  try {
    execSync('npm start', { stdio: 'inherit' });
  } catch (error) {
    log('\n🛑 Production server stopped', colors.yellow);
    logInfo(`Production server exit: ${error instanceof Error ? error.message : 'interrupted'}`);
  }

  return true;
}

// Run the test
if (require.main === module) {
  testPDFProduction()
    .then((success) => {
      if (success) {
        log('\n🎉 PDF production testing completed!', colors.green);
        log('If you encountered issues, check the browser console and network tab');
      } else {
        log('\n💥 PDF production testing failed!', colors.red);
        log('Please check the error messages above and fix them before deploying');
      }
    })
    .catch((error) => {
      logError(`Script error: ${error.message}`);
      process.exit(1);
    });
}

module.exports = { testPDFProduction };
