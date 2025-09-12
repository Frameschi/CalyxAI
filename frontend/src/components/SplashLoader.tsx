import { motion } from "framer-motion";

export default function SplashLoader() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-16 h-16 border-4 border-white border-t-blue-500 rounded-full animate-spin mx-auto"
    />
  );
}
