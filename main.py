import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import speedtest
import os
import ssl
from urllib.request import Request, urlopen
import threading
from typing import Optional
from pydantic import BaseModel, ValidationError, Field, field_validator
import re

# Define global variables for thread handling and stop flag
test_thread = None
should_stop = False



class ProxyConfig(BaseModel):
    """
    A configuration model for proxy settings.

    Attributes:
        proxy_user (str): The username for the proxy. Must be at least 1 character long.
        proxy_pass (str): The password for the proxy. Must be at least 1 character long.
        proxy_ip (str): The IP address of the proxy. Must match the format xxx.xxx.xxx.xxx where xxx is a number between 0 and 255.
        proxy_port (int): The port number of the proxy. Must be an integer between 1 and 65535.

    Validations:
        - `proxy_ip`: Validates that the IP address format is correct and that each octet is between 0 and 255.
        - `proxy_port`: Validates that the port number is between 1 and 65535.
    """
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
    """
    Prompts the user for proxy configuration details and validates the input.

    This function uses dialog boxes to collect the proxy username, password,
    IP address, and port number from the user. It handles user cancellation and
    validation errors, returning an instance of ProxyConfig if the input is valid
    or None if the input is canceled or invalid.

    Returns:
        Optional[ProxyConfig]: An instance of ProxyConfig if the input is valid;
        None if the user cancels the input or if validation fails.
    """
    proxy_user = simpledialog.askstring("Proxy Configuration", "Enter proxy username:")
    if proxy_user is None:  # Handle cancel button press
        append_debug_message("Proxy configuration canceled by user.")
        return None
    
    proxy_pass = simpledialog.askstring("Proxy Configuration", "Enter proxy password:", show='*')
    if proxy_pass is None:  # Handle cancel button press
        append_debug_message("Proxy configuration canceled by user.")
        return None

    proxy_ip = simpledialog.askstring("Proxy Configuration", "Enter proxy IP:")
    if proxy_ip is None:  # Handle cancel button press
        append_debug_message("Proxy configuration canceled by user.")
        return None

    proxy_port_str = simpledialog.askstring("Proxy Configuration", "Enter proxy port:")
    if proxy_port_str is None:  # Handle cancel button press
        append_debug_message("Proxy configuration canceled by user.")
        return None

    try:
        proxy_port = int(proxy_port_str)
    except ValueError:
        append_debug_message("Invalid port number format.")
        return None

    try:
        proxy_config_instance = ProxyConfig(
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
            proxy_ip=proxy_ip,
            proxy_port=proxy_port
        )
        append_debug_message("Proxy configuration is valid.")
        return proxy_config_instance
    except ValidationError as e:
        append_debug_message(f"Validation error: {e}")
        return None




def append_debug_message(message: str) -> None:
    def append_message():
        debug_log.config(state=tk.NORMAL)  # Enable editing temporarily
        debug_log.insert(tk.END, f"{message}\n")  # Insert the new message
        debug_log.config(state=tk.DISABLED)  # Disable editing again
        debug_log.see(tk.END)  # Scroll to the end to show the latest message
    
    # Asegúrate de que esto se ejecute en el hilo principal
    app.after(0, append_message)



def check_internet_connection() -> bool:
    """
    Checks the internet connection by attempting to connect to Google.

    This function sends a request to Google's homepage and checks the response status.
    It logs the attempt and the response status. If the connection is successful and
    the status code is 200, it returns True. Otherwise, it catches any exceptions,
    logs the error, and returns False.

    Returns:
        bool: True if the connection is successful (status code 200), False otherwise.
    """
    try:
        append_debug_message("Trying to connect to Google to identify the type of internet connection.")
        request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=5) as response:
            append_debug_message(f"Response status: {response.status}")
            return response.status == 200
    except Exception as e:
        append_debug_message(f"Error trying to connect: {e}")
        return False


