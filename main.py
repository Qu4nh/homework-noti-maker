import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
from datetime import datetime
from datetime import timedelta

def read_schedule(file_name):
    schedule = {}
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, file_name)
    if not os.path.exists(file_path):
        messagebox.showerror("Lỗi", f"File {file_name} không tồn tại.")
        return schedule
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if '=' in line:
                day, subjects = line.strip().split('=')
                subjects = subjects.strip('{}').split('},{')
                morning_subjects = [subject.strip() for subject in subjects[0].split(',')]
                afternoon_subjects = [subject.strip() for subject in subjects[1].split(',')] if len(subjects) > 1 else []
                schedule[day.lower()] = {
                    'morning': morning_subjects,
                    'afternoon': afternoon_subjects
                }
    return schedule

class HomeworkApp:
    def center_window(self, width, height):
        # Lấy kích thước màn hình
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Tính toán vị trí để căn giữa
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Đặt vị trí cho cửa sổ
        self.master.geometry(f"{width}x{height}+{x}+{y}")
    
    def __init__(self, master):
        self.master = master
        master.title("Thông báo bài tập (Qu4nh)")
        
        width = 800
        height = 600
        master.geometry(f"{width}x{height}")

        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.center_window(width, height)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel) 

        self.schedule = read_schedule('TKB.txt')

        self.day_var = tk.StringVar()
        self.date_var = tk.StringVar()

        self.watermark_label = tk.Label(master, text="Qu4nh", font=('Arial', 10, 'italic'), fg='gray')
        self.watermark_label.pack(side='bottom', anchor='se', padx=10, pady=10)

        days_frame = tk.Frame(self.scrollable_frame)
        days_frame.pack(pady=5)

        days = ['thuhai', 'thuba', 'thutu', 'thunam', 'thusau', 'thubay']
        day_labels = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy']
        for day, label in zip(days, day_labels):
            button = tk.Button(days_frame, text=label, command=lambda d=day: self.set_day(d))
            button.pack(side=tk.LEFT, padx=5)

        self.date_entry = tk.Entry(self.scrollable_frame, textvariable=self.date_var, state='readonly')
        self.date_entry.pack(pady=5)

        load_button = tk.Button(self.scrollable_frame, text="Tải Lịch", command=self.load_schedule)
        load_button.pack(pady=10)

        self.tasks_frame = tk.Frame(self.scrollable_frame)
        self.tasks_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        note_frame = tk.Frame(self.scrollable_frame)
        note_frame.pack(pady=5, anchor='w') 

        note_label = tk.Label(note_frame, text="Ghi chú:", font=('Arial', 12, 'bold'))
        note_label.grid(row=0, column=0, sticky='w')  

        self.note_entry = tk.Entry(note_frame, width=70)
        self.note_entry.grid(row=0, column=1, padx=10)  

        self.note_entry.bind("<KeyRelease>", lambda event: self.update_announcement())


        result_frame = tk.Frame(self.scrollable_frame) 
        result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        result_label = tk.Label(result_frame, text="Thông Báo Bài Tập:", font=('Arial', 12, 'bold'))
        result_label.grid(row=0, column=0, sticky='w')

        
        copy_button = tk.Button(result_frame, text="Copy", command=self.copy_to_clipboard)
        copy_button.grid(row=0, column=1, sticky='e')

        self.result_text = tk.Text(result_frame, height=15, width=90)
        self.result_text.grid(row=1, column=0, columnspan=2, pady=5)

        self.homework_entries = {}

        self.update_date()
        self.update_announcement()
        self.displayed_morning_subjects = set()   
        self.displayed_afternoon_subjects = set()  
        self.note_var = tk.StringVar()

    def on_mouse_wheel(self, event):
        if event.delta > 0:  
            self.canvas.yview_scroll(-1, "units")
        else:  
            self.canvas.yview_scroll(1, "units")

    def copy_to_clipboard(self):
        
        result_text = self.result_text.get(1.0, tk.END).strip()  
        self.master.clipboard_clear()  
        self.master.clipboard_append(result_text)  
        messagebox.showinfo("Sao chép", "Nội dung đã được sao chép vào clipboard!")

    def update_date(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        self.date_var.set(tomorrow.strftime("%d/%m"))

    def set_day(self, day):
        self.day_var.set(day)
        self.load_schedule()

    def load_schedule(self):
        day = self.day_var.get().strip().lower()
        date = self.date_var.get().strip()

        if day not in self.schedule:
            messagebox.showerror("Lỗi", "Ngày không có trong thời khóa biểu.")
            return

        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        self.displayed_morning_subjects.clear()
        self.displayed_afternoon_subjects.clear()

        schedule_day = self.schedule[day]
        row = 0

        # Xử lý môn học buổi sáng
        morning_subjects = schedule_day['morning']
        if morning_subjects:
            morning_label = tk.Label(self.tasks_frame, text="Sáng:", font=('Arial', 12, 'bold'))
            morning_label.grid(row=row, column=0, sticky='w', pady=5)
            row += 1
            for i, subject in enumerate(morning_subjects):
                if subject not in self.displayed_morning_subjects:
                    self.add_subject_frame(subject, 'morning', row, i)
                    row += 1
                    self.displayed_morning_subjects.add(subject)

        # Xử lý môn học buổi chiều
        afternoon_subjects = schedule_day['afternoon']
        if afternoon_subjects:
            afternoon_label = tk.Label(self.tasks_frame, text="Chiều:", font=('Arial', 12, 'bold'))
            afternoon_label.grid(row=row, column=0, sticky='w', pady=5)
            row += 1
            for i, subject in enumerate(afternoon_subjects):
                if subject not in self.displayed_afternoon_subjects:
                    self.add_subject_frame(subject, 'afternoon', row, i)
                    row += 1
                    self.displayed_afternoon_subjects.add(subject)

    def add_subject_frame(self, subject, period, row, index):
        frame = tk.Frame(self.tasks_frame)
        frame.grid(row=row, column=0, sticky='w', padx=40, pady=5)

        subject_label = tk.Label(frame, text=f"{subject}", width=15, anchor='w')
        subject_label.pack(side=tk.LEFT)

        tasks_container = tk.Frame(self.tasks_frame)
        tasks_container.grid(row=row, column=0, sticky='w', padx=100, pady=2)

        subject_key = f"{subject}_{period}_{index}"

        self.homework_entries[subject_key] = {
            'tasks_container': tasks_container,
            'entries': []
        }

        self.create_task_entry(subject_key, period)



    def create_task_entry(self, subject_key, period):
        entry_info = self.homework_entries[subject_key]
        container = entry_info['tasks_container']

        row = len(entry_info['entries'])
        entry = tk.Entry(container, width=50)
        entry.grid(row=row, column=0, pady=2)
        entry_info['entries'].append(entry)

        if row > 0:
            remove_button = tk.Button(container, text="X", command=lambda e=entry: self.remove_task_entry(subject_key, e))
            remove_button.grid(row=row, column=1, padx=5)

        if row == 0:
            add_button = tk.Button(container, text="+", command=lambda p=period: self.create_task_entry(subject_key, p))
            add_button.grid(row=row, column=1, padx=5)

        entry.bind("<KeyRelease>", lambda event: self.update_announcement())


    def remove_task_entry(self, subject_key, entry):
        entry_info = self.homework_entries[subject_key]
        
        _, period, _ = subject_key.split('_')

        entry_index = entry_info['entries'].index(entry)  
        entry_info['entries'].pop(entry_index)  

        entry.grid_forget()
        entry.destroy()

        for widget in entry_info['tasks_container'].grid_slaves():
            widget.grid_forget()

        for idx, task_entry in enumerate(entry_info['entries']):
            task_entry.grid(row=idx, column=0, pady=2)
            if idx > 0:
                remove_button = tk.Button(entry_info['tasks_container'], text="X",
                                        command=lambda e=task_entry: self.remove_task_entry(subject_key, e))
                remove_button.grid(row=idx, column=1, padx=5)
            elif idx == 0:
                add_button = tk.Button(entry_info['tasks_container'], text="+",
                                    command=lambda: self.create_task_entry(subject_key, period))
                add_button.grid(row=idx, column=1, padx=5)

        self.update_announcement()




    def update_announcement(self):
        date = self.date_var.get().strip()
        day = self.day_var.get().strip().lower()

        if not day or day not in self.schedule:
            return

        day_vietnamese = {
            'thuhai': 'thứ Hai',
            'thuba': 'thứ Ba',
            'thutu': 'thứ Tư',
            'thunam': 'thứ Năm',
            'thusau': 'thứ Sáu',
            'thubay': 'thứ Bảy'
        }.get(day, day)

        announcement = f"Thông báo bài tập {day_vietnamese} ({date}):\n\n"

        # Xử lý môn học buổi sáng
        if 'morning' in self.schedule.get(day.lower(), {}):
            morning_subjects = self.schedule[day.lower()]['morning']
            if morning_subjects:
                announcement += "Sáng: " + ", ".join(morning_subjects) + "\n"
                for i, subject in enumerate(morning_subjects):
                    subject_key = f"{subject}_morning_{i}"
                    if subject_key in self.homework_entries:
                        tasks = [entry.get().strip() for entry in self.homework_entries[subject_key]['entries'] if entry.get().strip()]
                        if tasks:
                            announcement += f"- {subject}:\n" + "\n".join(f"   + {task}" for task in tasks) + "\n"

        # Xử lý môn học buổi chiều
        if 'afternoon' in self.schedule.get(day.lower(), {}):
            afternoon_subjects = self.schedule[day.lower()]['afternoon']
            if afternoon_subjects:
                announcement += "Chiều: " + ", ".join(afternoon_subjects) + "\n"
                for i, subject in enumerate(afternoon_subjects):
                    subject_key = f"{subject}_afternoon_{i}"
                    if subject_key in self.homework_entries:
                        tasks = [entry.get().strip() for entry in self.homework_entries[subject_key]['entries'] if entry.get().strip()]
                        if tasks:
                            announcement += f"- {subject}:\n" + "\n".join(f"   + {task}" for task in tasks) + "\n"

        # Lấy nội dung từ ô nhập ghi chú
        note = self.note_entry.get().strip()
        if note:
            announcement += f"Note: {note}\n"

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, announcement)


if __name__ == "__main__":
    root = tk.Tk()
    app = HomeworkApp(root)
    root.mainloop()
