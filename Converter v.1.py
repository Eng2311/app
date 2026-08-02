import tkinter as tk
from tkinter import ttk
import ctypes

# 0 - Светлая, 1 - Серая, 2 - Темная
current_theme_index = 1

THEMES = [
    {  # 0: СВЕТЛАЯ
        "name": "☀️ Светлая",
        "bg": "#f0f0f0", "fg": "#000000", "frame_bg": "#ffffff",
        "entry_bg": "#ffffff", "entry_fg": "#000000",
        "highlight_bg": "#0056b3", "highlight_fg": "#ffffff",
        "border_color": "#d0d0d0",  # Цвет рамок блоков
        "is_dark_sys": 0
    },
    {  # 1: СЕРАЯ
        "name": "... Серая",
        "bg": "#404040", "fg": "#ffffff", "frame_bg": "#555555",
        "entry_bg": "#2b2b2b", "entry_fg": "#ffffff",
        "highlight_bg": "#7a7a7a", "highlight_fg": "#ffffff",
        "border_color": "#666666",  # Цвет рамок блоков
        "is_dark_sys": 1
    },
    {  # 2: ТЕМНАЯ
        "name": "🌙 Темная",
        "bg": "#1e1e1e", "fg": "#e0e0e0", "frame_bg": "#252526",
        "entry_bg": "#2d2d2d", "entry_fg": "#ffffff",
        "highlight_bg": "#0056b3", "highlight_fg": "#ffffff",
        "border_color": "#3c3c3c",  # Темно-серые рамки блоков вместо белых!
        "is_dark_sys": 1
    }
]

# ==========================================
# ВАЛИДАЦИЯ ВВОДА И СИСТЕМНЫЕ ФУНКЦИИ
# ==========================================

def validate_numeric(text_after_change):
    if text_after_change == "": return True
    normalized = text_after_change.replace(',', '.')
    if normalized == "-": return True
    try:
        float(normalized)
        return True
    except ValueError:
        return False

def select_all(event):
    event.widget.selection_range(0, tk.END)

def copy_to_clipboard(text_widget, button_widget):
    text_content = text_widget.get("1.0", tk.END).strip()
    if text_content and text_content not in ("Ожидание ввода...", "Введите число", "Ошибка ввода", "Значение должно быть > 0"):
        root.clipboard_clear()
        root.clipboard_append(text_content)
        root.update()
        
        old_text = button_widget.cget("text")
        button_widget.config(text="✅ Скопировано!", state=tk.DISABLED)
        root.after(1500, lambda: button_widget.config(text=old_text, state=tk.NORMAL))

def cycle_theme():
    global current_theme_index
    current_theme_index = (current_theme_index + 1) % 3
    apply_theme()

def apply_theme():
    colors = THEMES[current_theme_index]
    
    root.config(bg=colors["bg"])
    frame_content.config(bg=colors["bg"]) # Чтобы фон подложкой подстраивался под тему
    frame_top_bar.config(bg=colors["bg"])
    btn_global_theme.config(text=colors["name"], bg=colors["entry_bg"], fg=colors["entry_fg"])
    
    frames = [frame_temp, frame_press, frame_fuel, frame_heat]
    labels = [lbl_title_temp, lbl_title_press, lbl_title_fuel, lbl_title_heat]
    entries = [entry_temp, entry_press, entry_fuel, entry_heat]
    combos = [combo_temp, combo_press, combo_fuel, combo_heat]
    texts = [txt_res_temp, txt_res_press, txt_res_fuel, txt_res_heat]
    copy_btns = [btn_copy_temp, btn_copy_press, btn_copy_fuel, btn_copy_heat]
    
    # Динамически перекрашиваем плоские рамки блоков
    for f in frames: 
        f.config(bg=colors["bg"], highlightbackground=colors["border_color"], highlightcolor=colors["border_color"])
    
    for l in labels:
        l.config(bg=colors["bg"], fg=colors["fg"])
        
    for e in entries: 
        e.config(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["fg"],
                 bd=1, highlightbackground=colors["frame_bg"], highlightcolor=colors["highlight_bg"])
                 
    for c in combos: 
        c.config(background=colors["entry_bg"])
        
    for b in copy_btns: 
        b.config(bg=colors["entry_bg"], fg=colors["entry_fg"], activebackground=colors["highlight_bg"])
    
    for t in texts:
        t.config(bg=colors["frame_bg"], fg=colors["fg"])
        t.tag_configure("highlight", background=colors["highlight_bg"], foreground=colors["highlight_fg"])
        
    try:
        root.update()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        dwma_use_immersive_dark_mode = 20
        dark_flag = ctypes.c_int(colors["is_dark_sys"])
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, dwma_use_immersive_dark_mode, ctypes.byref(dark_flag), ctypes.sizeof(dark_flag)
        )
    except Exception:
        pass
        
    convert_temperature()
    convert_pressure()
    convert_fuel()
    convert_heat()

