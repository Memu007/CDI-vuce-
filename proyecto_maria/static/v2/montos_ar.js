/* Montos escritos a mano (flete, seguro, gastos, ajustes).
   Convención argentina: «3.480» y «3.480,00» son tres mil cuatrocientos
   ochenta, «3,48» es tres con cuarenta y ocho. Un monto no lleva tres
   decimales, así que «1,500» puede ser mil quinientos o uno con cinco: no se
   adivina, se pregunta. */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const NO_ES_NUMERO = 'Debe ser un numero.';
    const NO_CIERRAN = 'Los puntos y comas no cierran: escribí, por ejemplo, 3.480,50.';

    // Grupos de miles bien armados: «3», «480»; «1», «234», «567». Sin cero
    // adelante: «01.500.000» no cierra.
    function sonMiles(grupos) {
        return /^[1-9]\d{0,2}$/.test(grupos[0]) && grupos.slice(1).every(g => /^\d{3}$/.test(g));
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
                    const miles = (signo < 0 ? '-' : '') + partes[0] + '.' + partes[1];
                    const dec = escribir(signo * Number(partes[0] + '.' + partes[1]));
                    return { valor: null, error: '¿' + miles + ' o ' + dec +
                        '? Escribilo con punto de miles (' + miles + ') o como ' + dec + '.' };
                }
                entero = partes.join('');  // 3.480: punto de miles
            } else if (/^\d{4,}$/.test(partes[0]) && !/^0+$/.test(partes[0]) && partes[1].length === 3) {
                // «2500.125» (o «01234.500»):
                // ni miles bien escritos ni decimales sin dudas. Las dos
                // lecturas como las escribe escribir(), que leer() lee igual:
                // ¿2500125 o 2500,1250?
                // Más de quince cifras ya no se escriben exactas.
                if (partes[0].replace(/^0+/, '').length + 3 > 15) return { valor: null, error: NO_ES_NUMERO };
                const miles = escribir(signo * Number(partes[0] + partes[1]));
                const dec = escribir(signo * Number(partes[0] + '.' + partes[1]));
                return { valor: null, error: '¿' + miles + ' o ' + dec +
                    '? Escribilo sin separador (' + miles + ') o como ' + dec + '.' };
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
