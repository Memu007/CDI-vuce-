// Carga un CUIT en el perfil de la cuenta del guion: el CDDTAGR sale de ahí y, sin él, el servidor no
// genera el TXT. Si no se guarda, el guion se corta acá con el status y el cuerpo, y no al generar.
module.exports = async (request, base) => {
  // El token de la cookie, como lo manda la pantalla: con el CSRF en modo bloqueo, sin él responde 403.
  const token = ((await request.storageState()).cookies.find(c => c.name === 'csrf_token') || {}).value || '';
  const r = await request.put(base + '/api/user/profile', { data: { cuit: '20111111112' }, headers: { 'X-CSRF-Token': token } });
  if (!r.ok()) throw new Error('CUIT del perfil: ' + r.status() + ' ' + await r.text());
};
