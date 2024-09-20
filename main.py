import tkinter as tk
from tkinter import simpledialog, messagebox,ttk
import speedtest
import os
import ssl
from urllib.request import Request, urlopen
import threading



def check_proxy():
    http_proxy = os.environ.get('http_proxy')
    https_proxy = os.environ.get('https_proxy')
    print(f"http_proxy: {http_proxy}")  # Mensaje de depuración
    print(f"https_proxy: {https_proxy}")  # Mensaje de depuración
    return http_proxy or https_proxy  # Solo devolver si hay un proxy real

def speed_test():
    try:
        print("Iniciando prueba de velocidad...")
        app.after(0, lambda: progress.config(value=0))  # Inicializar progreso en 0
        st = speedtest.Speedtest()
        
        print("Obteniendo servidores...")
        app.after(0, lambda: progress.config(value=20))  # Actualizar barra al 20%
        st.get_servers()
        
        print("Seleccionando el mejor servidor...")
        app.after(0, lambda: progress.config(value=40))  # Actualizar barra al 40%
        st.get_best_server()
        
        print("Realizando prueba de descarga...")
        app.after(0, lambda: progress.config(value=60))  # Actualizar barra al 60%
        download_speed = st.download() / 1_000_000  # Convertir a Mbps
        
        print("Realizando prueba de subida...")
        app.after(0, lambda: progress.config(value=80))  # Actualizar barra al 80%
        upload_speed = st.upload() / 1_000_000  # Convertir a Mbps
        
        print(f"Download Speed: {download_speed:.2f} Mbps")
        print(f"Upload Speed: {upload_speed:.2f} Mbps")
        
        # Finaliza la barra de progreso en 100%
        app.after(0, lambda: progress.config(value=100))
        
        result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps")
        print("Prueba de velocidad completada.")
    
    except Exception as e:
        messagebox.showerror("Error", str(e))


def get_speed():
    try:
        proxy = check_proxy()
        
        if proxy:
            print("Proxy detected, requesting user input for proxy configuration.")
            proxy_user = simpledialog.askstring("Proxy Configuration", "Enter proxy username:")
            proxy_pass = simpledialog.askstring("Proxy Configuration", "Enter proxy password:", show='*')
            proxy_ip = simpledialog.askstring("Proxy Configuration", "Enter proxy IP:")
            proxy_port = int(simpledialog.askstring("Proxy Configuration", "Enter proxy port:"))

            if not all([proxy_user, proxy_pass, proxy_ip, proxy_port]):
                raise ValueError("Proxy configuration is required.")

            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url

            ssl_context = ssl.create_default_context()
            request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, context=ssl_context) as response:
                if response.status != 200:
                    raise Exception("Proxy authentication failed.")
        
        print("No proxy detected, performing speed test without proxy.")
        # Crear un hilo que ejecute la prueba de velocidad, para que no se bloquee la interfaz durante su ejecucion
        threading.Thread(target=speed_test).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_window():
    global app, frame, button, result_label, progress
    try:
    # Crear la ventana principal
        app = tk.Tk()
        app.geometry("500x400")
        app.title("Internet Speed Test")
        frame = tk.Frame(app)
        frame.pack(pady=20)
        frame.config(bg="#1E1E2F")  # Fondo claro para el frame
        app.config(bg="#1E1E2F")    # Fondo para la ventana principal

        button = tk.Button(
            frame, 
            text="Test Speed", 
            command=get_speed,
            bg="#4CAF50", 
            fg="white", 
            font=("Helvetica", 14, "bold"),
            relief="flat", 
            activebackground="#45a049"
            )
        button.pack()

        result_label = tk.Label(frame, text="", wraplength=400)
        result_label.pack(pady=10)
        # Crear la barra de progreso
        progress = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate', maximum=100)
        progress.pack(pady=10)


        return app
    except Exception as e:
        print(f"An error occurred in create_window(): {e}")
        return None

if __name__ == "__main__":
    root = create_window()
    root.mainloop()
