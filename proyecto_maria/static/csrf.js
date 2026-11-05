// Pantallas sin wrapper de fetch propio: toda escritura al mismo origen lleva
// el token de la cookie csrf_token, así ninguna llamada nueva se lo olvida.
(function () {
    'use strict';
    const nativeFetch = window.fetch.bind(window);
    const SAFE = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

    // Devuelve el init con el token, o null si el pedido no lo lleva.
    function conToken(input, init) {
        const req = input instanceof Request ? input : null;
        const method = String(init.method || (req ? req.method : 'GET')).toUpperCase();
        if (SAFE.has(method)) return null;
        const url = new URL(req ? req.url : String(input), location.href);
        const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
        if (url.origin !== location.origin || !m) return null;
        const headers = new Headers(init.headers || (req ? req.headers : undefined));
        if (!headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', decodeURIComponent(m[1]));
        return { ...init, headers };
    }

    window.fetch = function (input, init) {
        let conHeader = null;
        // Si algo del pedido no se puede leer, fetch nativo da el error que corresponde.
        try { conHeader = conToken(input, init || {}); } catch (e) { /* sigue sin token */ }
        return conHeader ? nativeFetch(input, conHeader) : nativeFetch(input, init);
    };
})();
