#!/usr/bin/env python3
"""
Script mejorado para convertir logo.png a icon.ico
"""
from PIL import Image
import os

def create_icon_from_logo():
    # Rutas de archivos
    logo_path = "frontend/public/logo.png"
    icon_path = "frontend/public/icon.ico"
    
    print(f"Convirtiendo {logo_path} a {icon_path}...")
    
    try:
        # Cargar la imagen original
        img = Image.open(logo_path)
        print(f"Logo original: {img.size} píxeles, modo: {img.mode}")
        
        # Convertir a RGBA si no lo es
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("Convertido a RGBA")
        
        # Crear icono directamente con múltiples tamaños
        # Método más simple y efectivo
        img.save(
            icon_path,
            format='ICO',
            sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256), (512,512)]
        )
        
        print(f"✅ Icono creado exitosamente: {icon_path}")
        
        # Verificar el archivo creado
        if os.path.exists(icon_path):
            file_size = os.path.getsize(icon_path)
            print(f"   Tamaño del archivo: {file_size:,} bytes")
            
            # Verificar que se pueda abrir
            test_icon = Image.open(icon_path)
            print(f"   Verificación exitosa - Modo: {test_icon.mode}, Tamaño: {test_icon.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear el icono: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_icon_from_logo()
