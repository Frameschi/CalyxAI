import http.server
import socketserver
import json
import re
import os
import sqlite3
import unicodedata

class CalyxHandler(http.server.BaseHTTPRequestHandler):
    def quitar_acentos(self, texto):
        return ''.join(c for c in unicodedata.normalize('NFD', texto) 
                      if unicodedata.category(c) != 'Mn')
    
    def buscar_alimento(self, nombre_busqueda):
        """Busca alimento en la base de datos"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "datainfo.db")
            if not os.path.exists(db_path):
                return None
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            nombre_sin_acentos = self.quitar_acentos(nombre_busqueda.lower())
            
            query = """
            SELECT * FROM alimentos
            WHERE LOWER(alimento) LIKE ?
            ORDER BY LENGTH(alimento) ASC
            LIMIT 1
            """
            
            cursor.execute(query, (f"%{nombre_sin_acentos}%",))
            row = cursor.fetchone()
            
            if row:
                column_names = [description[0] for description in cursor.description]
                alimento_dict = dict(zip(column_names, row))
                conn.close()
                return alimento_dict
            
            conn.close()
            return None
            
        except Exception as e:
            print(f'Error buscando alimento: {e}')
            return None
    def do_POST(self):
        print(f"POST request to {self.path}")
        if self.path == '/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                print(f"Content-Length: {content_length}")
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    prompt = data.get('prompt', '').strip().lower()
                    print(f"Prompt: {prompt}")
                else:
                    prompt = ''

                # Respuestas inteligentes de fallback
                if 'hola' in prompt or 'hi' in prompt or 'hello' in prompt:
                    response = '¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?'
                
                elif 'ayuda' in prompt or 'help' in prompt:
                    response = 'Puedo ayudarte con consultas nutricionales, información sobre alimentos, cálculos de macronutrientes y consejos dietéticos. ¿Qué necesitas saber?'
                
                elif 'imc' in prompt or 'indice' in prompt or 'masa corporal' in prompt:
                    response = 'Para calcular tu IMC, necesito saber tu peso en kg y tu altura en metros. Por ejemplo: "¿Cuál es mi IMC si peso 70kg y mido 1.75m?". ¿Me das tus datos?'
                
                elif 'calor' in prompt or 'calorias' in prompt or 'kcal' in prompt or 'energia' in prompt:
                    # Intentar extraer cantidad y alimento
                    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|kg|gr|gramos?)\s+(?:de\s+)?([a-zA-Záéíóúñ\s]+)', prompt, re.IGNORECASE)
                    if match:
                        cantidad = float(match.group(1))
                        unidad = match.group(0).split()[1].lower()
                        alimento = match.group(2).strip()
                        
                        # Convertir a gramos si es necesario
                        if unidad.startswith('kg'):
                            cantidad *= 1000
                        
                        print(f"Buscando {cantidad}g de {alimento}")
                        info_base = self.buscar_alimento(alimento)
                        
                        if info_base and info_base.get('energia (kcal)'):
                            energia_100g = float(info_base['energia (kcal)'])
                            energia_total = (energia_100g * cantidad) / 100
                            nombre = info_base.get('alimento', alimento)
                            
                            response = f"{cantidad}g de {nombre} contienen aproximadamente {energia_total:.1f} kcal."
                            if cantidad != 100:
                                response += f" (Basado en {energia_100g} kcal por 100g)"
                        else:
                            response = f'No encontré información calórica específica para "{alimento}". ¿Puedes verificar el nombre del alimento?'
                    else:
                        # Extraer solo alimento sin cantidad
                        alimento_match = re.search(r'(?:de\s+|sobre\s+|en\s+)?([a-zA-Záéíóúñ\s]+)', prompt, re.IGNORECASE)
                        if alimento_match:
                            alimento = alimento_match.group(1).strip()
                            info_base = self.buscar_alimento(alimento)
                            
                            if info_base and info_base.get('energia (kcal)'):
                                energia = info_base['energia (kcal)']
                                nombre = info_base.get('alimento', alimento)
                                response = f"{nombre} contiene {energia} kcal por cada 100g."
                            else:
                                response = f'No encontré información calórica para "{alimento}". ¿Puedes darme más detalles?'
                        else:
                            response = 'Para calcular calorías, dime qué alimento y cantidad quieres consultar. Por ejemplo: "100g de arroz" o "una manzana". ¿Qué alimento te interesa?'
                
                elif 'nutrient' in prompt or 'nutrientes' in prompt or 'tiene' in prompt or 'contiene' in prompt:
                    # Intentar extraer nombre de alimento y buscar en BD
                    alimento_match = re.search(r'(?:nutrientes?|tiene|contiene|de)\s+(?:la|el|las|los)?\s*([a-zA-Záéíóúñ\s]+)', prompt, re.IGNORECASE)
                    if alimento_match:
                        alimento = alimento_match.group(1).strip()
                        print(f"Buscando alimento: {alimento}")
                        info_alimento = self.buscar_alimento(alimento)
                        
                        if info_alimento:
                            nombre = info_alimento.get('alimento', alimento)
                            energia = info_alimento.get('energia (kcal)', 'N/A')
                            proteina = info_alimento.get('proteina (g)', 'N/A')
                            carbohidratos = info_alimento.get('hidratos de carbono (g)', 'N/A')
                            grasas = info_alimento.get('lipidos (g)', 'N/A')
                            fibra = info_alimento.get('fibra (g)', 'N/A')
                            
                            response = f"Información nutricional de {nombre} (por 100g):\n"
                            response += f"• Energía: {energia} kcal\n"
                            response += f"• Proteínas: {proteina} g\n"
                            response += f"• Carbohidratos: {carbohidratos} g\n"
                            response += f"• Grasas: {grasas} g\n"
                            if fibra != 'N/A':
                                response += f"• Fibra: {fibra} g\n"
                            response += f"\n¿Quieres información sobre otro alimento?"
                        else:
                            response = f'No encontré información específica sobre "{alimento}" en mi base de datos. ¿Puedes verificar el nombre o quieres información sobre otro alimento?'
                    else:
                        response = 'Para consultar nutrientes de un alimento, dime el nombre del alimento. Por ejemplo: "¿Qué nutrientes tiene la manzana?". ¿Qué alimento quieres consultar?'
                
                elif 'proteina' in prompt or 'proteína' in prompt or 'protein' in prompt:
                    response = 'Las proteínas son macronutrientes esenciales para el crecimiento y reparación de tejidos. Fuentes ricas incluyen: carnes, pescados, huevos, legumbres (lentejas, garbanzos), nueces y productos lácteos. ¿Quieres información sobre algún alimento específico?'
                
                elif 'carbohidrat' in prompt or 'carbs' in prompt or 'hidratos' in prompt:
                    response = 'Los carbohidratos son la principal fuente de energía. Se clasifican en simples (azúcares) y complejos (cereales integrales, legumbres). Son importantes para el funcionamiento del cerebro y músculos. ¿Te gustaría saber sobre algún tipo específico?'
                
                elif 'grasas' in prompt or 'lipidos' in prompt or 'fat' in prompt:
                    response = 'Las grasas son necesarias para muchas funciones corporales. Incluyen grasas saturadas (carnes, lácteos), monoinsaturadas (aceite de oliva, aguacate) y poliinsaturadas (pescados, nueces). ¿Quieres información sobre algún tipo de grasa?'
                
                elif 'vitamin' in prompt or 'vitamina' in prompt:
                    response = 'Las vitaminas son micronutrientes esenciales. Las más importantes en nutrición incluyen: vitamina A (visión), C (inmunidad), D (huesos), E (antioxidante) y complejo B (energía). ¿Sobre qué vitamina quieres saber?'
                
                elif 'mineral' in prompt or 'minerales' in prompt:
                    response = 'Los minerales son micronutrientes inorgánicos. Los principales incluyen: calcio (huesos), hierro (sangre), zinc (inmunidad), yodo (tiroides), potasio (músculos) y magnesio (nervios). ¿Quieres información sobre algún mineral específico?'
                
                elif 'dieta' in prompt or 'alimentacion' in prompt or 'comida' in prompt:
                    response = 'Una alimentación saludable debe incluir: verduras y frutas (50% de la dieta), cereales integrales, proteínas magras, lácteos bajos en grasa y grasas saludables. La clave es la variedad y el equilibrio. ¿Qué tipo de dieta te interesa?'
                
                elif 'peso' in prompt or 'adelgazar' in prompt or 'bajar' in prompt:
                    response = 'Para perder peso de forma saludable: combina dieta equilibrada con ejercicio, crea déficit calórico moderado (500 kcal/día), incluye proteínas en cada comida, come verduras y frutas, bebe agua y duerme bien. ¿Quieres consejos más específicos?'
                
                else:
                    response = 'Soy tu asistente nutricional. Puedo ayudarte con información sobre alimentos, cálculo de IMC, consejos dietéticos y nutrición general. ¿Qué consulta nutricional tienes?'

                print(f"Sending response: {response[:50]}...")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'message': response, 'console_block': None}).encode())
            except Exception as e:
                print(f'Error en POST: {e}')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Internal server error"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"Calyx AI Backend is running"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    print('Calyx AI Backend - Modo Fallback')
    print('Servidor corriendo en http://localhost:8000')

    try:
        with socketserver.TCPServer(('', 8000), CalyxHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f'Error en servidor: {e}')
    finally:
        print('Servidor detenido')