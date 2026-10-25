/* SEPARADORES-1: montos escritos a mano (flete, seguro, gastos, ajustes).
   Convención argentina: «3.480» y «3.480,00» son tres mil cuatrocientos
   ochenta, «3,48» es tres con cuarenta y ocho. Un monto no lleva tres
   decimales, así que «1,500» puede ser mil quinientos o uno con cinco: no se
   adivina, se pregunta. */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const NO_ES_NUMERO = 'Debe ser un numero.';
    const NO_CIERRAN = 'Los puntos y comas no cierran: escribí, por ejemplo, 3.480,50.';

    // Grupos de miles bien armados: «3», «480»; «1», «234», «567».
    function sonMiles(grupos) {
        return /^\d{1,3}$/.test(grupos[0]) && grupos.slice(1).every(g => /^\d{3}$/.test(g));
    }

    // { valor, error }: valor es un número o null (vacío o con error).
    function leer(raw) {
        if (typeof raw === 'number') {
            return isFinite(raw) ? { valor: raw, error: null } : { valor: null, error: NO_ES_NUMERO };
        }
        if (raw === null || raw === undefined) return { valor: null, error: null };
        let s = String(raw).trim();
        if (!s) return { valor: null, error: null };
        let signo = 1;
        if (s[0] === '-') { signo = -1; s = s.slice(1).trim(); }
        if (!/^\d[\d.,]*$/.test(s) || /[.,]$/.test(s)) return { valor: null, error: NO_ES_NUMERO };

        const hayPunto = s.includes('.');
        const hayComa = s.includes(',');
        let entero = s;
        let decimales = '';
        if (hayPunto && hayComa) {
            const dec = s.lastIndexOf('.') > s.lastIndexOf(',') ? '.' : ',';
            const miles = dec === '.' ? ',' : '.';
            const i = s.lastIndexOf(dec);
            decimales = s.slice(i + 1);
            const grupos = s.slice(0, i).split(miles);
            if (s.slice(0, i).includes(dec) || !sonMiles(grupos)) return { valor: null, error: NO_CIERRAN };
            entero = grupos.join('');
        } else if (hayPunto || hayComa) {
            const sep = hayPunto ? '.' : ',';
            const partes = s.split(sep);
            if (partes.length > 2) {
                if (!sonMiles(partes)) return { valor: null, error: NO_CIERRAN };
                entero = partes.join('');
            } else if (/^[1-9]\d{0,2}$/.test(partes[0]) && partes[1].length === 3) {
                if (sep === ',') {
                    // «1,500»: ¿mil quinientos o uno con cinco?
                    const dec = escribir(Number(partes[0] + '.' + partes[1]));
                    return { valor: null, error: '¿' + partes[0] + '.' + partes[1] + ' o ' + dec +
                        '? Escribilo con punto de miles (' + partes[0] + '.' + partes[1] + ') o como ' + dec + '.' };
                }
                entero = partes.join('');  // 3.480: punto de miles
            } else if (/^[1-9]\d{3,}$/.test(partes[0]) && partes[1].length === 3) {
                // SEPARADORES-1b. «2500.125»: ni miles bien escritos ni
                // decimales sin dudas. ¿2.500.125 o 2.500,125?
                const grupos = partes[0].replace(/\B(?=(\d{3})+$)/g, '.');
                const miles = grupos + '.' + partes[1];
                const dec = grupos + ',' + partes[1];
                return { valor: null, error: '¿' + miles + ' o ' + dec +
                    '? Escribilo con puntos de miles (' + miles + ') o como ' + dec + '.' };
            } else {
                entero = partes[0];
                decimales = partes[1];
            }
        }
        const n = signo * Number(entero + (decimales ? '.' + decimales : ''));
        return isFinite(n) ? { valor: n, error: null } : { valor: null, error: NO_ES_NUMERO };
    }

    // Un número para mostrar en un campo, que leer() vuelve a leer igual:
    // 3480 → «3480», 3.48 → «3,48», 1.125 → «1,1250» (tres decimales serían
    // ambiguos).
    function escribir(n) {
        if (typeof n !== 'number' || !isFinite(n)) return '';
        let s = String(n);
        if (/e/i.test(s)) s = n.toFixed(2);
        const [entero, dec] = s.split('.');
        if (!dec) return entero;
        return entero + ',' + (dec.length === 3 ? dec + '0' : dec);
    }

    CDI.montos = Object.freeze({ leer, escribir, NO_ES_NUMERO });
})();
