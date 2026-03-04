# ui/dialogs.py
import tkinter as tk
from config import COLORS

class CustomDialog:

    @staticmethod
    def ask_yes_no(parent, title, message):
        dialog = tk.Toplevel(parent)
        dialog.title(title); dialog.configure(bg=COLORS['bg'])
        dialog.resizable(False, False); dialog.attributes('-topmost', True)
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"400x200+{x}+{y}")
        result = [None]
        main_frame = tk.Frame(dialog, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(main_frame, text=message, font=("Cascadia Code",11),
                 bg=COLORS['bg'], fg=COLORS['fg'], wraplength=360,
                 justify='left').pack(pady=10, expand=True)
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=10, fill='x')
        def on_yes(): result[0]=True;  dialog.destroy()
        def on_no():  result[0]=False; dialog.destroy()
        tk.Button(btn_frame, text="SIM", command=on_yes,
                  bg=COLORS['focus'], fg='#000', font=("Cascadia Code",10,"bold"),
                  relief='flat', padx=10, pady=8, cursor='hand2'
                  ).pack(side='left', padx=10, expand=True)
        tk.Button(btn_frame, text="NÃO", command=on_no,
                  bg=COLORS['accent'], fg=COLORS['fg'], font=("Cascadia Code",10,"bold"),
                  relief='flat', padx=10, pady=8, cursor='hand2'
                  ).pack(side='right', padx=10, expand=True)
        dialog.bind('<Return>', lambda e: on_yes())
        dialog.bind('<Escape>', lambda e: on_no())
        dialog.transient(parent); dialog.grab_set()
        parent.wait_window(dialog)
        return result[0] if result[0] is not None else False

    @staticmethod
    def show_error(parent, title, message):
        dialog = tk.Toplevel(parent)
        dialog.title(title); dialog.configure(bg=COLORS['bg'])
        dialog.resizable(False, False); dialog.attributes('-topmost', True)
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"400x200+{x}+{y}")
        main_frame = tk.Frame(dialog, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(main_frame, text="⚠️ "+title, font=("Cascadia Code",14,"bold"),
                 bg=COLORS['bg'], fg=COLORS['accent']).pack(pady=(0,15))
        tk.Label(main_frame, text=message, font=("Cascadia Code",11),
                 bg=COLORS['bg'], fg=COLORS['fg'], wraplength=360,
                 justify='left').pack(pady=10, expand=True)
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=10, fill='x')
        def on_ok(): dialog.destroy()
        btn = tk.Button(btn_frame, text="OK", command=on_ok,
                        bg=COLORS['accent'], fg=COLORS['fg'],
                        font=("Cascadia Code",10,"bold"),
                        relief='flat', padx=10, pady=8, cursor='hand2')
        btn.pack(expand=True)
        btn.focus()
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_ok())
        dialog.transient(parent); dialog.grab_set()
        parent.wait_window(dialog)

    @staticmethod
    def show_info(parent, title, message):
        dialog = tk.Toplevel(parent)
        dialog.title(title); dialog.configure(bg=COLORS['bg'])
        dialog.resizable(False, False); dialog.attributes('-topmost', True)
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"400x200+{x}+{y}")
        main_frame = tk.Frame(dialog, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(main_frame, text="✓ "+title, font=("Cascadia Code",14,"bold"),
                 bg=COLORS['bg'], fg=COLORS['success']).pack(pady=(0,15))
        tk.Label(main_frame, text=message, font=("Cascadia Code",11),
                 bg=COLORS['bg'], fg=COLORS['fg'], wraplength=360,
                 justify='left').pack(pady=10, expand=True)
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=10, fill='x')
        def on_ok(): dialog.destroy()
        btn = tk.Button(btn_frame, text="OK", command=on_ok,
                        bg=COLORS['success'], fg='#000',
                        font=("Cascadia Code",10,"bold"),
                        relief='flat', padx=10, pady=8, cursor='hand2')
        btn.pack(expand=True)
        btn.focus()
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_ok())
        dialog.transient(parent); dialog.grab_set()
        parent.wait_window(dialog)

