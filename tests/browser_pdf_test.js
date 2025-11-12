/**
 * Browser-based PDF Loading Test
 * Run this in the browser console to test PDF functionality
 */

// Test PDF loading and PDF.js functionality
class BrowserPDFTest {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.frontendURL = 'http://localhost:3001';
        this.results = [];
    }

    log(testName, passed, message = '') {
        const status = passed ? 'PASS' : 'FAIL';
        this.results.push({ test: testName, status, message });
        console.log(`[${status}] ${testName}: ${message}`);
    }

    async testPDFFileAccess() {
        try {
            const response = await fetch(
                `${this.baseURL}/course-files/90a903c0-4ef6-4415-ae3b-9dbc70ad69a9/books/7a8b3b91-46c0-4b47-9e2b-083f79dc9f29/Caboto%20-%20Enciclopedia%20-%20Treccani.pdf`,
                { method: 'HEAD' }
            );
            const contentType = response.headers.get('content-type');
            const size = response.headers.get('content-length');

            this.log(
                'PDF File Access (Backend)',
                response.ok,
                `${contentType}, Size: ${size} bytes`
            );
            return response.ok;
        } catch (error) {
            this.log('PDF File Access (Backend)', false, error.message);
            return false;
        }
    }

    async testFrontendProxy() {
        try {
            const response = await fetch(
                `${this.frontendURL}/course-files/90a903c0-4ef6-4415-ae3b-9dbc70ad69a9/books/7a8b3b91-46c0-4b47-9e2b-083f79dc9f29/Caboto%20-%20Enciclopedia%20-%20Treccani.pdf`,
                { method: 'HEAD' }
            );
            const contentType = response.headers.get('content-type');

            this.log(
                'PDF File Access (Frontend Proxy)',
                response.ok,
                `${contentType}`
            );
            return response.ok;
        } catch (error) {
            this.log('PDF File Access (Frontend Proxy)', false, error.message);
            return false;
        }
    }

    async testCoursesAPI() {
        try {
            const response = await fetch(`${this.baseURL}/courses/90a903c0-4ef6-4415-ae3b-9dbc70ad69a9`);
            const data = await response.json();
            const materials = data.course?.materials || [];

            // Check if URLs use correct port
            const incorrectPorts = materials.filter(m =>
                m.pdf_url && m.pdf_url.includes('localhost:8001')
            );

            this.log(
                'Courses API & URL Consistency',
                incorrectPorts.length === 0,
                `Found ${incorrectPorts.length} URLs with wrong port`
            );

            return response.ok && incorrectPorts.length === 0;
        } catch (error) {
            this.log('Courses API & URL Consistency', false, error.message);
            return false;
        }
    }

    testPDFJSAvailability() {
        // Check if PDF.js is loaded
        const pdfjsLib = window.pdfjsLib || window['pdfjs-dist/build/pdf'];

        if (pdfjsLib) {
            this.log('PDF.js Availability', true, 'PDF.js is loaded');
            return true;
        } else {
            this.log('PDF.js Availability', false, 'PDF.js not found');
            return false;
        }
    }

    testWorkspaceLoading() {
        // Check if we're on a workspace page
        const isWorkspace = window.location.pathname.includes('/materials/') &&
                           window.location.pathname.includes('/workspace');

        if (isWorkspace) {
            // Check if PDF viewer container exists
            const pdfViewer = document.querySelector('[data-testid="pdf-viewer"]') ||
                           document.querySelector('.react-pdf__Document') ||
                           document.querySelector('#pdf-viewer');

            this.log('Workspace PDF Loading', !!pdfViewer,
                     pdfViewer ? 'PDF viewer found' : 'PDF viewer not found');

            // Check for errors
            const errorElements = document.querySelectorAll('[data-testid="error-message"], .error, .alert-danger');
            const hasErrors = errorElements.length > 0;

            if (hasErrors) {
                const errorTexts = Array.from(errorElements).map(el => el.textContent.trim());
                this.log('Workspace Errors', false, errorTexts.join('; '));
            } else {
                this.log('Workspace Errors', true, 'No error elements found');
            }

            return !!pdfViewer && !hasErrors;
        } else {
            this.log('Workspace Loading Test', false, 'Not on a workspace page');
            return false;
        }
    }

    async testBookDetailPage() {
        const isBookDetail = window.location.pathname.includes('/courses/') &&
                           window.location.pathname.includes('/books/') &&
                           !window.location.pathname.includes('/workspace');

        if (isBookDetail) {
            // Check for book content
            const bookContent = document.querySelector('[data-testid="book-content"]') ||
                              document.querySelector('.book-details') ||
                              document.querySelector('main');

            this.log('Book Detail Page', !!bookContent,
                     bookContent ? 'Book content loaded' : 'Book content not found');

            return !!bookContent;
        } else {
            this.log('Book Detail Page Test', false, 'Not on a book detail page');
            return false;
        }
    }

    async runAllTests() {
        console.log('🚀 Starting Browser PDF Test Suite');
        console.log('='.repeat(50));

        // Run basic tests
        await this.testCoursesAPI();
        await this.testPDFFileAccess();
        await this.testFrontendProxy();
        this.testPDFJSAvailability();

        // Run page-specific tests
        this.testWorkspaceLoading();
        await this.testBookDetailPage();

        // Summary
        console.log('='.repeat(50));
        console.log('📊 TEST SUMMARY');
        console.log('='.repeat(50));

        const passed = this.results.filter(r => r.status === 'PASS').length;
        const total = this.results.length;
        const successRate = ((passed / total) * 100).toFixed(1);

        console.log(`Total Tests: ${total}`);
        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${total - passed}`);
        console.log(`Success Rate: ${successRate}%`);

        const failed = this.results.filter(r => r.status === 'FAIL');
        if (failed.length > 0) {
            console.log('\n❌ FAILED TESTS:');
            failed.forEach(test => {
                console.log(`  • ${test.test}: ${test.message}`);
            });
        }

        return passed === total;
    }
}

// Auto-run if loaded in browser
if (typeof window !== 'undefined') {
    window.browserPDFTest = new BrowserPDFTest();

    // Run tests automatically after page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => window.browserPDFTest.runAllTests(), 1000);
        });
    } else {
        setTimeout(() => window.browserPDFTest.runAllTests(), 1000);
    }

    console.log('📋 PDF Test Suite loaded. Run: browserPDFTest.runAllTests()');
}