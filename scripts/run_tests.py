# clan_territorial_simulation/scripts/run_tests.py
import subprocess
import sys
import os

def run_all_tests():
    print("Ejecutando todos los tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests"])
        print("Todos los tests pasaron.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar los tests: {e}")
        sys.exit(1)

def run_specific_test(test_file):
    print(f"Ejecutando tests en {test_file}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", os.path.join("tests", test_file)])
        print(f"Tests en {test_file} pasaron.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar los tests en {test_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        run_specific_test(test_file)
    else:
        run_all_tests()