# ==========================================
# ЛОГИКА КОНВЕРТАЦИИ И ПОДСВЕТКИ
# ==========================================

def update_text_widget(widget, text_lines, highlight_prefix):
    widget.config(state=tk.NORMAL)
    widget.delete("1.0", tk.END)
    for i, line in enumerate(text_lines):
        widget.insert(tk.END, line + "\n")
        if line.startswith(highlight_prefix):
            line_num = i + 1
            widget.tag_add("highlight", f"{line_num}.0", f"{line_num}.end")
    widget.config(state=tk.DISABLED)

def convert_temperature(*args):
    try:
        val_str = entry_temp.get().replace(',', '.')
        if val_str in ("", "-"): 
            update_text_widget(txt_res_temp, ["Ожидание ввода..."], "Ничего")
            return
        val = float(val_str)
        unit = combo_temp.get()
        c, f = (val, val * 9/5 + 32) if unit == "Цельсий (°C)" else ((val - 32) * 5/9, val)
        prefix = "°C:" if unit == "Цельсий (°C)" else "°F:"
        update_text_widget(txt_res_temp, [f"°C: {c:.2f}", f"°F: {f:.2f}"], prefix)
    except ValueError:
        update_text_widget(txt_res_temp, ["Ошибка ввода"], "Ничего")

def convert_pressure(*args):
    try:
        val_str = entry_press.get().replace(',', '.')
        if val_str in ("", "-"):
            update_text_widget(txt_res_press, ["Ожидание ввода..."], "Ничего")
            return
        val = float(val_str)
        unit = combo_press.get()
        
        to_pa = {
            "Паскаль (Па)": 1, "Килопаскаль (кПа)": 1000, "Мегапаскаль (МПа)": 1000000,
            "Бар (бар)": 100000, "Миллибар (мбар)": 100, "Атмосфера (атм)": 101325,
            "мм рт. ст. (Torr)": 133.322, "PSI (фунт/кв. дюйм)": 6894.76,
            "м вод. ст. (m H2O)": 9806.65, "мм вод. ст. (mm H2O)": 9.80665,
            "кгс/м²": 9.80665, "кгс/см² (ат)": 98066.5
        }
        prefixes = {
            "Паскаль (Па)": "Па:", "Килопаскаль (кПа)": "кПа:", "Мегапаскаль (МПа)": "МПа:",
            "Бар (бар)": "бар:", "Миллибар (мбар)": "мбар:", "Атмосфера (атм)": "атм:",
            "мм рт. ст. (Torr)": "мм рт.ст.:", "PSI (фунт/кв. дюйм)": "PSI:",
            "м вод. ст. (m H2O)": "м вод. ст.:", "мм вод. ст. (mm H2O)": "мм вод. ст.:",
            "кгс/м²": "кгс/м²:", "кгс/см² (ат)": "кгс/см²:"
        }
        pa = val * to_pa[unit]
        lines = [
            f"Па: {pa:.1f}", f"кПа: {pa/1000:.3f}", f"МПа: {pa/1000000:.6f}",
            f"бар: {pa/100000:.4f}", f"мбар: {pa/100:.2f}", f"атм: {pa/101325:.4f}",
            f"мм рт.ст.: {pa/133.322:.2f}", f"PSI: {pa/6894.76:.2f}",
            f"м вод. ст.: {pa/9806.65:.4f}", f"мм вод. ст.: {pa/9.80665:.1f}",
            f"кгс/м²: {pa/9.80665:.1f}", f"кгс/см² (ат): {pa/98066.5:.4f}"
        ]
        update_text_widget(txt_res_press, lines, prefixes[unit])
    except ValueError:
        update_text_widget(txt_res_press, ["Ошибка ввода"], "Ничего")

def convert_fuel(*args):
    try:
        val_str = entry_fuel.get().replace(',', '.')
        if val_str in ("", "-"):
            update_text_widget(txt_res_fuel, ["Ожидание ввода..."], "Ничего")
            return
        val = float(val_str)
        unit = combo_fuel.get()
        if val <= 0:
            update_text_widget(txt_res_fuel, ["Значение должно быть > 0"], "Ничего")
            return
        l100, mpg = (val, 235.215 / val) if unit == "л/100км" else (235.215 / val, val)
        prefix = "л/100км:" if unit == "л/100км" else "mpg:"
        update_text_widget(txt_res_fuel, [f"л/100км: {l100:.2f}", f"mpg: {mpg:.2f}"], prefix)
    except ValueError:
        update_text_widget(txt_res_fuel, ["Ошибка ввода"], "Ничего")

