export default function Login() {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-2xl font-bold mb-4">Iniciar sesión</h1>
      <input type="text" placeholder="Clave de acceso" className="border p-2 rounded mb-2" />
      <button className="bg-blue-600 text-white px-4 py-2 rounded">Entrar</button>
    </div>
  );
}
