import datetime
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import winreg
import winsound
import ctypes
from ctypes import wintypes
import time
import subprocess

import customtkinter as ctk
import pandas as pd

# =====================================================================
# ШАГ 1: АВТОМАТИЧЕСКИЙ ЗАПРОС ПРАВ АДМИНИСТРАТОРА
# =====================================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()
# =====================================================================

EVENTLOG_BACKWARDS_READ = 0x0008
EVENTLOG_SEQUENTIAL_READ = 0x0001

# --- Глобальные переменные контроля ---
excel_path = None
monitoring_active = False
is_handling_alert = False
last_system_record_id = 0  # Хранит ID последней записи в ОС на момент старта мониторинга


def select_excel_path(label_widget):
    global excel_path
    file_path = filedialog.asksaveasfilename(
        title="Выберите файл для сохранения логов",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
    )
    if file_path:
        excel_path = file_path
        label_widget.configure(text=f"Файл: {os.path.basename(excel_path)}", text_color="#00FF00")


def log_to_excel(timestamp, process_name, reg_path):
    global excel_path
    if not excel_path:
        return

    new_data = {
        "Дата и Время": [timestamp],
        "Приложение": [process_name],
        "Путь в реестре": [reg_path],
    }
    df_new = pd.DataFrame(new_data)

    try:
        if os.path.exists(excel_path):
            df_old = pd.read_excel(excel_path)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new
        df_final.to_excel(excel_path, index=False)
    except Exception as e:
        print(f"Ошибка записи в Excel: {e}")


def show_alert_window(timestamp, process_name, reg_path):
    global is_handling_alert

    try:
        winsound.Beep(1000, 400)
    except:
        pass

    alert = ctk.CTkToplevel()
    alert.title("КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ")
    alert.geometry("650x320")

    screen_width = alert.winfo_screenwidth()
    screen_height = alert.winfo_screenheight()
    center_x = int(screen_width / 2 - 650 / 2)
    center_y = int(screen_height / 2 - 320 / 2)
    alert.geometry(f"650x320+{center_x}+{center_y}")
    alert.attributes("-topmost", True)

    main_frame = ctk.CTkFrame(alert, fg_color="#FF0000", corner_radius=0)
    main_frame.pack(fill="both", expand=True)

    label_title = ctk.CTkLabel(
        main_frame, text="⚠️ ПОПЫТКА ИЗМЕНЕНИЯ РЕЕСТРА!", font=("Arial", 20, "bold"), text_color="#FFFFFF"
    )
    label_title.pack(pady=(20, 10))

    info_text = f"Время: {timestamp}\n\nПриложение: {process_name}\n\nКуда: {reg_path}"

    label_info = ctk.CTkLabel(
        main_frame, text=info_text, font=("Arial", 13, "bold"), text_color="#FFFFFF", justify="left", wraplength=600
    )
    label_info.pack(pady=10, padx=20)

    def close_and_release():
        global is_handling_alert
        alert.destroy()
        is_handling_alert = False

    btn_close = ctk.CTkButton(
        main_frame, text="Ясно", fg_color="#FFFFFF", text_color="#FF0000", hover_color="#E0E0E0", font=("Arial", 12, "bold"), command=close_and_release
    )
    btn_close.pack(pady=(15, 20))


