import tkinter as tk
from tkinter import simpledialog, messagebox
import speedtest
import os
import requests
from requests.auth import HTTPProxyAuth
import ssl
from urllib.request import Request, urlopen

def check_proxy():
    proxy = os.environ.get('http_proxy') or os.environ.get('https_proxy')
    return proxy

def get_speed():
    try:
        # Verificar si hay configuración de proxy
        proxy = check_proxy()
        if proxy:
            proxy_user = simpledialog.askstring("Proxy Detected", "Enter proxy username:")
            proxy_pass = simpledialog.askstring("Proxy Detected", "Enter proxy password:", show='*')
            proxy_ip = simpledialog.askstring("Proxy Detected", "Enter proxy IP:")
            proxy_port = simpledialog.askstring("Proxy Detected", "Enter proxy port:")

            if not all([proxy_user, proxy_pass, proxy_ip, proxy_port]):
                raise ValueError("Proxy configuration is required.")

            proxy_url = f"http://{proxy_ip}:{proxy_port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            auth = HTTPProxyAuth(proxy_user, proxy_pass)

            # Usar HTTPS para verificar la conexión del proxy
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, context=ssl_context, proxies=proxies, auth=auth) as response:
                if response.status_code != 200:
                    raise Exception("Proxy authentication failed.")
        else:
            # Realizar prueba de velocidad sin proxy si no hay configuración válida
            st = speedtest.Speedtest()
            st.get_servers()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps

            result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps")

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