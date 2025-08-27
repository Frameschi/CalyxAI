#!/usr/bin/env python3
"""
Script para convertir logo.png a icon.ico con múltiples tamaños
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
        
        # Si la imagen tiene transparencia (RGBA), mantenerla
        # Si no la tiene (RGB), convertir a RGBA para mejor compatibilidad
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("Convertido a RGBA para mantener transparencias")
        
        # Tamaños estándar para archivos ICO (incluye 512x512 para electron-builder)
        sizes = [
            (16, 16),
            (32, 32), 
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
            (512, 512)  # Añadido para electron-builder
        ]
        
        # Crear las imágenes redimensionadas
        icon_images = []
        for size in sizes:
            # Redimensionar manteniendo la relación de aspecto y centrando
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)
            print(f"Creado tamaño: {size[0]}x{size[1]}")
        
        # Guardar como archivo ICO
        icon_images[0].save(
            icon_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in icon_images],
            append_images=icon_images[1:]
        )
        
        print(f"✅ Icono creado exitosamente: {icon_path}")
        print(f"   Tamaños incluidos: {[f'{s[0]}x{s[1]}' for s in sizes]}")
        
        # Verificar el archivo creado
        if os.path.exists(icon_path):
            file_size = os.path.getsize(icon_path)
            print(f"   Tamaño del archivo: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear el icono: {e}")
        return False

if __name__ == "__main__":
    create_icon_from_logo()
