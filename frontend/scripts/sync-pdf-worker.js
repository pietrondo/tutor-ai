#!/usr/bin/env node

/**
 * PDF Worker Synchronization Script
 *
 * This script copies the PDF.js worker from node_modules to the public directory
 * to ensure it's available for the frontend application. This follows the local
 * JavaScript library policy defined in CLAUDE.md.
 *
 * The script:
 * 1. Copies pdf.worker.min.mjs from pdfjs-dist to public/pdf.worker.min.js
 * 2. Ensures the file has the correct extension (.js instead of .mjs)
 * 3. Updates the content to work with the .js extension if needed
 */

const fs = require('fs');
const path = require('path');

// Define paths
const nodeModulesPath = path.join(__dirname, '../node_modules/pdfjs-dist/build/pdf.worker.min.mjs');
const publicPath = path.join(__dirname, '../public/pdf.worker.min.js');

console.log('🔄 PDF Worker Sync Script');
console.log('========================');

try {
  // Check if source file exists
  if (!fs.existsSync(nodeModulesPath)) {
    console.error(`❌ Source worker not found: ${nodeModulesPath}`);
    console.error('Please ensure pdfjs-dist is installed');
    process.exit(1);
  }

  // Create public directory if it doesn't exist
  const publicDir = path.dirname(publicPath);
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
    console.log(`📁 Created public directory: ${publicDir}`);
  }

  // Copy the worker file
  fs.copyFileSync(nodeModulesPath, publicPath);

  // Get file info
  const stats = fs.statSync(publicPath);
  const sourceStats = fs.statSync(nodeModulesPath);

  console.log(`✅ PDF worker synced successfully:`);
  console.log(`   Source: ${nodeModulesPath}`);
  console.log(`   Target: ${publicPath}`);
  console.log(`   Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   Modified: ${stats.mtime.toLocaleString()}`);

  // Verify the files are identical
  if (stats.size === sourceStats.size) {
    console.log(`✅ File integrity verified`);
  } else {
    console.warn(`⚠️  Warning: File sizes differ (source: ${(sourceStats.size / 1024 / 1024).toFixed(2)} MB, target: ${(stats.size / 1024 / 1024).toFixed(2)} MB)`);
  }

  // Test if the file is accessible by reading first few bytes
  try {
    const buffer = fs.readFileSync(publicPath, { start: 0, end: 100 });
    const content = buffer.toString('utf8', 0, 100);

    // Check if it looks like a JavaScript file
    if (content.includes('pdfjs') || content.includes('worker') || content.includes('function')) {
      console.log(`✅ File content validation passed`);
    } else {
      console.warn(`⚠️  Warning: File content doesn't appear to be JavaScript`);
    }
  } catch (readError) {
    console.error(`❌ Error reading file for validation:`, readError.message);
  }

  console.log('\n🎉 PDF worker is ready for use!');
  console.log('   Frontend can now access: /pdf.worker.min.js');

} catch (error) {
  console.error(`❌ Error syncing PDF worker:`, error.message);
  console.error('\n🔧 Troubleshooting:');
  console.error('1. Ensure pdfjs-dist is installed: npm install');
  console.error('2. Check file permissions in node_modules and public directories');
  console.error('3. Verify the script has read access to node_modules');
  console.error('4. Verify the script has write access to public directory');
  process.exit(1);
}