// Ejecuta en node los scripts de una plantilla real con un DOM mínimo y un fetch
// que devuelve el cuerpo dado; imprime en JSON lo que la pantalla le muestra a la persona.
// Uso: node front422_pantalla.js <modo> <status> <cuerpo JSON>   (modo: api | reset | landing)
'use strict';
const vm = require('vm');
const fs = require('fs');
const path = require('path');

const RAIZ = path.join(__dirname, '..', 'proyecto_maria');
const [modo, status, cuerpo] = process.argv.slice(2);

// Objeto que acepta cualquier acceso o llamada, para lo que la pantalla toca y la prueba no mira.
const todo = new Proxy(function () {}, {
  get: (t, k) => (k === Symbol.toPrimitive ? () => '' : k === 'then' ? undefined : todo),
  apply: () => todo,
  construct: () => todo,
});

const elementos = {};
function elemento(id) {
  if (!elementos[id]) {
    const oyentes = {};
    elementos[id] = new Proxy({ id, textContent: '', value: '', hidden: false, oyentes,
      addEventListener: (tipo, fn) => { oyentes[tipo] = fn; },
      querySelector: (sel) => elemento(id + ' ' + sel) }, {
      get: (t, k) => (k in t ? t[k] : todo),
      // Como el DOM: textContent guarda el texto de lo que se le asigna.
      set: (t, k, v) => { t[k] = k === 'textContent' ? String(v) : v; return true; },
    });
  }
  return elementos[id];
}

const ctx = {
  console, Response, URLSearchParams, Promise, JSON,
  setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {},
  CustomEvent: function () {}, addEventListener() {},
  FormData: function (form) { this.forEach = (fn) => Object.entries(form.campos || {}).forEach(([k, v]) => fn(v, k)); },
  localStorage: todo, sessionStorage: todo, navigator: todo,
  location: { search: '?token=t', pathname: '/', href: '' },
  document: new Proxy({ getElementById: elemento, querySelector: () => null,
    querySelectorAll: () => [], cookie: '' }, { get: (t, k) => (k in t ? t[k] : todo) }),
  fetch: async () => new Response(cuerpo, { status: Number(status),
    headers: { 'Content-Type': 'application/json' } }),
};
ctx.window = ctx;
vm.createContext(ctx);

function scriptsDe(plantilla) {
  const html = fs.readFileSync(path.join(RAIZ, 'templates', plantilla), 'utf8');
  const res = [];
  for (const m of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)) {
    const src = /src="([^"?]+)/.exec(m[1]);
    if (/application\/ld\+json/.test(m[1])) continue;
    if (src) res.push(fs.readFileSync(path.join(RAIZ, src[1].replace(/^\/static\//, 'static/')), 'utf8'));
    else res.push(m[2].replace(/\{\{[^}]*\}\}/g, ''));
  }
  return res;
}

function correr(plantilla, hasta) {
  for (const codigo of scriptsDe(plantilla)) {
    vm.runInContext(codigo, ctx);
    if (hasta && hasta()) return;
  }
}

async function enviar(id) {
  await elemento(id).oyentes.submit({ preventDefault() {} });
}

const modos = {
  async api() {
    correr('dashboard_v2.html', () => ctx.CDI);
    let r;
    try { r = await ctx.CDI.api('/x', { method: 'POST' }); } catch (e) { return { lanza: { code: e.code, message: e.message } }; }
    const b = await r.json();
    return { status: r.status, texto: b.detail };
  },
  async reset() {
    correr('reset_password.html');
    elemento('password').value = elemento('confirm').value = 'Clave-valida-1';
    await enviar('resetForm');
    return { texto: elemento('msg').textContent };
  },
  async landing() {
    correr('landing.html');
    elemento('registerForm').campos = { name: 'Ana', email: 'ana@example.com', password: 'Clave-valida-1', plan: 'premium' };
    await enviar('registerForm');
    // El alta sigue en una promesa que el oyente no devuelve: se espera a que escriba el error.
    for (let i = 0; i < 100 && !elemento('registerError').textContent; i++) await new Promise((r) => setImmediate(r));
    return { texto: elemento('registerError').textContent };
  },
};

modos[modo]().then(
  (r) => console.log(JSON.stringify(r)),
  (e) => { console.log(JSON.stringify({ error: String(e && e.stack || e) })); process.exitCode = 1; },
);