def check_proxy() -> Optional[str]:
    """
    Checks for existing proxy settings and configures a proxy if necessary.

    This function first checks the environment variables for existing HTTP and HTTPS proxy settings.
    If any proxy settings are detected, it logs this information and returns the HTTP or HTTPS proxy.
    
    If no proxy is set and an internet connection is available, it logs that a direct connection is
    available and returns None. If no internet connection is detected, it prompts the user to
    configure a proxy using the `proxy_config` function.

    If the user cancels the proxy configuration, it logs this event and returns None. Otherwise, 
    it sets the HTTP and HTTPS proxy environment variables using the provided user credentials and IP address,
    and logs that the proxy has been configured.

    Returns:
        Optional[str]: The configured HTTP proxy if successful, or None if no proxy is needed or configuration was canceled.
    """

    http_proxy = os.environ.get('http_proxy')
    https_proxy = os.environ.get('https_proxy')

    if http_proxy or https_proxy:
        append_debug_message(f"Proxy settings detected")
        return http_proxy or https_proxy

    if check_internet_connection():
        append_debug_message("Direct internet connection available, no proxy needed.")
        return None

    append_debug_message("No internet connection detected, requesting proxy configuration...")
    proxy_config_instance = proxy_config()

    if proxy_config_instance is None:  # Handle case when proxy configuration is canceled
        append_debug_message("Proxy authentication canceled. Returning to main window.")
        return None

    os.environ['http_proxy'] = f"http://{proxy_config_instance.proxy_user}:{proxy_config_instance.proxy_pass}@{proxy_config_instance.proxy_ip}:{proxy_config_instance.proxy_port}"
    os.environ['https_proxy'] = os.environ['http_proxy']

    append_debug_message(f"Proxy configured")
    return os.environ['http_proxy']


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
    try:
        app.after(0, lambda: append_debug_message("Starting speed test..."))
        app.after(0, lambda: update_progress(0))
        
        st = speedtest.Speedtest()

        app.after(0, lambda: append_debug_message("Fetching servers..."))
        app.after(0, lambda: update_progress(20))
        st.get_servers()

        app.after(0, lambda: append_debug_message("Selecting best server..."))
        app.after(0, lambda: update_progress(40))
        st.get_best_server()

        app.after(0, lambda: append_debug_message("Performing download test..."))
        app.after(0, lambda: update_progress(60))
        download_speed = st.download() / 1_000_000  # Convert to Mbps

        app.after(0, lambda: append_debug_message("Performing upload test..."))
        app.after(0, lambda: update_progress(80))
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps

        app.after(0, lambda: append_debug_message(f"Download Speed: {download_speed:.2f} Mbps"))
        app.after(0, lambda: append_debug_message(f"Upload Speed: {upload_speed:.2f} Mbps"))

        app.after(0, lambda: update_progress(100))

        app.after(0, lambda: result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\nUpload Speed: {upload_speed:.2f} Mbps"))
        app.after(0, lambda: append_debug_message("Speed test completed."))

    except Exception as e:
        app.after(0, lambda: messagebox.showerror("Error", str(e)))
        app.after(0, lambda: append_debug_message(f"Error during speed test: {e}"))
    finally:
        global test_thread
        test_thread = None  # Liberar el hilo después de finalizar el test, para permitir nuevas pruebas


def get_speed() -> None:
    """
    Initiates an internet speed test, checking for proxy settings before execution.

    This function first checks if a speed test is already in progress. If so, it logs a message and 
    prevents the initiation of a new test. It then verifies the presence of proxy settings and logs 
    the detected proxy.

    If no proxy is detected or if the proxy configuration process is canceled, the function starts 
    a new thread to run the speed test without proxy interference. The thread is set as a daemon to 
    ensure it does not block the application from closing.

    Returns:
        None: This function does not return a value but initiates the speed test process in a separate thread.
    """
    global test_thread
    try:
        if test_thread and test_thread.is_alive():
            append_debug_message("A speed test is already in progress. Please wait.")
            return
        
        proxy = check_proxy()
        append_debug_message(f"Proxy detected: {proxy}")
        
        if proxy is None:
            append_debug_message("No proxy detected, performing speed test without proxy.")
            test_thread = threading.Thread(target=speed_test)
            test_thread.daemon = True
            test_thread.start()
            return
        
        # Si llegamos aquí, significa que check_proxy ya configuró el proxy.
        # No es necesario volver a solicitar la configuración del proxy.
        ssl_context = ssl.create_default_context()
        request = Request('https://www.google.com', headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, context=ssl_context) as response:
            if response.status != 200:
                raise Exception("Proxy authentication failed. Please check your credentials and try again.")
        
        test_thread = threading.Thread(target=speed_test)
        test_thread.start()
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

def on_close() -> None:
    """
    Handles the closing of the application.

    This function is triggered when the application is requested to close. 
    It performs two main actions:
    1. Quits the application, which initiates the closing process.
    2. Destroys the main application window, freeing up resources.

    Returns:
        None: This function does not return a value but ensures proper termination of the application.
    """
    app.quit()  # Cerrar la aplicación
    app.destroy()  # Destruir la ventana



def create_window() -> Optional[tk.Tk]:
    """
    Creates and configures the main application window for the Internet Speed Test application.

    This function initializes a Tkinter window with a specified size, title, and icon. 
    It sets the background color and adds various widgets, including buttons, labels, 
    and a progress bar, to facilitate the speed testing process. Additionally, 
    it captures the close event to ensure proper application termination.

    Returns:
        Optional[tk.Tk]: Returns the main application window instance if created successfully; 
                          otherwise, returns None in case of an error.
    """
    global app, frame, button, result_label, progress, percentage_label, debug_log
    try:
        app = tk.Tk()
        app.geometry("600x500")
        app.title("Internet Speed Test")
        app.iconbitmap('icono.ico')
        app.config(bg="#1E1E2F")

        # Capture the close event and call on_close function
        app.protocol("WM_DELETE_WINDOW", on_close)

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