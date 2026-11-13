// Registra la cuenta de un guion de pantalla. Si el servidor no la crea, el guion se corta acá con
// el status y el cuerpo: sin cuenta, todo lo que sigue corre sin sesión y falla lejos de la causa.
module.exports = async (request, base, opciones) => {
  const r = await request.post(base + '/auth/register', opciones);
  if (!r.ok()) throw new Error('registro: ' + r.status() + ' ' + await r.text());
  return r;
};
