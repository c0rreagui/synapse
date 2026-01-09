
import os
import sys
import importlib
import pkgutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.append(BASE_DIR)
sys.path.append(BACKEND_DIR)

def check_imports():
    print("🔬 Verificando Imports do Backend...")
    
    modules_to_check = []
    
    # Walk through backend dir
    for root, dirs, files in os.walk(BACKEND_DIR):
        if "tests" in root or "venv" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                # Convert path to module name
                rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                module_name = rel_path.replace(os.path.sep, ".").replace(".py", "")
                modules_to_check.append(module_name)

    errors = []
    for mod in modules_to_check:
        try:
            importlib.import_module(mod)
            # print(f"  ✅ {mod}") 
        except Exception as e:
            print(f"  ❌ FALHA ao importar {mod}: {e}")
            errors.append((mod, str(e)))

    if errors:
        with open("import_errors.txt", "w", encoding="utf-8") as f:
            for mod, err in errors:
                f.write(f"MODELO: {mod}\nERRO: {err}\n\n")
        print(f"⚠️ {len(errors)} módulos com erro. Detalhes salvos em import_errors.txt")
    else:
        print("✅ Todos os módulos importados com sucesso.")

if __name__ == "__main__":
    check_imports()
