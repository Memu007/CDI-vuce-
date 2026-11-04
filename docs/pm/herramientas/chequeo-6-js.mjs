// Funciones de archivos JS/TS, y casos del archivo de casos, como JSON para chequeo-6.py.
// Uso: node chequeo-6-js.mjs <sha> <archivo de casos> <función de caso> <ruta>...
// (lee cada archivo con git show; los dos del medio vienen de la configuración de chequeo-6.py)
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';

const git = (...args) => execFileSync('git', args, { encoding: 'utf8', maxBuffer: 1 << 28 });
const raiz = git('rev-parse', '--show-toplevel').trim();
// Desde la raíz del repo; si no hay node_modules, require mira NODE_PATH.
const ts = createRequire(`${raiz}/package.json`)('typescript');

function nombreDe(f) {
  if (f.name) return f.name.getText();
  const p = f.parent;
  if (ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p) || ts.isPropertyDeclaration(p)) return p.name.getText();
  if (ts.isCallExpression(p)) return `${p.expression.getText().split('\n')[0].slice(-30)}(…)`;
  return '<anónima>';
}

const [sha, archivoCasos, funcionCaso, ...rutas] = process.argv.slice(2);
const esCallbackDeCaso = (f) => ts.isCallExpression(f.parent) && f.parent.expression.getText() === funcionCaso;

function funciones(fuente, linea) {
  const out = [];
  const visitar = (nodo, nombres) => {
    let propios = nombres;
    if (ts.isFunctionLike(nodo) && nodo.body) {
      propios = [...nombres, nombreDe(nodo)];
      // El cuerpo de un caso se mide como caso, no como función.
      if (!esCallbackDeCaso(nodo)) {
        out.push({ nombre: propios.join('.'), desde: linea(nodo.getStart(fuente)), hasta: linea(nodo.end) });
      }
    }
    ts.forEachChild(nodo, (h) => visitar(h, propios));
  };
  visitar(fuente, []);
  return out;
}

function numeroDeCaso(s) {
  const llamada = ts.isExpressionStatement(s) && ts.isAwaitExpression(s.expression) && s.expression.expression;
  if (!llamada || !ts.isCallExpression(llamada) || llamada.expression.getText() !== funcionCaso) return null;
  const n = llamada.arguments[0];
  return n && ts.isNumericLiteral(n) ? Number(n.text) : null;
}

function declaraciones(sentencias) {
  const declara = new Map();
  sentencias.forEach((s, i) => {
    if (ts.isVariableStatement(s)) {
      for (const d of s.declarationList.declarations) if (ts.isIdentifier(d.name)) declara.set(d.name.text, i);
    } else if ((ts.isFunctionDeclaration(s) || ts.isClassDeclaration(s)) && s.name) {
      declara.set(s.name.text, i);
    }
  });
  return declara;
}

function usos(sentencias, declara) {
  const usos = new Map();
  sentencias.forEach((s, i) => {
    const mirar = (n) => {
      const esPropiedad = n.parent && ts.isPropertyAccessExpression(n.parent) && n.parent.name === n;
      if (ts.isIdentifier(n) && !esPropiedad && declara.has(n.text) && declara.get(n.text) !== i) {
        const d = declara.get(n.text);
        if (!usos.has(d)) usos.set(d, new Set());
        usos.get(d).add(i);
      }
      ts.forEachChild(n, mirar);
    };
    mirar(s);
  });
  return usos;
}

// Una declaración de arriba es de un caso si sólo la usa ese caso, directo o
// a través de otras declaraciones que también son sólo suyas.
function duenios(caso, usosDe, esDeclaracion) {
  const duenio = new Map();
  for (let cambio = true; cambio; ) {
    cambio = false;
    for (const [d, quienes] of usosDe) {
      if (duenio.has(d)) continue;
      const de = [...quienes].map((q) => (caso.has(q) ? caso.get(q) : duenio.has(q) ? duenio.get(q) : esDeclaracion.has(q) ? undefined : 'compartida'));
      if (de.includes(undefined)) continue;
      duenio.set(d, new Set(de).size === 1 ? de[0] : 'compartida');
      cambio = true;
    }
  }
  return duenio;
}

function casos(fuente, linea) {
  const sentencias = fuente.statements;
  const caso = new Map();
  sentencias.forEach((s, i) => { const n = numeroDeCaso(s); if (n !== null) caso.set(i, n); });
  const declara = declaraciones(sentencias);
  const duenio = duenios(caso, usos(sentencias, declara), new Set(declara.values()));
  const tramo = (i) => [linea(sentencias[i].getStart(fuente)), linea(sentencias[i].end)];
  return [...caso].map(([i, n]) => ({
    n,
    cuerpo: tramo(i),
    propias: [...duenio].filter(([, c]) => c === n).map(([d]) => tramo(d)),
  }));
}

const salida = {};
for (const ruta of rutas) {
  const texto = git('show', `${sha}:${ruta}`);
  const tipo = ruta.endsWith('.tsx') ? ts.ScriptKind.TSX : ruta.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS;
  const fuente = ts.createSourceFile(ruta, texto, ts.ScriptTarget.Latest, true, tipo);
  const linea = (pos) => fuente.getLineAndCharacterOfPosition(pos).line + 1;
  salida[ruta] = { funciones: funciones(fuente, linea) };
  if (ruta === archivoCasos) salida[ruta].casos = casos(fuente, linea);
}
process.stdout.write(JSON.stringify(salida));
