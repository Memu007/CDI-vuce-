// Texto para la persona a partir del `detail` de un error de la API. El 422 de
// pydantic llega como lista de {type, loc, msg, ctx} con el mensaje en inglés.
(function (global) {
    'use strict';
    const CAMPOS = {
        username: 'el usuario', email: 'el email', name: 'el nombre',
        password: 'la contraseña', new_password: 'la contraseña', current_password: 'la contraseña',
    };

    function campo(loc) {
        const nombre = (Array.isArray(loc) ? loc : []).filter((p) => typeof p === 'string' && p !== 'body').pop();
        return nombre ? (CAMPOS[nombre] || 'el campo «' + nombre + '»') : 'el dato enviado';
    }

    function mayuscula(t) { return t.charAt(0).toUpperCase() + t.slice(1); }

    function unError(e) {
        if (!e || typeof e !== 'object') return '';
        const c = campo(e.loc);
        const tope = e.ctx && e.ctx.max_length;
        switch (e.type) {
            case 'missing': return 'Falta ' + c + '.';
            case 'json_invalid': return 'Los datos enviados no son JSON válido.';
            case 'model_attributes_type': case 'dict_type': return 'Los datos enviados tienen que ser un objeto.';
            case 'string_type': return mayuscula(c) + ' tiene que ser texto.';
            case 'too_long': case 'string_too_long':
                if (tope) return mayuscula(c) + ' puede tener hasta ' + tope + ' caracteres.';
                break;
            case 'value_error':
                // El mensaje es el de un ValueError del backend, que ya está en castellano.
                if (typeof e.msg === 'string') return e.msg.replace(/^Value error, /, '').replace(/\.?$/, '.');
                break;
        }
        return mayuscula(c) + ' no es válido.';
    }

    global.textoDeError = function (detail, fallback) {
        if (typeof detail === 'string' && detail.trim()) return detail;
        if (Array.isArray(detail)) {
            const textos = Array.from(new Set(detail.map(unError).filter(Boolean)));
            return textos.length ? textos.join(' ') : fallback;
        }
        if (detail && typeof detail === 'object') {
            if (typeof detail.message === 'string') return detail.message;
            if (typeof detail.msg === 'string') return detail.msg;
        }
        return fallback;
    };
})(window);