def convert_heat(*args):
    try:
        val_str = entry_heat.get().replace(',', '.')
        if val_str in ("", "-"):
            update_text_widget(txt_res_heat, ["Ожидание ввода..."], "Ничего")
            return
        val = float(val_str)
        unit = combo_heat.get()
        
        if unit == "Гкал/ч":
            kwh = val * 1163.0
        elif unit == "МВт/ч":
            kwh = val * 1000.0
        else:
            kwh = val
            
        prefixes = {"Гкал/ч": "Гкал/ч:", "МВт/ч": "МВт/ч:", "кВт/ч": "кВт/ч:"}
        
        lines = [
            f"Гкал/ч: {kwh / 1163.0:.4f}",
            f"МВт/ч: {kwh / 1000.0:.4f}",
            f"кВт/ч: {kwh:.2f}"
        ]
        update_text_widget(txt_res_heat, lines, prefixes[unit])
    except ValueError:
        update_text_widget(txt_res_heat, ["Ошибка ввода"], "Ничего")

# ==========================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (GUI)
# ==========================================

root = tk.Tk()
root.title("Универсальный конвертер величин")

root.geometry("1100x500")
root.resizable(True, True)
root.minsize(1100, 500)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=0)
root.rowconfigure(1, weight=1)

FONT_TITLE = ("Arial", 14, "bold")
FONT_INPUT = ("Arial", 14)
FONT_COMBO = ("Arial", 13)
FONT_RESULT = ("Arial", 13)
FONT_BTN = ("Arial", 10, "bold")

style = ttk.Style()
style.theme_use("classic")

# Текстовые списки (черный цвет шрифта сохранен)
style.configure("TCombobox", foreground="black", fieldforeground="black")
root.option_add("*TCombobox*Listbox.font", FONT_COMBO)
root.option_add("*TCombobox*Listbox.foreground", "black")

vcmd = (root.register(validate_numeric), '%P')

# --- ВЕРХНЯЯ ПАНЕЛЬ С КНОПКОЙ СМЕНЫ ТЕМЫ ---
frame_top_bar = tk.Frame(root)
frame_top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))

btn_global_theme = tk.Button(frame_top_bar, font=FONT_BTN, command=cycle_theme, bd=1, relief=tk.GROOVE, padx=10, pady=5)
btn_global_theme.pack(anchor="ne")

# --- КОНТЕЙНЕР ДЛЯ 4 КОЛОНОК ---
# Добавлен принудительный цвет фона bd=0 и highlightthickness=0, чтобы убрать белую подложку
frame_content = tk.Frame(root, bg="", bd=0, highlightthickness=0)
frame_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
frame_content.rowconfigure(0, weight=1)
for i in range(4):
    frame_content.columnconfigure(i, weight=1, uniform="equal")

# --- 1 КОЛОНКА: ТЕМПЕРАТУРА ---
# Вместо внешних padx в grid, мы используем внутренние отступы и плоскую рамку bd=1
frame_temp = tk.Frame(frame_content, highlightthickness=1, bd=0, padx=15, pady=15)
frame_temp.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)

lbl_title_temp = tk.Label(frame_temp, text=" 🌡️  Температура", font=FONT_TITLE, anchor="w")
lbl_title_temp.pack(fill=tk.X, pady=(0, 5))

entry_temp = tk.Entry(frame_temp, font=FONT_INPUT, validate="key", validatecommand=vcmd)
entry_temp.pack(fill=tk.X, pady=5)
entry_temp.bind("<KeyRelease>", convert_temperature)
entry_temp.bind("<FocusIn>", select_all)

combo_temp = ttk.Combobox(frame_temp, values=["Цельсий (°C)", "Фаренгейт (°F)"], state="readonly", font=FONT_COMBO)
combo_temp.current(0)
combo_temp.pack(fill=tk.X, pady=5)
combo_temp.bind("<<ComboboxSelected>>", convert_temperature)

txt_res_temp = tk.Text(frame_temp, font=FONT_RESULT, bd=0, highlightthickness=0, state=tk.DISABLED, wrap=tk.WORD, height=1)
txt_res_temp.pack(fill=tk.BOTH, expand=True, pady=10)

btn_copy_temp = tk.Button(frame_temp, text="📋 Копировать", font=FONT_BTN, command=lambda: copy_to_clipboard(txt_res_temp, btn_copy_temp), bd=1, relief=tk.GROOVE)
btn_copy_temp.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))


# --- 2 КОЛОНКА: ДАВЛЕНИЕ ---
frame_press = tk.Frame(frame_content, highlightthickness=1, bd=0, padx=15, pady=15)
frame_press.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)

lbl_title_press = tk.Label(frame_press, text=" 🧯  Давление", font=FONT_TITLE, anchor="w")
lbl_title_press.pack(fill=tk.X, pady=(0, 5))

