#!/usr/bin/env python3
"""
Script para sincronizar la versión de Calyx AI en todos los archivos.
Uso: python update_version.py
"""

import os
import re
import json

def read_version():
    """Leer versión desde VERSION.txt"""
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
    with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def update_package_json(version):
    """Actualizar versión en package.json"""
    package_file = os.path.join(os.path.dirname(__file__), 'frontend', 'package.json')

    with open(package_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data['version'] = version

    with open(package_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Actualizado package.json: {version}")

def update_readme(version):
    """Actualizar versión en README.md"""
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')

    with open(readme_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Reemplazar patrón "Versión X.Y.Z"
    new_content = re.sub(r'Versión \d+\.\d+\.\d+', f'Versión {version}', content)

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ Actualizado README.md: {version}")

def main():
    version = read_version()
    print(f"🔄 Sincronizando versión: {version}")
    print()

    update_package_json(version)
    update_readme(version)

    print()
    print("✅ ¡Versión sincronizada en todos los archivos!")
    print()
    print("Para futuras actualizaciones:")
    print("1. Edita VERSION.txt con la nueva versión")
    print("2. Ejecuta: python update_version.py")
    print()
    print("Archivos que se actualizan automáticamente:")
    print("- frontend/package.json")
    print("- README.md")
    print()
    print("Archivos que se actualizan dinámicamente:")
    print("- frontend/src/pages/Settings.tsx (desde backend)")

if __name__ == "__main__":
    main()