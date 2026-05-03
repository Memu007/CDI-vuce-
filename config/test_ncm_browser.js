/**
 * Script para ejecutar en la consola del browser (DevTools)
 * Simula la entrada de NCM con puntos y verifica el auto-formato
 *
 * USO:
 * 1. Abrir http://127.0.0.1:8001/dashboard
 * 2. Abrir DevTools (F12)
 * 3. Ir a Console
 * 4. Copiar y pegar este script completo
 * 5. Ver resultados en console
 */

console.log('🧪 Iniciando tests de NCM Auto-Formato...\n');

// Test 1: NCM con puntos al final
function testCase1() {
    console.log('📋 TEST 1: NCM "2905.19." (con puntos)');

    const input = document.querySelector('[data-field="pieza"]');
    if (!input) {
        console.error('❌ No se encontró input NCM');
        return;
    }

    const originalValue = '2905.19.';
    input.value = originalValue;
    console.log(`   Valor ingresado: "${originalValue}"`);

    // Simular evento blur
    input.dispatchEvent(new Event('blur', { bubbles: true }));

    setTimeout(() => {
        const newValue = input.value;
        const borderColor = input.style.borderColor;

        if (newValue === '290519') {
            console.log(`   ✅ SUCCESS: Campo actualizado a "${newValue}"`);
            console.log(`   ✅ Borde: ${borderColor || 'default'}`);
        } else {
            console.log(`   ❌ FAIL: Campo no se actualizó. Valor: "${newValue}"`);
        }
        console.log('');

        // Siguiente test
        setTimeout(testCase2, 500);
    }, 100);
}

// Test 2: NCM inválido (4 dígitos)
function testCase2() {
    console.log('📋 TEST 2: NCM "2905" (inválido - 4 dígitos)');

    const input = document.querySelector('[data-field="pieza"]');
    const originalValue = '2905';
    input.value = originalValue;
    console.log(`   Valor ingresado: "${originalValue}"`);

    input.dispatchEvent(new Event('blur', { bubbles: true }));

    setTimeout(() => {
        const newValue = input.value;
        const borderColor = input.style.borderColor;
        const hasError = input.classList.contains('input-error');

        if (newValue === '2905' && (borderColor.includes('626') || hasError)) {
            console.log(`   ✅ SUCCESS: Campo no se actualizó (inválido detectado)`);
            console.log(`   ✅ Borde rojo: ${borderColor}`);
            console.log(`   ✅ Error class: ${hasError}`);
        } else {
            console.log(`   ❌ FAIL: Debería marcar error. Valor: "${newValue}"`);
        }
        console.log('');

        setTimeout(testCase3, 500);
    }, 100);
}

// Test 3: NCM formato completo
function testCase3() {
    console.log('📋 TEST 3: NCM "2905.19.00" (formato completo)');

    const input = document.querySelector('[data-field="pieza"]');
    const originalValue = '2905.19.00';
    input.value = originalValue;
    console.log(`   Valor ingresado: "${originalValue}"`);

    input.dispatchEvent(new Event('blur', { bubbles: true }));

    setTimeout(() => {
        const newValue = input.value;

        if (newValue === '29051900') {
            console.log(`   ✅ SUCCESS: Campo actualizado a "${newValue}" (8 dígitos)`);
        } else {
            console.log(`   ❌ FAIL: Esperado "29051900", obtenido "${newValue}"`);
        }
        console.log('');

        setTimeout(testCase4, 500);
    }, 100);
}

// Test 4: NCM con espacios
function testCase4() {
    console.log('📋 TEST 4: NCM "  290519  " (con espacios)');

    const input = document.querySelector('[data-field="pieza"]');
    const originalValue = '  290519  ';
    input.value = originalValue;
    console.log(`   Valor ingresado: "${originalValue}"`);

    input.dispatchEvent(new Event('blur', { bubbles: true }));

    setTimeout(() => {
        const newValue = input.value;

        if (newValue === '290519') {
            console.log(`   ✅ SUCCESS: Espacios removidos → "${newValue}"`);
        } else {
            console.log(`   ❌ FAIL: Esperado "290519", obtenido "${newValue}"`);
        }
        console.log('');

        setTimeout(testCase5, 500);
    }, 100);
}

// Test 5: Capítulo inválido
function testCase5() {
    console.log('📋 TEST 5: NCM "9905.19" (capítulo >97 inválido)');

    const input = document.querySelector('[data-field="pieza"]');
    const originalValue = '9905.19';
    input.value = originalValue;
    console.log(`   Valor ingresado: "${originalValue}"`);

    input.dispatchEvent(new Event('blur', { bubbles: true }));

    setTimeout(() => {
        const newValue = input.value;
        const borderColor = input.style.borderColor;
        const hasError = input.classList.contains('input-error');

        if (newValue === '9905.19' && (borderColor.includes('626') || hasError)) {
            console.log(`   ✅ SUCCESS: Capítulo inválido detectado`);
            console.log(`   ✅ Campo no actualizado: "${newValue}"`);
            console.log(`   ✅ Error visual activo`);
        } else {
            console.log(`   ❌ FAIL: Debería rechazar capítulo 99`);
        }
        console.log('');

        printSummary();
    }, 100);
}

// Resumen final
function printSummary() {
    console.log('═'.repeat(50));
    console.log('📊 RESUMEN DE TESTS');
    console.log('═'.repeat(50));
    console.log('');
    console.log('Si todos los tests pasaron (✅), el auto-formato funciona correctamente.');
    console.log('Si alguno falló (❌), revisar implementación en app.js');
    console.log('');
    console.log('💡 PRÓXIMO PASO:');
    console.log('   Probá manualmente escribiendo "2905.19." en el campo NCM');
    console.log('   y presionando Tab. El campo debería actualizarse a "290519"');
    console.log('');
}

// Iniciar tests
console.log('⏳ Esperando 1 segundo para que el DOM esté listo...\n');
setTimeout(testCase1, 1000);
