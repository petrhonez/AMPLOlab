# main.py
import tkinter as tk
from ui.app import AmploApp

def main():
    root = tk.Tk()
    app = AmploApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()