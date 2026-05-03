const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class E2ETestSuite {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = {
            puppeteer: { passed: 0, failed: 0, details: [] },
            lighthouse: { passed: 0, failed: 0, details: [] },
            debugging: { passed: 0, failed: 0, details: [] }
        };
    }

    async init() {
        console.log('🚀 Inicializando Puppeteer...');
        this.browser = await puppeteer.launch({
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            defaultViewport: { width: 1920, height: 1080 }
        });
        this.page = await this.browser.newPage();
        
        // Capturar console errors y network errors
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                this.results.debugging.details.push({
                    type: 'console_error',
                    message: msg.text(),
                    timestamp: new Date().toISOString()
                });
                this.results.debugging.failed++;
            }
        });

        this.page.on('requestfailed', request => {
            this.results.debugging.details.push({
                type: 'network_error',
                url: request.url(),
                failure: request.failure().errorText,
                timestamp: new Date().toISOString()
            });
            this.results.debugging.failed++;
        });
    }

    async testInterface(interfacePath, testName) {
        console.log(`🧪 Testeando: ${testName}`);
        const testResult = { name: testName, steps: [], passed: 0, failed: 0 };

        try {
            // Navegar a la interfaz
            const fullPath = `file://${path.resolve(interfacePath)}`;
            await this.page.goto(fullPath, { waitUntil: 'networkidle2' });
            testResult.steps.push({ action: 'navigate', status: 'passed', url: fullPath });
            testResult.passed++;

            // Esperar a que cargue el contenido
            await this.page.waitForTimeout(2000);

            // Verificar que el título no esté vacío
            const title = await this.page.title();
            if (title && title.length > 0) {
                testResult.steps.push({ action: 'check_title', status: 'passed', title });
                testResult.passed++;
            } else {
                testResult.steps.push({ action: 'check_title', status: 'failed', title });
                testResult.failed++;
            }

            // Buscar elementos interactivos comunes
            const buttons = await this.page.$$('button, input[type="button"], input[type="submit"]');
            testResult.steps.push({ action: 'find_buttons', status: 'passed', count: buttons.length });
            testResult.passed++;

            // Buscar formularios
            const forms = await this.page.$$('form');
            testResult.steps.push({ action: 'find_forms', status: 'passed', count: forms.length });
            testResult.passed++;

            // Buscar inputs
            const inputs = await this.page.$$('input, textarea, select');
            testResult.steps.push({ action: 'find_inputs', status: 'passed', count: inputs.length });
            testResult.passed++;

            // Si hay botones, intentar hacer click en el primero
            if (buttons.length > 0) {
                try {
                    await buttons[0].click();
                    await this.page.waitForTimeout(1000);
                    testResult.steps.push({ action: 'click_first_button', status: 'passed' });
                    testResult.passed++;
                } catch (error) {
                    testResult.steps.push({ action: 'click_first_button', status: 'failed', error: error.message });
                    testResult.failed++;
                }
            }

            // Si hay inputs, intentar escribir en el primero
            if (inputs.length > 0) {
                try {
                    await inputs[0].type('test input');
                    await this.page.waitForTimeout(500);
                    testResult.steps.push({ action: 'type_in_first_input', status: 'passed' });
                    testResult.passed++;
                } catch (error) {
                    testResult.steps.push({ action: 'type_in_first_input', status: 'failed', error: error.message });
                    testResult.failed++;
                }
            }

            // Capturar screenshot
            const screenshotPath = `screenshots/${testName.replace(/\s+/g, '_')}_${Date.now()}.png`;
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            testResult.steps.push({ action: 'screenshot', status: 'passed', path: screenshotPath });
            testResult.passed++;

            this.results.puppeteer.details.push(testResult);
            this.results.puppeteer.passed += testResult.passed;
            this.results.puppeteer.failed += testResult.failed;

        } catch (error) {
            testResult.steps.push({ action: 'test_error', status: 'failed', error: error.message });
            testResult.failed++;
            this.results.puppeteer.details.push(testResult);
            this.results.puppeteer.failed += testResult.failed;
        }

        console.log(`✅ ${testName}: ${testResult.passed} passed, ${testResult.failed} failed`);
    }

    async runLighthouseAudit(interfacePath, testName) {
        console.log(`📊 Ejecutando auditoría Lighthouse: ${testName}`);
        
        try {
            // Iniciar servidor local para probar las páginas web dinámicas
            const { spawn } = require('child_process');
            const serverProcess = spawn('python3', ['proyecto_maria/server_funcional.py'], {
                stdio: 'pipe',
                detached: true
            });
            
            // Esperar a que el servidor inicie
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            const lighthouse = require('lighthouse');
            const chromeLauncher = require('chrome-launcher');

            const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
            const options = {
                logLevel: 'info',
                output: 'json',
                onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
                port: chrome.port
            };

            // Mapear interfaces a URLs del servidor local
            const urlMap = {
                'Landing Page': 'http://127.0.0.1:8001/',
                'Interfaz Gratuita': 'http://127.0.0.1:8001/gratuita',
                'Grouping Interface': 'http://127.0.0.1:8001/dashboard',
                'Dashboard': 'http://127.0.0.1:8001/dashboard'
            };
            
            const testUrl = urlMap[testName] || `file://${path.resolve(interfacePath)}`;
            console.log(`🔍 Auditando URL: ${testUrl}`);

            const runnerResult = await lighthouse(testUrl, options);
            await chrome.kill();

            // Matar el servidor
            serverProcess.kill('SIGTERM');
            
            const auditResult = {
                name: testName,
                url: testUrl,
                performance: runnerResult.lhr.categories.performance.score * 100,
                accessibility: runnerResult.lhr.categories.accessibility.score * 100,
                bestPractices: runnerResult.lhr.categories['best-practices'].score * 100,
                seo: runnerResult.lhr.categories.seo.score * 100,
                timestamp: new Date().toISOString()
            };

            // Guardar reporte detallado
            const reportPath = `lighthouse_reports/${testName.replace(/\s+/g, '_')}_${Date.now()}.json`;
            fs.writeFileSync(reportPath, JSON.stringify(runnerResult.lhr, null, 2));
            auditResult.reportPath = reportPath;

            this.results.lighthouse.details.push(auditResult);
            
            // Considerar aprobado si todos los scores > 70
            const allGood = auditResult.performance > 70 && 
                           auditResult.accessibility > 70 && 
                           auditResult.bestPractices > 70 && 
                           auditResult.seo > 70;
            
            if (allGood) {
                this.results.lighthouse.passed++;
            } else {
                this.results.lighthouse.failed++;
            }

            console.log(`📊 ${testName}: Performance ${auditResult.performance.toFixed(0)}, Accessibility ${auditResult.accessibility.toFixed(0)}, Best Practices ${auditResult.bestPractices.toFixed(0)}, SEO ${auditResult.seo.toFixed(0)}`);

        } catch (error) {
            console.error(`❌ Error en auditoría Lighthouse para ${testName}:`, error.message);
            this.results.lighthouse.failed++;
            this.results.lighthouse.details.push({
                name: testName,
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                puppeteer: { passed: this.results.puppeteer.passed, failed: this.results.puppeteer.failed },
                lighthouse: { passed: this.results.lighthouse.passed, failed: this.results.lighthouse.failed },
                debugging: { passed: this.results.debugging.passed, failed: this.results.debugging.failed }
            },
            details: this.results
        };

        const reportPath = `testing_report_${Date.now()}.json`;
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        return reportPath;
    }
}

