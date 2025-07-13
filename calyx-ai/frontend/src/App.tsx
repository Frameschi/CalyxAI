
import { motion } from "framer-motion";

export default function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-green-100 via-white to-green-300">
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="mb-8"
      >
        <img
          src="/logo.png"
          alt="Calyx AI Logo"
          className="h-24 w-24 drop-shadow-lg"
        />
      </motion.div>
      <motion.h1
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.5, duration: 0.8 }}
        className="text-4xl font-bold text-green-700 mb-4"
      >
        ¡Bienvenido a Calyx AI!
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="text-lg text-gray-700 max-w-xl text-center"
      >
        Tu asistente inteligente de nutrición local. Explora recomendaciones, registra tus comidas y descubre cómo mejorar tu salud con IA, ¡todo sin salir de tu PC!
      </motion.p>
    </div>
  );
}
