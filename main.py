import tkinter as tk
from tkinter import simpledialog, messagebox
import speedtest
import os
import ssl
from urllib.request import Request, urlopen

# Configurar variables de entorno para el proxy
os.environ['http_proxy'] = 'http://username:password@proxy_ip:proxy_port'
os.environ['https_proxy'] = 'https://username:password@proxy_ip:proxy_port'

def check_proxy():
    http_proxy = os.environ.get('http_proxy')
    https_proxy = os.environ.get('https_proxy')
    print(f"http_proxy: {http_proxy}")  # Mensaje de depuración
    print(f"https_proxy: {https_proxy}")  # Mensaje de depuración
    proxy = http_proxy or https_proxy
    return proxy

def speed_test():
    st = speedtest.Speedtest()
    st.get_servers()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
    
    # Mensajes de depuración para verificar los valores obtenidos
    print(f"Download Speed: {download_speed:.2f} Mbps")
    print(f"Upload Speed: {upload_speed:.2f} Mbps")

    result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps")


def get_speed():
    try:
        # Verificar si hay configuración de proxy
        proxy = check_proxy()
        
        if proxy:
            print("Proxy detected, requesting user input for proxy configuration.")
            
            # Solicitar la configuración del proxy al usuario
            proxy_user = simpledialog.askstring("Proxy Configuration", "Enter proxy username:")
            proxy_pass = simpledialog.askstring("Proxy Configuration", "Enter proxy password:", show='*')
            proxy_ip = simpledialog.askstring("Proxy Configuration", "Enter proxy IP:")
            proxy_port = int(simpledialog.askstring("Proxy Configuration", "Enter proxy port:"))

            if not all([proxy_user, proxy_pass, proxy_ip, proxy_port]):
                raise ValueError("Proxy configuration is required.")

            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
            
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url


            # Usar HTTPS para verificar la conexión del proxy
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, context=ssl_context) as response:
                if response.status != 200:
                    raise Exception("Proxy authentication failed.")
        else:
            print("No proxy detected, performing speed test without proxy.")
            # Realizar prueba de velocidad sin proxy si no hay configuración válida
        speed_test()
        

    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_window():
    global app, frame, button, result_label
    try:
        app = tk.Tk()
        app.title("Internet Speed Test")
        frame = tk.Frame(app)
        frame.pack(pady=20)

        button = tk.Button(frame, text="Test Speed", command=get_speed)
        button.pack()

        result_label = tk.Label(frame, text="", wraplength=400)
        result_label.pack(pady=10)
        
        return app
    except Exception as e:
        print(f"An error occurred in create_window(): {e}")
        return None

if __name__ == "__main__":
    root = create_window()
    if root:
        try:
            root.mainloop()
        except Exception as e:
            print(f"An error occurred during mainloop: {e}")
    else:
        print("Failed to create the main window.")