async function main() {
    const testSuite = new E2ETestSuite();
    
    // Crear directorios necesarios
    if (!fs.existsSync('screenshots')) fs.mkdirSync('screenshots');
    if (!fs.existsSync('lighthouse_reports')) fs.mkdirSync('lighthouse_reports');

    try {
        await testSuite.init();

        // Interfaces principales a probar - probar URLs del servidor en vivo
        const interfaces = [
            { path: 'http://127.0.0.1:8001/', name: 'Landing Page' },
            { path: 'http://127.0.0.1:8001/gratuita', name: 'Interfaz Gratuita' },
            { path: 'http://127.0.0.1:8001/dashboard', name: 'Dashboard' }
        ];

        // Ejecutar tests E2E
        console.log('\n🧪 === INICIANDO TESTS E2E (SERVIDOR EN VIVO) ===');
        for (const interface of interfaces) {
            try {
                await testSuite.testInterface(interface.path, interface.name);
            } catch (error) {
                console.log(`⚠️  Error testeando ${interface.name}: ${error.message}`);
            }
        }

        // Ejecutar auditorías Lighthouse
        console.log('\n📊 === INICIANDO AUDITORÍAS LIGHTHOUSE (SERVIDOR EN VIVO) ===');
        for (const interface of interfaces) {
            try {
                await testSuite.runLighthouseAudit(interface.path, interface.name);
            } catch (error) {
                console.log(`⚠️  Error auditando ${interface.name}: ${error.message}`);
            }
        }

        // Generar reporte final
        const reportPath = testSuite.generateReport();
        console.log(`\n📋 Reporte generado: ${reportPath}`);

        // Resumen final
        console.log('\n📊 === RESUMEN FINAL ===');
        console.log(`Puppeteer: ${testSuite.results.puppeteer.passed} passed, ${testSuite.results.puppeteer.failed} failed`);
        console.log(`Lighthouse: ${testSuite.results.lighthouse.passed} passed, ${testSuite.results.lighthouse.failed} failed`);
        console.log(`Debugging: ${testSuite.results.debugging.passed} passed, ${testSuite.results.debugging.failed} failed`);

    } catch (error) {
        console.error('❌ Error en la ejecución:', error);
    } finally {
        await testSuite.cleanup();
    }
}

if (require.main === module) {
    main();
}

module.exports = E2ETestSuite;
