import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import re

class CustomText(tk.Text):
    """A text widget that supports line numbers and basic auto-indent."""
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # Let the actual widget perform the action
        result = self.tk.call(self._orig, *args)
        # Trigger an event if anything changes so we can update line numbers
        if (args[0] in ("insert", "replace", "delete") or 
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("yview", "moveto")):
            self.event_generate("<<Change>>", when="tail")
        return result

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PyNexus Professional Editor")
        self.root.geometry("1100x750")

        self.style = ttk.Style()
        self.dark_mode = False
        
        # --- UI Components ---
        self.setup_menu()
        
        # Tabbed Interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Status Bar
        self.status_bar = tk.Label(self.root, text="Line: 1 | Col: 0", anchor='e', bd=1, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')

        # Initial Tab
        self.add_new_tab()

        # Keyboard Shortcuts
        self.root.bind("<Control-n>", lambda e: self.add_new_tab())
        self.root.bind("<Control-f>", lambda e: self.find_replace_dialog())
        self.root.bind("<Control-s>", lambda e: self.save_file())

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        file_m = tk.Menu(menubar, tearoff=0)
        file_m.add_command(label="New Tab (Ctrl+N)", command=self.add_new_tab)
        file_m.add_command(label="Open", command=self.open_file)
        file_m.add_command(label="Save (Ctrl+S)", command=self.save_file)
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self.root.quit)
        
        edit_m = tk.Menu(menubar, tearoff=0)
        edit_m.add_command(label="Find & Replace (Ctrl+F)", command=self.find_replace_dialog)
        edit_m.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        
        menubar.add_cascade(label="File", menu=file_m)
        menubar.add_cascade(label="Edit", menu=edit_m)
        self.root.config(menu=menubar)

    def add_new_tab(self, content="", title="Untitled"):
        frame = ttk.Frame(self.notebook)
        
        # Line numbers
        line_nums = tk.Canvas(frame, width=40, highlightthickness=0, bg='#f0f0f0')
        line_nums.pack(side='left', fill='y')

        # Text Area
        text_area = CustomText(frame, undo=True, wrap='none', font=("Consolas", 13))
        text_area.pack(side='left', expand=True, fill='both')
        
        # Scrollbars
        v_scroll = tk.Scrollbar(frame, orient="vertical", command=text_area.yview)
        v_scroll.pack(side='right', fill='y')
        text_area.configure(yscrollcommand=v_scroll.set)

        self.notebook.add(frame, text=title)
        self.notebook.select(frame)

        # Syntax and Line Number logic
        text_area.bind("<<Change>>", lambda e: self.update_ui(text_area, line_nums))
        text_area.bind("<KeyRelease>", lambda e: self.highlight_keywords(text_area))
        text_area.bind("<Return>", lambda e: self.auto_indent(text_area))
        
        if content:
            text_area.insert("1.0", content)
            self.highlight_keywords(text_area)

    def get_current_text(self):
        selected_index = self.notebook.index(self.notebook.select())
        tab_frame = self.notebook.nametowidget(self.notebook.select())
        return tab_frame.winfo_children()[1] # The CustomText widget

    def update_ui(self, text_widget, canvas):
        # Update Line Numbers
        canvas.delete("all")
        i = text_widget.index("@0,0")
        while True:
            dline = text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            canvas.create_text(20, y, anchor="n", text=linenum, fill="gray")
            i = text_widget.index("%s+1line" % i)

        # Update Status Bar
        cursor = text_widget.index(tk.INSERT).split(".")
        self.status_bar.config(text=f"Line: {cursor[0]} | Col: {cursor[1]}")

    def highlight_keywords(self, text_widget):
        # Very basic syntax highlighting for Python
        keywords = r'\b(def|class|if|else|elif|return|import|from|while|for|in|print|with|as)\b'
        text_widget.tag_remove('kw', '1.0', tk.END)
        content = text_widget.get("1.0", tk.END)
        for match in re.finditer(keywords, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            text_widget.tag_add('kw', start, end)
        text_widget.tag_config('kw', foreground='blue' if not self.dark_mode else '#569cd6')

    def auto_indent(self, text_widget):
        line = text_widget.get("insert linestart", "insert")
        match = re.match(r'^(\s+)', line)
        whitespace = match.group(0) if match else ""
        if line.strip().endswith(':'):
            whitespace += "    "
        text_widget.insert("insert", "\n" + whitespace)
        return "break"

    def find_replace_dialog(self):
        search_query = simpledialog.askstring("Find", "Enter text to find:")
        if search_query:
            text_widget = self.get_current_text()
            idx = "1.0"
            while True:
                idx = text_widget.search(search_query, idx, nocase=1, stopindex=tk.END)
                if not idx: break
                lastidx = f"{idx}+{len(search_query)}c"
                text_widget.tag_add('found', idx, lastidx)
                idx = lastidx
            text_widget.tag_config('found', background='yellow', foreground='black')

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        bg = "#212121" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        # In a real app, you'd iterate through all tabs to apply this
        txt = self.get_current_text()
        txt.config(bg=bg, fg=fg, insertbackground=fg)

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".py")
        if path:
            with open(path, "w") as f:
                f.write(self.get_current_text().get("1.0", tk.END))
            self.notebook.tab("current", text=path.split("/")[-1])

    def open_file(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, "r") as f:
                self.add_new_tab(f.read(), path.split("/")[-1])

    def on_tab_change(self, event):
        pass # Can be used for specific tab logic

if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
