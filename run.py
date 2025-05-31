import tkinter as tk
from tkinter import messagebox
import socket
import webbrowser
from app import create_app
import os
import threading
from dotenv import load_dotenv

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def run_flask():
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)

def open_browser():
    webbrowser.open(f'http://{get_local_ip()}:5000')

def create_gui():
    root = tk.Tk()
    root.title("Auto Video Generator")
    root.geometry("400x200")
    root.configure(bg='#2a2d32')
    
    # Set icon
    if os.path.exists('vidgen.ico'):
        root.iconbitmap('vidgen.ico')

    # Style
    style = {
        'bg': '#2a2d32',
        'fg': '#e0e0e0',
        'font': ('Helvetica', 10),
        'pady': 10
    }

    # Header
    header = tk.Label(
        root, 
        text="Auto Video Generator Server", 
        font=('Helvetica', 14, 'bold'),
        bg=style['bg'],
        fg='#00c2cb',
        pady=15
    )
    header.pack()

    # IP Address display
    ip_addr = get_local_ip()
    ip_label = tk.Label(
        root,
        text=f"Server running at: http://{ip_addr}:5000",
        bg=style['bg'],
        fg=style['fg'],
        font=style['font'],
        pady=style['pady']
    )
    ip_label.pack()

    # Open browser button
    open_btn = tk.Button(
        root,
        text="Open in Browser",
        command=open_browser,
        bg='#00adb5',
        fg='white',
        font=style['font'],
        pady=5
    )
    open_btn.pack(pady=10)

    # Creator credit
    creator_label = tk.Label(
        root,
        text="Created by trialota",
        bg=style['bg'],
        fg='#888888',
        font=('Helvetica', 8),
        pady=5
    )
    creator_label.pack(side=tk.BOTTOM)

    return root

if __name__ == '__main__':
    load_dotenv()
    
    # Ensure media directories exist
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(base_dir, 'app', 'static', 'generated_media')
    os.makedirs(os.path.join(static_folder, 'audio'), exist_ok=True)
    os.makedirs(os.path.join(static_folder, 'images'), exist_ok=True)
    os.makedirs(os.path.join(static_folder, 'videos'), exist_ok=True)
    
    # Create and start Flask thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Create and run GUI
    root = create_gui()
    root.mainloop()