def security_log_monitor_loop():
    global monitoring_active, is_handling_alert, last_system_record_id

    advapi32 = ctypes.windll.advapi32
    
    advapi32.OpenEventLogW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    advapi32.OpenEventLogW.restype = wintypes.HANDLE
    
    advapi32.CloseEventLog.argtypes = [wintypes.HANDLE]
    advapi32.CloseEventLog.restype = wintypes.BOOL

    advapi32.ReadEventLogW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD)
    ]
    advapi32.ReadEventLogW.restype = wintypes.BOOL

    hand = advapi32.OpenEventLogW(None, "Security")
    if not hand:
        print("[ОШИБКА] Не удалось открыть журнал безопасности.")
        return

    class EVENTLOGRECORD(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.DWORD),
            ("Reserved", wintypes.DWORD),
            ("RecordNumber", wintypes.DWORD),
            ("TimeGenerated", wintypes.DWORD),
            ("TimeWritten", wintypes.DWORD),
            ("EventID", wintypes.DWORD),
            ("EventType", wintypes.WORD),
            ("NumStrings", wintypes.WORD),
            ("EventCategory", wintypes.WORD),
            ("ReservedFlags", wintypes.WORD),
            ("ClosingRecordNumber", wintypes.DWORD),
            ("StringOffset", wintypes.DWORD),
            ("UserSidLength", wintypes.DWORD),
            ("UserSidOffset", wintypes.DWORD),
            ("DataLength", wintypes.DWORD),
            ("DataOffset", wintypes.DWORD),
        ]

    buffer_size = 1024 * 64
    buffer = ctypes.create_string_buffer(buffer_size)
    bytes_read = wintypes.DWORD()
    min_bytes_needed = wintypes.DWORD()

    monitoring_active = True

    print("[СИСТЕМА] Нативный Win32-мониторинг логов успешно запущен.")

    while monitoring_active:
        time.sleep(0.4)

        if is_handling_alert:
            continue

        ret = advapi32.ReadEventLogW(
            hand,
            EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ,
            0,
            ctypes.byref(buffer),
            buffer_size,
            ctypes.byref(bytes_read),
            ctypes.byref(min_bytes_needed)
        )

        if not ret or bytes_read.value == 0:
            continue

        offset = 0
        while offset < bytes_read.value:
            record = EVENTLOGRECORD.from_buffer(buffer, offset)
            real_event_id = record.EventID & 0xFFFF
            
            if real_event_id == 4657 and record.NumStrings >= 12:
                # НАДЕЖНЫЙ ЦИФРОВОЙ ФИЛЬТР: Пропускаем всё, что было записано до старта кнопки мониторинга
                if record.RecordNumber <= last_system_record_id:
                    offset += record.Length
                    continue
                
                try:
                    string_ptr = ctypes.cast(ctypes.byref(buffer, offset + record.StringOffset), ctypes.c_void_p)
                    strings = []
                    current_ptr = string_ptr.value
                    
                    for _ in range(record.NumStrings):
                        string_val = ctypes.wstring_at(current_ptr).strip()
                        strings.append(string_val)
                        current_ptr += (len(string_val) + 1) * 2

                    raw_reg_path = strings[1]
                    reg_val_name = strings[2]
                    proc_full_path = strings[11]

                    reg_hive_path = raw_reg_path.replace("\\REGISTRY\\USER\\", "HKEY_CURRENT_USER\\")
                    if "S-1-5-" in reg_hive_path:
                        parts = reg_hive_path.split("\\")
                        if len(parts) > 3:
                            reg_hive_path = "HKEY_CURRENT_USER\\" + "\\".join(parts[3:])

                    full_reg_path = reg_hive_path
                    if reg_val_name and reg_val_name != "-":
                        full_reg_path += f" \\ {reg_val_name}"

                    process_name = os.path.basename(proc_full_path) if proc_full_path else "Неизвестно"

                    if any(x in process_name.lower() for x in ["python", "excel", "explorer", "svchost", "system"]):
                        offset += record.Length
                        continue

                    if "PythonRegistryMonitorTest" in full_reg_path:
                        process_name = "reg.exe (Тест системы)"
                        if not reg_val_name or reg_val_name == "-":
                            full_reg_path += " \\ TestAction"

                    now = datetime.datetime.fromtimestamp(record.TimeGenerated).strftime("%Y-%m-%d %H:%M:%S")

                    is_handling_alert = True
                    threading.Thread(target=log_to_excel, args=(now, process_name, full_reg_path), daemon=True).start()
                    threading.Thread(target=show_alert_window, args=(now, process_name, full_reg_path), daemon=True).start()
                    break

                except Exception as e:
                    pass
            
            offset += record.Length

    advapi32.CloseEventLog(hand)

