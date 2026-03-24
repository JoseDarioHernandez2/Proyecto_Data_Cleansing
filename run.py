import subprocess
import sys

def run_task():
    print("Running proyecto Data_Cleansing...")
    # Ejecuta el main.py
    subprocess.run(["poetry", "run", "python", "main.py"], check=True)
    
    print("Step 2: Starting Streamlit...")
    # Ejecuta streamlit
    subprocess.run(["poetry", "run", "streamlit", "run", "visualizacion/app.py"])

if __name__ == "__main__":
    run_task()