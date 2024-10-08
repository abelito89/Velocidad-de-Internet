import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import speedtest
import os
import ssl
from urllib.request import Request, urlopen
import requests
import threading
from typing import Optional
from pydantic import BaseModel, ValidationError, Field, field_validator
import re

class ProxyConfig(BaseModel):
    proxy_user: str = Field(..., min_length=1)
    proxy_pass: str = Field(..., min_length=1)
    proxy_ip: str = Field(..., pattern=r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    proxy_port: int = Field(..., gt=0, lt=65536)
    
    @field_validator('proxy_ip')
    def validate_ip(cls, v):
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_pattern.match(v):
            raise ValueError('Invalid IP address format')
        octets = v.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError('IP address octets must be between 0 and 255')
        return v

    @field_validator('proxy_port')
    def validate_port(cls, v):
        if not (0 < v < 65536):
            raise ValueError('Port number must be between 1 and 65535')
        return v


def proxy_config() -> Optional[ProxyConfig]:
    try:
        proxy_config = ProxyConfig(
            proxy_user=simpledialog.askstring("Proxy Configuration", "Enter proxy username:"),
            proxy_pass=simpledialog.askstring("Proxy Configuration", "Enter proxy password:", show='*'),
            proxy_ip=simpledialog.askstring("Proxy Configuration", "Enter proxy IP:"),
            proxy_port=int(simpledialog.askstring("Proxy Configuration", "Enter proxy port:"))
        )
        print("Proxy configuration is valid:", proxy_config)
        return proxy_config
    except ValidationError as e:
        print("Validation error:", e)
        return None

def append_debug_message(message: str) -> None:
    """
    Appends a message to the debug log in the UI.
    
    Args:
        message (str): The debug message to be displayed.
    """
    debug_log.config(state=tk.NORMAL)  # Enable editing temporarily
    debug_log.insert(tk.END, f"{message}\n")  # Insert the new message
    debug_log.config(state=tk.DISABLED)  # Disable editing again
    debug_log.see(tk.END)  # Scroll to the end to show the latest message


def check_internet_connection() -> bool:
    """
    Checks if there is an active internet connection by trying to reach Google.
    
    Returns:
        bool: True if internet connection is available, False otherwise.
    """
    try:
        append_debug_message("Intentando conectar a Google...")
        request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=5) as response:
            append_debug_message(f"Estado de la respuesta: {response.status}")
            return response.status == 200
    except Exception as e:
        append_debug_message(f"Error al intentar conectar: {e}")
        return False


def check_proxy() -> Optional[str]:
    """
    Checks if there is an active internet connection, and only requests proxy
    configuration if a direct connection is not available.
    
    Returns:
        Optional[str]: The proxy URL if it exists, otherwise None.
    """
    # Check if system proxy settings already exist
    http_proxy = os.environ.get('http_proxy')
    https_proxy = os.environ.get('https_proxy')
    
    if http_proxy or https_proxy:
        append_debug_message(f"Proxy settings detected:\nhttp_proxy: {http_proxy}\nhttps_proxy: {https_proxy}")
        return http_proxy or https_proxy

    # Step 1: Check internet connection first before requesting proxy settings
    if check_internet_connection():
        append_debug_message("Direct internet connection available, no proxy needed.")
        return None

    # Step 2: If no connection, ask for proxy configuration
    append_debug_message("No internet connection detected, requesting proxy configuration...")
    proxy_config_instance = proxy_config()
    
    if proxy_config_instance:
        os.environ['http_proxy'] = f"http://{proxy_config_instance.proxy_user}:{proxy_config_instance.proxy_pass}@{proxy_config_instance.proxy_ip}:{proxy_config_instance.proxy_port}"
        os.environ['https_proxy'] = f"http://{proxy_config_instance.proxy_user}:{proxy_config_instance.proxy_pass}@{proxy_config_instance.proxy_ip}:{proxy_config_instance.proxy_port}"
        
        append_debug_message(f"Proxy configured:\nhttp_proxy: {os.environ['http_proxy']}\nhttps_proxy: {os.environ['https_proxy']}")
        return os.environ['http_proxy'], proxy_config_instance
    # Retorna None si no hay proxy
    return None, None


