// Pantallas sin wrapper de fetch propio: toda escritura al mismo origen lleva
// el token de la cookie csrf_token, así ninguna llamada nueva se lo olvida.
(function () {
    'use strict';
    const nativeFetch = window.fetch.bind(window);
    const SAFE = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

    window.fetch = function (input, init = {}) {
        const req = input instanceof Request ? input : null;
        const method = String(init.method || (req ? req.method : 'GET')).toUpperCase();
        const url = new URL(req ? req.url : String(input), location.href);
        const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
        if (SAFE.has(method) || url.origin !== location.origin || !m) {
            return nativeFetch(input, init);
        }
        const headers = new Headers(init.headers || (req ? req.headers : undefined));
        if (!headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', decodeURIComponent(m[1]));
        return nativeFetch(input, { ...init, headers });
    };
})();