entry_press = tk.Entry(frame_press, font=FONT_INPUT, validate="key", validatecommand=vcmd)
entry_press.pack(fill=tk.X, pady=5)
entry_press.bind("<KeyRelease>", convert_pressure)
entry_press.bind("<FocusIn>", select_all)

press_units = [
    "Паскаль (Па)", "Килопаскаль (кПа)", "Мегапаскаль (МПа)", "Бар (бар)", "Миллибар (мбар)",
    "Атмосфера (атм)", "мм рт. ст. (Torr)", "PSI (фунт/кв. дюйм)", "м вод. ст. (m H2O)",
    "мм вод. ст. (mm H2O)", "кгс/м²", "кгс/см² (ат)"
]
combo_press = ttk.Combobox(frame_press, values=press_units, state="readonly", font=FONT_COMBO)
combo_press.current(1)
combo_press.pack(fill=tk.X, pady=5)
combo_press.bind("<<ComboboxSelected>>", convert_pressure)

txt_res_press = tk.Text(frame_press, font=FONT_RESULT, bd=0, highlightthickness=0, state=tk.DISABLED, wrap=tk.WORD, height=1)
txt_res_press.pack(fill=tk.BOTH, expand=True, pady=10)

btn_copy_press = tk.Button(frame_press, text="📋 Копировать", font=FONT_BTN, command=lambda: copy_to_clipboard(txt_res_press, btn_copy_press), bd=1, relief=tk.GROOVE)
btn_copy_press.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))


# --- 3 КОЛОНКА: РАСХОД ТОПЛИВА ---
frame_fuel = tk.Frame(frame_content, highlightthickness=1, bd=0, padx=15, pady=15)
frame_fuel.grid(row=0, column=2, sticky="nsew", padx=5, pady=10)

lbl_title_fuel = tk.Label(frame_fuel, text=" 🚗  Расход топлива", font=FONT_TITLE, anchor="w")
lbl_title_fuel.pack(fill=tk.X, pady=(0, 5))

entry_fuel = tk.Entry(frame_fuel, font=FONT_INPUT, validate="key", validatecommand=vcmd)
entry_fuel.pack(fill=tk.X, pady=5)
entry_fuel.bind("<KeyRelease>", convert_fuel)
entry_fuel.bind("<FocusIn>", select_all)

combo_fuel = ttk.Combobox(frame_fuel, values=["л/100км", "mpg (мили/галлон)"], state="readonly", font=FONT_COMBO)
combo_fuel.current(0)
combo_fuel.pack(fill=tk.X, pady=5)
combo_fuel.bind("<<ComboboxSelected>>", convert_fuel)

txt_res_fuel = tk.Text(frame_fuel, font=FONT_RESULT, bd=0, highlightthickness=0, state=tk.DISABLED, wrap=tk.WORD, height=1)
txt_res_fuel.pack(fill=tk.BOTH, expand=True, pady=10)

btn_copy_fuel = tk.Button(frame_fuel, text="📋 Копировать", font=FONT_BTN, command=lambda: copy_to_clipboard(txt_res_fuel, btn_copy_fuel), bd=1, relief=tk.GROOVE)
btn_copy_fuel.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))


# --- 4 КОЛОНКА: ТЕПЛО ---
frame_heat = tk.Frame(frame_content, highlightthickness=1, bd=0, padx=15, pady=15)
frame_heat.grid(row=0, column=3, sticky="nsew", padx=5, pady=10)

lbl_title_heat = tk.Label(frame_heat, text=" 🔥  Тепло", font=FONT_TITLE, anchor="w")
lbl_title_heat.pack(fill=tk.X, pady=(0, 5))

entry_heat = tk.Entry(frame_heat, font=FONT_INPUT, validate="key", validatecommand=vcmd)
entry_heat.pack(fill=tk.X, pady=5)
entry_heat.bind("<KeyRelease>", convert_heat)
entry_heat.bind("<FocusIn>", select_all)

heat_units = ["Гкал/ч", "МВт/ч", "кВт/ч"]
combo_heat = ttk.Combobox(frame_heat, values=heat_units, state="readonly", font=FONT_COMBO)
combo_heat.current(0)
combo_heat.pack(fill=tk.X, pady=5)
combo_heat.bind("<<ComboboxSelected>>", convert_heat)

txt_res_heat = tk.Text(frame_heat, font=FONT_RESULT, bd=0, highlightthickness=0, state=tk.DISABLED, wrap=tk.WORD, height=1)
txt_res_heat.pack(fill=tk.BOTH, expand=True, pady=10)

btn_copy_heat = tk.Button(frame_heat, text="📋 Копировать", font=FONT_BTN, command=lambda: copy_to_clipboard(txt_res_heat, btn_copy_heat), bd=1, relief=tk.GROOVE)
btn_copy_heat.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))


# Применяем серую тему при первом запуске
apply_theme()

root.mainloop()
