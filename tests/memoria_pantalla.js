// Las posiciones tal como las arma la pantalla, con sus funciones reales.
// Uso: node memoria_pantalla.js '<json: {nombre: [función, ...argumentos]}>'
const vm = require('node:vm'), fs = require('node:fs'), path = require('node:path');
const V2 = path.join(__dirname, '..', 'proyecto_maria', 'static', 'v2');

function funcion(archivo, nombre) {
  const fuente = fs.readFileSync(path.join(V2, archivo), 'utf8');
  const inicio = fuente.indexOf(`function ${nombre}(`);
  if (inicio < 0) throw new Error(`${nombre} no está en ${archivo}`);
  let i = fuente.indexOf('{', inicio), abiertas = 0;
  do { abiertas += { '{': 1, '}': -1 }[fuente[i]] || 0; i++; } while (abiertas);
  return fuente.slice(inicio, i);
}

const CDI = {};
const ctx = vm.createContext({ CDI });
vm.runInContext(funcion('app_v2.js', 'formatNcm') + '\nCDI.formatNcm = formatNcm;', ctx);
vm.runInContext(funcion('screens/ncm.js', 'buildSimPosition') + '\nCDI.buildSimPosition = buildSimPosition;', ctx);

const pedidos = JSON.parse(process.argv[2]);
const salida = {};
for (const [nombre, [fn, ...args]] of Object.entries(pedidos)) salida[nombre] = CDI[fn](...args);
process.stdout.write(JSON.stringify(salida));
