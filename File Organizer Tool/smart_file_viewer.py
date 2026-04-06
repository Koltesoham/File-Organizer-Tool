import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


# File types used for sorting
FILE_TYPES = {
    "Images": [".png", ".jpg", ".jpeg"],
    "Videos": [".mp4", ".mkv"],
    "Documents": [".pdf", ".txt", ".docx"],
}


selected_folder = ""
current_category = "All Files"
all_files = []
preview_image = None


def get_category(filename):
    """Return the category for a file based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_TYPES.items():
        if ext in extensions:
            return category
    return "Others"


def format_size(path):
    """Return file size in a simple readable format."""
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def load_files():
    """Read files from the selected folder."""
    global all_files
    all_files = []

    if not selected_folder:
        return

    try:
        for name in sorted(os.listdir(selected_folder), key=str.lower):
            path = os.path.join(selected_folder, name)
            if os.path.isfile(path):
                all_files.append(
                    {
                        "name": name,
                        "path": path,
                        "category": get_category(name),
                        "size": format_size(path),
                    }
                )
    except OSError:
        messagebox.showerror("Error", "Could not open this folder.")
        return

    show_files(current_category)


def show_files(category):
    """Show files in the center panel based on category."""
    global current_category
    current_category = category

    for item in file_tree.get_children():
        file_tree.delete(item)

    shown = 0
    for file_info in all_files:
        if category == "All Files" or file_info["category"] == category:
            file_tree.insert("", tk.END, values=(file_info["name"], file_info["category"], file_info["size"]))
            shown += 1

    if shown == 0:
        text = "No files found" if category == "All Files" else f"No {category.lower()} found"
        file_tree.insert("", tk.END, values=(text, "-", "-"))


def select_folder():
    """Let the user choose a folder."""
    global selected_folder, current_category
    folder = filedialog.askdirectory()
    if folder:
        selected_folder = folder
        current_category = "All Files"
        folder_path_var.set(selected_folder)
        load_files()
        clear_preview()


def refresh_files():
    """Reload files from the current folder."""
    load_files()
    clear_preview()


def organize_files():
    """Move files into category subfolders."""
    if not selected_folder:
        messagebox.showwarning("No Folder", "Please select a folder first.")
        return

    moved = 0
    for file_info in all_files:
        category = file_info["category"]
        target_folder = os.path.join(selected_folder, category)
        os.makedirs(target_folder, exist_ok=True)
        target_path = os.path.join(target_folder, file_info["name"])
        shutil.move(file_info["path"], target_path)
        moved += 1

    load_files()
    clear_preview()
    messagebox.showinfo("Success", f"{moved} file(s) organized successfully.")


def clear_preview():
    """Reset preview panel."""
    global preview_image
    preview_image = None
    preview_title.config(text="No file selected")
    preview_label.config(image="", text="Select a file to see preview", compound="center")
    preview_text.config(state="normal")
    preview_text.delete("1.0", tk.END)
    preview_text.insert(tk.END, "Preview details will appear here.")
    preview_text.config(state="disabled")


def show_preview(event=None):
    """Show preview for the selected file."""
    global preview_image
    selected = file_tree.selection()
    if not selected:
        return

    filename = file_tree.item(selected[0], "values")[0]
    file_info = next((f for f in all_files if f["name"] == filename), None)
    if not file_info:
        return

    ext = os.path.splitext(file_info["name"])[1].lower()
    preview_title.config(text=file_info["name"])
    preview_label.config(image="", text="")
    preview_text.config(state="normal")
    preview_text.delete("1.0", tk.END)

    if file_info["category"] == "Images" and Image:
        try:
            image = Image.open(file_info["path"])
            image.thumbnail((260, 200))
            preview_image = ImageTk.PhotoImage(image)
            preview_label.config(image=preview_image)
            preview_text.insert(tk.END, f"Type: Image\nSize: {file_info['size']}")
        except Exception:
            preview_label.config(text="Image preview not available", compound="center")
    elif ext == ".txt":
        preview_label.config(text="Text Preview", compound="center")
        try:
            with open(file_info["path"], "r", encoding="utf-8", errors="ignore") as file:
                lines = "".join(file.readlines()[:10])
            preview_text.insert(tk.END, lines if lines else "Text file is empty.")
        except Exception:
            preview_text.insert(tk.END, "Could not read this text file.")
    else:
        preview_label.config(text="File Info", compound="center")
        preview_text.insert(
            tk.END,
            f"Name: {file_info['name']}\n"
            f"Category: {file_info['category']}\n"
            f"Size: {file_info['size']}\n"
            f"Path: {file_info['path']}",
        )

    preview_text.config(state="disabled")


# Main window
root = tk.Tk()
root.title("Smart File Viewer")

# Set window icon if the icon file exists
icon_path = "filemanagericon.ico"
if os.path.exists(icon_path):
    try:
        root.iconbitmap(icon_path)
    except tk.TclError:
        pass

root.geometry("1100x620")
root.minsize(900, 500)

folder_path_var = tk.StringVar(value="No folder selected")


# Top bar
top_frame = ttk.Frame(root, padding=10)
top_frame.pack(fill="x")

ttk.Button(top_frame, text="Select Folder", command=select_folder).pack(side="left")
ttk.Entry(top_frame, textvariable=folder_path_var).pack(side="left", fill="x", expand=True, padx=10)
ttk.Button(top_frame, text="Organize Files", command=organize_files).pack(side="right", padx=(10, 0))
ttk.Button(top_frame, text="Refresh", command=refresh_files).pack(side="right")


# Main layout
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)
main_frame.columnconfigure(1, weight=1)
main_frame.columnconfigure(2, weight=1)
main_frame.rowconfigure(0, weight=1)


# Left sidebar
sidebar = ttk.Frame(main_frame, padding=10)
sidebar.grid(row=0, column=0, sticky="ns")

ttk.Label(sidebar, text="Categories", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

for category in ["All Files", "Images", "Videos", "Documents", "Others"]:
    ttk.Button(sidebar, text=category, width=18, command=lambda c=category: show_files(c)).pack(pady=4, fill="x")


# Center panel
center = ttk.Frame(main_frame, padding=10)
center.grid(row=0, column=1, sticky="nsew")
center.columnconfigure(0, weight=1)
center.rowconfigure(1, weight=1)

ttk.Label(center, text="Files", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

tree_frame = ttk.Frame(center)
tree_frame.grid(row=1, column=0, sticky="nsew")
tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)

file_tree = ttk.Treeview(tree_frame, columns=("Name", "Category", "Size"), show="headings")
file_tree.heading("Name", text="File Name")
file_tree.heading("Category", text="Type")
file_tree.heading("Size", text="Size")
file_tree.column("Name", width=260)
file_tree.column("Category", width=100, anchor="center")
file_tree.column("Size", width=80, anchor="center")
file_tree.grid(row=0, column=0, sticky="nsew")
file_tree.bind("<<TreeviewSelect>>", show_preview)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=file_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
file_tree.configure(yscrollcommand=scrollbar.set)


# Right preview panel
preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
preview_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
preview_frame.columnconfigure(0, weight=1)
preview_frame.rowconfigure(2, weight=1)

preview_title = ttk.Label(preview_frame, text="No file selected", font=("Segoe UI", 11, "bold"))
preview_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

preview_label = ttk.Label(preview_frame, text="Select a file to see preview", anchor="center")
preview_label.grid(row=1, column=0, sticky="ew", pady=(0, 10))

preview_text = tk.Text(preview_frame, height=12, wrap="word")
preview_text.grid(row=2, column=0, sticky="nsew")
preview_text.config(state="disabled")


clear_preview()
root.mainloop()
