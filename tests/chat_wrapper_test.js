#!/usr/bin/env node

/**
 * Test per verificare la funzionalità ChatWrapper
 * Esegue test di accesso e caricamento della pagina chat
 */

const http = require('http');
const https = require('https');

const BASE_URL = 'http://localhost:3000';
const CHAT_URL = `${BASE_URL}/chat`;

/**
 * Esegue una richiesta HTTP GET
 */
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;

    const req = protocol.get(url, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

/**
 * Test della pagina chat
 */
async function testChatPage() {
  console.log('🧪 Test: Verifica pagina chat...');

  try {
    const response = await fetchUrl(CHAT_URL);

    if (response.statusCode === 200) {
      console.log('✅ Pagina chat accessibile (200 OK)');

      // Verifica che la pagina contenga elementi HTML validi
      if (response.body.includes('Chat con il Tutor AI')) {
        console.log('✅ Titolo della pagina presente');
      } else {
        console.log('⚠️  Titolo della pagina non trovato');
      }

      // Verifica che non ci siano errori JavaScript critici
      if (response.body.includes('Element type is invalid')) {
        console.log('❌ Errore di lazy loading presente');
        return false;
      } else {
        console.log('✅ Nessun errore di lazy loading rilevato');
      }

      return true;
    } else {
      console.log(`❌ Pagina chat non accessibile: ${response.statusCode}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Errore durante la richiesta: ${error.message}`);
    return false;
  }
}

/**
 * Test del backend API
 */
async function testBackendAPI() {
  console.log('🧪 Test: Verifica backend API...');

  try {
    const response = await fetchUrl(`${BASE_URL.replace('3000', '8001')}/health`);

    if (response.statusCode === 200) {
      console.log('✅ Backend API operativo');
      return true;
    } else {
      console.log(`❌ Backend API non operativo: ${response.statusCode}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Backend API non raggiungibile: ${error.message}`);
    return false;
  }
}

/**
 * Test integrale della funzionalità chat
 */
async function runChatTests() {
  console.log('🚀 Inizio test ChatWrapper\n');
  console.log('📍 Testing URL:', CHAT_URL);
  console.log('=' .repeat(50));

  const results = [];

  // Test 1: Backend API
  console.log('\n📋 Test 1: Backend API');
  results.push(await testBackendAPI());

  // Test 2: Pagina chat
  console.log('\n📋 Test 2: Pagina Chat');
  results.push(await testChatPage());

  // Risultati finali
  console.log('\n' + '='.repeat(50));
  console.log('📊 RISULTATI FINALI:');
  console.log('='.repeat(50));

  const passedTests = results.filter(r => r).length;
  const totalTests = results.length;

  console.log(`✅ Test superati: ${passedTests}/${totalTests}`);
  console.log(`❌ Test falliti: ${totalTests - passedTests}/${totalTests}`);
  console.log(`📈 Success rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);

  if (passedTests === totalTests) {
    console.log('\n🎉 Tutti i test superati! ChatWrapper funzionante.');
    process.exit(0);
  } else {
    console.log('\n⚠️  Alcuni test falliti. Controllare i log sopra.');
    process.exit(1);
  }
}

// Esegui i test
if (require.main === module) {
  runChatTests().catch(error => {
    console.error('💥 Errore durante l\'esecuzione dei test:', error);
    process.exit(1);
  });
}

module.exports = { testChatPage, testBackendAPI, runChatTests };