#!/bin/bash
# setup_autokinetics_full.sh
# Vollständiges Projekt-Setup für AutoKinetics (C++ + Python + Cython + CMake)
# Inklusive "Hello World"-Implementierung.

set -e

PROJECT_NAME="AutoKinetics"
BINDING_NAME="autokinetics_binding"
PYTHON_PACKAGE="python"

# 1. Root folder
echo "🛠️ Creating project structure..."
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# 2. Core folders and files
mkdir -p cpp "$PYTHON_PACKAGE" examples tests

touch README.md
touch LICENSE
cat > .gitignore <<EOL
/build
__pycache__/
*.pyc
*.so
*.egg-info
*.pyd
${BINDING_NAME}.*
EOL

# 3. C++ IMPLEMENTATION: core.hpp
echo "📝 Creating C++ core.hpp..."
cat > cpp/core.hpp <<EOL
#pragma once

#include <string>

namespace autokinetics {
    /**
     * @brief Gibt einen einfachen Hello-String zurück.
     */
    std::string get_hello_message();
}
EOL

# 4. C++ IMPLEMENTATION: core.cpp
echo "📝 Creating C++ core.cpp..."
cat > cpp/core.cpp <<EOL
#include "core.hpp"
#include <iostream>

namespace autokinetics {
    std::string get_hello_message() {
        return "Hello from C++ Core!";
    }
}
EOL

# 5. MINIMAL CMAKE: Root
echo "⚙️ Creating root CMakeLists.txt..."
cat > CMakeLists.txt <<EOL
cmake_minimum_required(VERSION 3.15)
project(${PROJECT_NAME} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

add_subdirectory(cpp)
EOL

# 6. C++ CMAKE: Library Definition
echo "⚙️ Creating cpp/CMakeLists.txt..."
cat > cpp/CMakeLists.txt <<EOL
add_library(autokinetics STATIC
    core.cpp # <--- Hello World Quelldatei
)

target_include_directories(autokinetics PUBLIC \${CMAKE_CURRENT_SOURCE_DIR})
EOL

# 7. PYTHON API: __init__.py
echo "🐍 Creating python/__init__.py..."
cat > "$PYTHON_PACKAGE"/__init__.py <<EOL
# AutoKinetics Python API
# Importiert die 'hello' Funktion aus dem Cython-Binding-Modul
from .${BINDING_NAME} import hello 
EOL

# 8. CYTHON BINDING: autokinetics_binding.pyx
echo "🐍 Creating Cython binding file..."
cat > "$PYTHON_PACKAGE"/${BINDING_NAME}.pyx <<EOL
# distutils: language = c++

from libcpp.string import string

# Deklariere die C++-Funktion aus core.hpp
cdef extern from "core.hpp" namespace "autokinetics":
    string get_hello_message()

# Python-Schnittstellenfunktion
def hello():
    """
    Ruft die C++-Funktion auf und gibt den String zurück.
    """
    cdef string cpp_message = get_hello_message()
    # Konvertiere den C++-String in einen Python-String
    return cpp_message.decode('utf-8')
EOL

# 9. PYTHON BUILD: setup.py
echo "🐍 Creating setup.py..."
cat > setup.py <<EOL
from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Pfad zum C++-Quellverzeichnis relativ zum setup.py
CPP_DIR = os.path.join(os.path.dirname(__file__), 'cpp')

extensions = [
    Extension("${BINDING_NAME}",
              # Fügt die Cython-Datei und die C++-Quelle hinzu
              sources=["${PYTHON_PACKAGE}/${BINDING_NAME}.pyx", os.path.join(CPP_DIR, "core.cpp")], 
              language="c++",
              # Wichtig: Fügt den Header-Pfad hinzu, damit Cython 'core.hpp' findet
              include_dirs=[CPP_DIR], 
              extra_compile_args=['-std=c++17'])
]

setup(
    name="${PROJECT_NAME}",
    version="0.1.0",
    # Lässt setuptools/Cython das Extension-Modul bauen
    ext_modules=cythonize(extensions),
    # Definiert den Python-Paket-Ordner
    packages=["${PYTHON_PACKAGE}"],
)
EOL

echo ""
echo "✅ ${PROJECT_NAME} Projektstruktur mit Hello World erstellt."
echo "---"
echo "Nächste Schritte:"
echo "1. C++-Bibliothek bauen (optional, aber empfohlen für große Projekte):"
echo "   cd ${PROJECT_NAME} && mkdir build && cd build && cmake .. && make"
echo "2. Python-Binding mit Cython bauen:"
echo "   cd .. # Zurück in den ${PROJECT_NAME} Ordner"
echo "   pip install cython setuptools"
echo "   python setup.py build_ext --inplace"
echo "3. Testen:"
echo "   python -c 'from python import hello; print(hello())'"