def update_progress(value: int) -> None:
    """
    Updates the progress bar and the percentage label with the given value.
    
    Args:
        value (int): The current progress value (0-100).
    """
    if not (0 <= value <= 100):
        raise ValueError("Progress value must be between 0 and 100.")
    progress.config(value=value)
    percentage_label.config(text=f"{value}%")  # Update percentage label


def speed_test() -> None:
    """
    Performs the internet speed test, updating the progress bar as the test progresses.
    Displays download and upload speed results after the test.
    """
    try:
        append_debug_message("Starting speed test...")
        app.after(0, lambda: update_progress(0))
        st = speedtest.Speedtest()

        append_debug_message("Fetching servers...")
        app.after(0, lambda: update_progress(20))
        st.get_servers()

        append_debug_message("Selecting best server...")
        app.after(0, lambda: update_progress(40))
        st.get_best_server()

        append_debug_message("Performing download test...")
        app.after(0, lambda: update_progress(60))
        download_speed = st.download() / 1_000_000  # Convert to Mbps

        append_debug_message("Performing upload test...")
        app.after(0, lambda: update_progress(80))
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps

        append_debug_message(f"Download Speed: {download_speed:.2f} Mbps")
        append_debug_message(f"Upload Speed: {upload_speed:.2f} Mbps")

        app.after(0, lambda: update_progress(100))

        result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps")
        append_debug_message("Speed test completed.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        append_debug_message(f"Error during speed test: {e}")


def get_speed() -> None:
    try:
        proxy = check_proxy()
        append_debug_message(f"Proxy detected: {proxy}")

        if proxy:
            proxy_config_instance = proxy_config()
            if not all([proxy_config_instance.proxy_user, proxy_config_instance.proxy_pass, proxy_config_instance.proxy_ip, proxy_config_instance.proxy_port]):
                raise ValueError("Proxy configuration is required.")

            proxy_port = int(proxy_config_instance.proxy_port)
            proxy_url = f"http://{proxy_config_instance.proxy_user}:{proxy_config_instance.proxy_pass}@{proxy_config_instance.proxy_ip}:{proxy_config_instance.proxy_port}"
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url

            ssl_context = ssl.create_default_context()
            request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, context=ssl_context) as response:
                if response.status != 200:
                    raise Exception("Proxy authentication failed. Please check your credentials and try again.")

        append_debug_message("No proxy detected, performing speed test without proxy.")
        append_debug_message("Verifying internet connection...")
        if not check_internet_connection():
            raise ConnectionError("No internet connection. Please check your connection and try again.")
        threading.Thread(target=speed_test).start()

    except ConnectionError as e:
        messagebox.showerror("Connection Error", str(e))
        append_debug_message(f"Connection error: {e}")
    except Exception as e:
        if "Proxy authentication failed" in str(e):
            messagebox.showerror("Proxy Error", "Proxy authentication failed. Please check your credentials and try again.")
            append_debug_message(f"Proxy error: {e}")
        else:
            messagebox.showerror("Error", str(e))
        append_debug_message(f"Error: {e}")


def create_window() -> Optional[tk.Tk]:
    """
    Creates the main window and sets up the user interface elements including the progress bar,
    result display label, and speed test button. Applies a modern UI design using colors and fonts.
    
    Returns:
        Optional[tk.Tk]: The root window object, or None if an error occurs.
    """
    global app, frame, button, result_label, progress, percentage_label, debug_log
    try:
        app = tk.Tk()
        app.geometry("600x500")
        app.title("Internet Speed Test")
        app.iconbitmap('icono.ico')
        app.config(bg="#1E1E2F")

        frame = tk.Frame(app, bg="#1E1E2F")
        frame.pack(expand=True, pady=20)

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

        progress = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate', maximum=100)
        progress.pack(pady=10)

        percentage_label = tk.Label(frame, text="0%", font=("Helvetica", 12), bg="#1E1E2F", fg="white")
        percentage_label.pack(pady=5)

        result_label = tk.Label(frame, text="", wraplength=400, bg="#1E1E2F", fg="white", font=("Helvetica", 16, "bold"))
        result_label.pack(pady=10)

        # Adding a Text widget for debugging messages
        debug_log = tk.Text(app, height=10, bg="#2E2E3F", fg="white", font=("Helvetica", 10), state=tk.DISABLED)
        debug_log.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)

        return app
    except Exception as e:
        print(f"An error occurred in create_window(): {e}")
        return None


if __name__ == "__main__":
    root = create_window()
    if root:
        root.mainloop()