# --- Функция получения ID самой последней записи в журнале на текущий момент ---
def get_last_log_record_id():
    advapi32 = ctypes.windll.advapi32
    
    # Строго настраиваем типы данных для защиты от Access Violation
    advapi32.OpenEventLogW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    advapi32.OpenEventLogW.restype = wintypes.HANDLE
    
    advapi32.CloseEventLog.argtypes = [wintypes.HANDLE]
    advapi32.CloseEventLog.restype = wintypes.BOOL

    advapi32.ReadEventLogW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD)
    ]
    advapi32.ReadEventLogW.restype = wintypes.BOOL

    hand = advapi32.OpenEventLogW(None, "Security")
    if not hand:
        return 0
        
    class EVENTLOGRECORD(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.DWORD), 
            ("Reserved", wintypes.DWORD), 
            ("RecordNumber", wintypes.DWORD)
        ]
        
    buffer = ctypes.create_string_buffer(1024)
    bytes_read = wintypes.DWORD()
    min_bytes_needed = wintypes.DWORD()
    
    # Теперь вызов через ctypes.byref абсолютно безопасен
    ret = advapi32.ReadEventLogW(
        hand, 
        EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ, 
        0, 
        ctypes.byref(buffer), 
        1024, 
        ctypes.byref(bytes_read), 
        ctypes.byref(min_bytes_needed)
    )
    
    record_id = 0
    if ret and bytes_read.value > 0:
        record = EVENTLOGRECORD.from_buffer(buffer, 0)
        record_id = record.RecordNumber
        
    advapi32.CloseEventLog(hand)
    return record_id



def toggle_monitoring(btn, status_label):
    global monitoring_active, last_system_record_id
    if not excel_path:
        messagebox.showwarning("Внимание", "Сначала выберите файл Excel!")
        return

    if not monitoring_active:
        # Узнаем текущий последний ID лога прямо перед запуском слежки
        last_system_record_id = get_last_log_record_id()
        threading.Thread(target=security_log_monitor_loop, daemon=True).start()
        btn.configure(text="Остановить мониторинг", fg_color="#FF3333")
        status_label.configure(text="Статус: Работает", text_color="#00FF00")
    else:
        monitoring_active = False
        btn.configure(text="2. Запустить мониторинг", fg_color="#1F6AA5")
        status_label.configure(text="Статус: Отключен", text_color="gray")


def trigger_test_modification():
    if not monitoring_active:
        messagebox.showwarning("Внимание", "Сначала запустите мониторинг!")
        return
    if is_handling_alert:
        return

    def run_test():
        try:
            test_path = r"HKCU\Software\PythonRegistryMonitorTest"
            subprocess.run(
                f'reg add "{test_path}" /v TestAction /t REG_SZ /d "Proverka_Sistemy" /f',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.3)
            subprocess.run(
                f'reg delete "{test_path}" /f',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            messagebox.showerror("Ошибка теста", str(e))

    threading.Thread(target=run_test, daemon=True).start()


def create_main_gui():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Registry Guard Setup & Monitor")
    root.geometry("500x400")
    root.resizable(False, False)

    label_title = ctk.CTkLabel(root, text="Мониторинг Реестра через Аудит ОС", font=("Arial", 18, "bold"))
    label_title.pack(pady=20)

    btn_select_file = ctk.CTkButton(root, text="1. Выбрать путь для Excel", command=lambda: select_excel_path(label_file_status))
    btn_select_file.pack(pady=10)

    label_file_status = ctk.CTkLabel(root, text="Файл логов не выбран", text_color="#FF3333")
    label_file_status.pack(pady=5)

    frame_line = ctk.CTkFrame(root, height=2, width=400, fg_color="gray")
    frame_line.pack(pady=15)

    btn_toggle = ctk.CTkButton(root, text="2. Запустить мониторинг", fg_color="#1F6AA5")
    btn_toggle.configure(command=lambda: toggle_monitoring(btn_toggle, label_monitor_status))
    btn_toggle.pack(pady=10)

    label_monitor_status = ctk.CTkLabel(root, text="Статус: Отключен", text_color="gray")
    label_monitor_status.pack(pady=5)

    btn_test = ctk.CTkButton(
        root, text="🚨 ТЕСТ ИЗМЕНЕНИЯ (РЕАЛЬНЫЙ)", fg_color="#FF8C00", hover_color="#CD7A00", text_color="black", font=("Arial", 13, "bold"), command=trigger_test_modification
    )
    btn_test.pack(pady=25)

    root.mainloop()


if __name__ == "__main__":
    create_main_gui()
