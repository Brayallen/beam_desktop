import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from beam_designer import (
    BeamLoads,
    PointLoad,
    STEEL_SECTIONS,
    LUMBER_SECTIONS,
    SECTION_SOURCES,
    UniformLoad,
    analyze,
)
from design_io import SavedDesign, open_design, save_design


class BeamDesignerApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master = master
        master.title("Beam Designer")
        master.geometry("1180x820")
        master.minsize(900, 650)

        self.support = "simple"
        self.material = "steel"
        self.point_rows: list[tuple[ttk.Entry, ttk.Entry, ttk.Button]] = []
        self.uniform_rows: list[tuple[ttk.Entry, ttk.Entry, ttk.Entry, ttk.Button]] = []
        self.result = None
        self.loading_design = False
        self.limit_tracks_span = True
        self.create_file_menu()
        self.build_ui()
        self.add_point_load(5.0, 10.0)
        self.add_uniform_load(1.0, 0.0, 20.0)
        self.update_section_options()
        self.analyze()

    def create_file_menu(self):
        menu_bar = tk.Menu(self.master)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Open...", command=self.open_design_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Save...", command=self.save_design_dialog, accelerator="Ctrl+S")
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.master.configure(menu=menu_bar)
        self.master.bind("<Control-o>", lambda event: self.open_design_dialog())
        self.master.bind("<Control-s>", lambda event: self.save_design_dialog())

    def build_ui(self):
        self.pack(fill="both", expand=True)

        header = tk.Frame(self, bg="#1f2f47", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Beam Designer",
            bg="#1f2f47",
            fg="white",
            font=("TkDefaultFont", 18, "bold"),
            padx=20,
        ).pack(side="left")
        tk.Label(
            header,
            text="Imperial units  |  Preliminary design",
            bg="#1f2f47",
            fg="#dce5f2",
            font=("TkDefaultFont", 11),
            padx=20,
        ).pack(side="right")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=12)

        left_container = ttk.Frame(body, width=350)
        body.add(left_container, weight=0)
        left = ttk.Frame(left_container)
        left.pack(fill="both", expand=True)

        canvas = tk.Canvas(left, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        controls = ttk.Frame(canvas)
        controls.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=controls, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(controls, text="Beam inputs", font=("TkDefaultFont", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        row = 1
        self.support_var = tk.StringVar(value="simple")
        ttk.Label(controls, text="SUPPORT").grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        support_frame = ttk.Frame(controls)
        support_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        for index, (text, value) in enumerate(
            (("Simply supported", "simple"), ("Cantilever", "cantilever"))
        ):
            ttk.Radiobutton(
                support_frame,
                text=text,
                value=value,
                variable=self.support_var,
                command=self.analyze,
            ).grid(row=0, column=index, sticky="ew", padx=(0, 6))
        row += 1

        ttk.Label(controls, text="Span (ft)").grid(row=row, column=0, sticky="w")
        self.span_entry = ttk.Entry(controls, width=12)
        self.span_entry.insert(0, "20")
        self.span_entry.grid(row=row, column=1, sticky="e", pady=(0, 12))
        self.span_entry.bind("<KeyRelease>", lambda event: self.on_span_changed())
        row += 1
        ttk.Label(controls, text="Deflection limit (in)").grid(row=row, column=0, sticky="w")
        self.deflection_limit_entry = ttk.Entry(controls, width=12)
        self.deflection_limit_entry.insert(0, str(20.0 * 12.0 / 360.0))
        self.deflection_limit_entry.grid(row=row, column=1, sticky="e", pady=(0, 12))
        self.deflection_limit_entry.bind("<KeyRelease>", lambda event: self.on_limit_changed())
        row += 1

        ttk.Separator(controls).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1
        ttk.Label(controls, text="POINT LOADS").grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        self.point_frame = ttk.Frame(controls)
        self.point_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        row += 1
        ttk.Button(self.point_frame, text="+ Add point load", command=lambda: self.add_point_load()).grid(
            row=100, column=0, columnspan=3, sticky="ew", pady=(8, 12)
        )

        ttk.Separator(controls).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1
        ttk.Label(controls, text="UNIFORM LOADS").grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        self.uniform_frame = ttk.Frame(controls)
        self.uniform_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        row += 1
        ttk.Button(
            self.uniform_frame,
            text="+ Add uniform load",
            command=lambda: self.add_uniform_load(),
        ).grid(row=100, column=0, columnspan=4, sticky="ew", pady=(8, 12))

        ttk.Separator(controls).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1
        ttk.Label(controls, text="SECTION").grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        self.material_var = tk.StringVar(value="steel")
        material_frame = ttk.Frame(controls)
        material_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Radiobutton(
            material_frame, text="Steel", value="steel", variable=self.material_var,
            command=self.update_section_options
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            material_frame, text="Lumber", value="lumber", variable=self.material_var,
            command=self.update_section_options
        ).grid(row=0, column=1, sticky="w")
        row += 1
        ttk.Label(controls, text="Shape / size").grid(row=row, column=0, sticky="w")
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(
            controls, textvariable=self.section_var, state="readonly", width=22
        )
        self.section_combo.grid(row=row, column=1, sticky="e", pady=(0, 8))
        self.section_combo.bind("<<ComboboxSelected>>", lambda event: self.analyze())
        row += 1
        ttk.Label(controls, text="Orientation").grid(row=row, column=0, sticky="w")
        self.orientation_var = tk.StringVar(value="edgewise")
        self.orientation_combo = ttk.Combobox(
            controls,
            textvariable=self.orientation_var,
            values=("edgewise", "flatwise"),
            state="readonly",
            width=22,
        )
        self.orientation_combo.grid(row=row, column=1, sticky="e", pady=(0, 12))
        self.orientation_combo.bind("<<ComboboxSelected>>", lambda event: self.analyze())
        row += 1

        ttk.Button(controls, text="Analyze beam", command=self.analyze).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(4, 6)
        )
        row += 1
        self.error_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=self.error_var, foreground="#bd2c2c", wraplength=300).grid(
            row=row, column=0, columnspan=2, sticky="w"
        )

        right = ttk.Frame(body)
        body.add(right, weight=1)
        summary = ttk.Frame(right)
        summary.pack(fill="x", pady=(0, 10))
        self.summary_labels = {}
        for index, title in enumerate(
            ("Overall status", "Maximum moment", "Maximum deflection", "Maximum shear")
        ):
            card = ttk.Labelframe(summary, text=title)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 8))
            value = ttk.Label(card, text="—", font=("TkDefaultFont", 15, "bold"))
            value.pack(pady=(8, 2), padx=8)
            sub = ttk.Label(card, text="Run an analysis", foreground="#667085")
            sub.pack(pady=(0, 8), padx=8)
            self.summary_labels[title] = (value, sub)
        for index in range(4):
            summary.grid_columnconfigure(index, weight=1)

        self.beam_canvas = tk.Canvas(right, height=170, bg="#ffffff", highlightthickness=1,
                                     highlightbackground="#dfe5ec")
        self.beam_canvas.pack(fill="x", pady=(0, 10))

        diagrams = ttk.Frame(right)
        diagrams.pack(fill="both", expand=True)
        self.shear_canvas = tk.Canvas(diagrams, bg="#ffffff", highlightthickness=1,
                                      highlightbackground="#dfe5ec")
        self.moment_canvas = tk.Canvas(diagrams, bg="#ffffff", highlightthickness=1,
                                       highlightbackground="#dfe5ec")
        self.deflection_canvas = tk.Canvas(diagrams, bg="#ffffff", highlightthickness=1,
                                           highlightbackground="#dfe5ec")
        for index, canvas in enumerate((self.shear_canvas, self.moment_canvas, self.deflection_canvas)):
            canvas.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            diagrams.grid_columnconfigure(index, weight=1)

        detail = ttk.LabelFrame(right, text="Strength and stiffness summary")
        detail.pack(fill="x", pady=(10, 0))
        self.check_summary = ttk.Label(detail, text="Run an analysis to show results.",
                                       justify="left", wraplength=760)
        self.check_summary.pack(fill="x", padx=10, pady=8)

        source = ttk.Label(
            right,
            text="Section sources: " + SECTION_SOURCES["steel"],
            foreground="#667085",
            wraplength=760,
        )
        source.pack(fill="x", pady=(8, 0))
        self.source_label = source

        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

    def add_point_load(self, value: float | None = None, position: float | None = None):
        row = len(self.point_rows)
        value_entry = ttk.Entry(self.point_frame, width=8)
        position_entry = ttk.Entry(self.point_frame, width=8)
        value_entry.insert(0, str(5.0 if value is None else value))
        position_entry.insert(0, str(10.0 if position is None else position))
        value_entry.grid(row=row, column=0, padx=(0, 4), pady=3)
        position_entry.grid(row=row, column=1, padx=(0, 4), pady=3)
        remove = ttk.Button(self.point_frame, text="×", width=3)
        remove.grid(row=row, column=2, pady=3)
        remove.configure(command=lambda: self.remove_point_load(remove))
        value_entry.bind("<KeyRelease>", lambda event: self.analyze())
        position_entry.bind("<KeyRelease>", lambda event: self.analyze())
        self.point_rows.append((value_entry, position_entry, remove))
        self.relayout_load_buttons()

    def add_uniform_load(self, value: float | None = None, start: float | None = None,
                          end: float | None = None):
        try:
            span = float(self.span_entry.get())
        except ValueError:
            span = 20.0
        row = len(self.uniform_rows)
        value_entry = ttk.Entry(self.uniform_frame, width=7)
        start_entry = ttk.Entry(self.uniform_frame, width=7)
        end_entry = ttk.Entry(self.uniform_frame, width=7)
        value_entry.insert(0, str(1.0 if value is None else value))
        start_entry.insert(0, str(0.0 if start is None else start))
        end_entry.insert(0, str(span if end is None else end))
        value_entry.grid(row=row, column=0, padx=(0, 3), pady=3)
        start_entry.grid(row=row, column=1, padx=(0, 3), pady=3)
        end_entry.grid(row=row, column=2, padx=(0, 3), pady=3)
        remove = ttk.Button(self.uniform_frame, text="×", width=3)
        remove.grid(row=row, column=3, pady=3)
        remove.configure(command=lambda: self.remove_uniform_load(remove))
        for entry in (value_entry, start_entry, end_entry):
            entry.bind("<KeyRelease>", lambda event: self.analyze())
        self.uniform_rows.append((value_entry, start_entry, end_entry, remove))
        self.relayout_load_buttons()

    def relayout_load_buttons(self):
        point_button = self.point_frame.grid_slaves(row=100, column=0)
        if point_button:
            point_button[0].grid(row=100, column=0, columnspan=3, sticky="ew", pady=(8, 12))
        uniform_button = self.uniform_frame.grid_slaves(row=100, column=0)
        if uniform_button:
            uniform_button[0].grid(row=100, column=0, columnspan=4, sticky="ew", pady=(8, 12))

    def remove_point_load(self, button: ttk.Button):
        for index, (_, _, remove) in enumerate(self.point_rows):
            if remove is button:
                for widget in self.point_rows[index]:
                    widget.destroy()
                del self.point_rows[index]
                break
        for row, (value_entry, position_entry, remove) in enumerate(self.point_rows):
            value_entry.grid(row=row, column=0)
            position_entry.grid(row=row, column=1)
            remove.grid(row=row, column=2)
        self.relayout_load_buttons()
        self.analyze()

    def remove_uniform_load(self, button: ttk.Button):
        for index, (_, _, _, remove) in enumerate(self.uniform_rows):
            if remove is button:
                for widget in self.uniform_rows[index]:
                    widget.destroy()
                del self.uniform_rows[index]
                break
        for row, (value_entry, start_entry, end_entry, remove) in enumerate(self.uniform_rows):
            value_entry.grid(row=row, column=0)
            start_entry.grid(row=row, column=1)
            end_entry.grid(row=row, column=2)
            remove.grid(row=row, column=3)
        self.relayout_load_buttons()
        self.analyze()

    def update_section_options(self):
        self.set_section_options(run_analysis=True)

    def set_section_options(self, run_analysis: bool):
        self.material = self.material_var.get()
        if self.material == "steel":
            values = [section.designation for section in STEEL_SECTIONS]
            self.section_var.set("W12x26")
            self.orientation_combo.configure(state="disabled")
            self.source_label.configure(text="Section source: " + SECTION_SOURCES["steel"])
        else:
            values = [
                f"{section.designation} - {section.species} {section.grade}"
                for section in LUMBER_SECTIONS
            ]
            self.section_var.set(values[0])
            self.orientation_combo.configure(state="readonly")
            self.source_label.configure(text="Section source: " + SECTION_SOURCES["lumber"])
        self.section_combo.configure(values=values)
        if run_analysis:
            self.analyze()

    def on_span_changed(self):
        if self.limit_tracks_span:
            try:
                span = float(self.span_entry.get())
                if span > 0:
                    self.deflection_limit_entry.delete(0, tk.END)
                    self.deflection_limit_entry.insert(0, str(span * 12.0 / 360.0))
            except ValueError:
                pass
        self.analyze()

    def on_limit_changed(self):
        self.limit_tracks_span = False
        self.analyze()

    def read_loads(self) -> BeamLoads:
        point = []
        for value_entry, position_entry, _ in self.point_rows:
            point.append(PointLoad(float(value_entry.get()), float(position_entry.get())))
        uniform = []
        for value_entry, start_entry, end_entry, _ in self.uniform_rows:
            uniform.append(
                UniformLoad(float(value_entry.get()), float(start_entry.get()), float(end_entry.get()))
            )
        return BeamLoads(tuple(point), tuple(uniform))

    def get_selected_section(self):
        if self.material == "steel":
            for section in STEEL_SECTIONS:
                if section.designation == self.section_var.get():
                    return section
            return STEEL_SECTIONS[0]

        designation = self.section_var.get().split(" - ", 1)[0]
        for section in LUMBER_SECTIONS:
            if section.designation == designation:
                return section
        return LUMBER_SECTIONS[0]

    def analyze(self):
        if self.loading_design:
            return
        try:
            span = float(self.span_entry.get())
            loads = self.read_loads()
            section = self.get_selected_section()
            support = self.support_var.get()
            orientation = self.orientation_var.get()
            deflection_limit = float(self.deflection_limit_entry.get())
            self.result = analyze(
                support,
                span,
                loads,
                section,
                orientation,
                deflection_limit_in=deflection_limit,
            )
            self.error_var.set("")
        except ValueError as error:
            self.error_var.set(str(error))
            return

        r = self.result
        value, sub = self.summary_labels["Overall status"]
        value.configure(
            text="PASS" if r["overall_pass"] else "FAIL",
            foreground="#18864b" if r["overall_pass"] else "#bd2c2c",
        )
        sub.configure(
            text=("Bending pass | Deflection pass" if r["overall_pass"]
                  else ("Bending " + ("pass" if r["bending_pass"] else "fail") +
                        " | Deflection " + ("pass" if r["deflection_pass"] else "fail")))
        )

        value, sub = self.summary_labels["Maximum moment"]
        value.configure(text=f"{abs(r['max_moment']):.2f} kip-ft")
        sub.configure(text=f"at {r['moment_location']:.2f} ft")
        value, sub = self.summary_labels["Maximum deflection"]
        value.configure(text=f"{abs(r['max_deflection']):.3f} in")
        sub.configure(text=f"at {r['deflection_location']:.2f} ft")
        value, sub = self.summary_labels["Maximum shear"]
        value.configure(text=f"{abs(r['max_shear']):.2f} kip")
        sub.configure(text=f"at {r['shear_location']:.2f} ft")

        reaction = r["reaction"]
        if r["support"] == "simple":
            reaction_text = f"Reactions: RA {reaction['RA']:.2f} kip, RB {reaction['RB']:.2f} kip"
        else:
            reaction_text = (
                f"Reactions: RA {reaction['RA']:.2f} kip, "
                f"fixed-end moment {abs(reaction['MA']):.2f} kip-ft"
            )
        orientation_text = f" ({r['orientation']})" if self.material == "lumber" else ""
        section_name = r["section"].designation
        self.check_summary.configure(
            text=(
                f"Section: {section_name}{orientation_text}\n"
                f"Bending: {r['bending_stress']:.2f} ksi stress / "
                f"{r['allowable']:.2f} ksi allowable "
                f"({r['bending_ratio'] * 100:.1f}%) - "
                f"{'PASS' if r['bending_pass'] else 'FAIL'}\n"
                f"Deflection: {abs(r['max_deflection']):.3f} in / "
                f"{r['deflection_limit']:.3f} in limit "
                f"({r['deflection_ratio'] * 100:.1f}%) - "
                f"{'PASS' if r['deflection_pass'] else 'FAIL'}\n"
                f"{reaction_text}"
            )
        )
        self.draw_all()

    def current_design(self) -> SavedDesign:
        span = float(self.span_entry.get())
        loads = self.read_loads()
        material = self.material_var.get()
        section = self.get_selected_section()
        return SavedDesign.from_json_value(
            {
                "support": self.support_var.get(),
                "span_ft": span,
                "material": material,
                "section": section.designation,
                "lumber_orientation": self.orientation_var.get() if material == "lumber" else None,
                "deflection_limit_in": float(self.deflection_limit_entry.get()),
                "point_loads": [
                    {"magnitude_kip": load.value, "position_ft": load.position}
                    for load in loads.point
                ],
                "uniform_loads": [
                    {
                        "magnitude_kip_per_ft": load.value,
                        "start_ft": load.start,
                        "end_ft": load.end,
                    }
                    for load in loads.uniform
                ],
            }
        )

    def save_design_dialog(self):
        path = filedialog.asksaveasfilename(
            title="Save beam design",
            defaultextension=".json",
            filetypes=(("Beam design JSON", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            design = self.current_design()
            save_design(path, design)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not save design", str(error), parent=self.master)
            return
        messagebox.showinfo("Design saved", f"Saved beam design to:\n{path}", parent=self.master)

    def open_design_dialog(self):
        path = filedialog.askopenfilename(
            title="Open beam design",
            filetypes=(("Beam design JSON", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            design = open_design(path)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Could not open design",
                f"The selected file is invalid or incompatible:\n{error}",
                parent=self.master,
            )
            return
        self.restore_design(design)

    def restore_design(self, design: SavedDesign):
        self.loading_design = True
        try:
            self.support_var.set(design.support)
            self.material_var.set(design.material)
            self.span_entry.delete(0, tk.END)
            self.span_entry.insert(0, str(design.span_ft))
            self.deflection_limit_entry.delete(0, tk.END)
            self.deflection_limit_entry.insert(0, str(design.deflection_limit_in))
            self.limit_tracks_span = abs(
                design.deflection_limit_in - design.span_ft * 12.0 / 360.0
            ) < 1e-12

            self.set_section_options(run_analysis=False)
            if design.material == "lumber":
                section_value = next(
                    value
                    for value in self.section_combo["values"]
                    if value.split(" - ", 1)[0] == design.section
                )
                self.orientation_var.set(design.lumber_orientation)
            else:
                section_value = design.section
            self.section_var.set(section_value)

            for row in self.point_rows:
                for widget in row:
                    widget.destroy()
            self.point_rows.clear()
            for load in design.point_loads:
                self.add_point_load(load.value, load.position)

            for row in self.uniform_rows:
                for widget in row:
                    widget.destroy()
            self.uniform_rows.clear()
            for load in design.uniform_loads:
                self.add_uniform_load(load.value, load.start, load.end)
        finally:
            self.loading_design = False
        self.analyze()

    def clear_canvas(self, canvas: tk.Canvas):
        canvas.delete("all")

    def draw_line_chart(self, canvas: tk.Canvas, x_values, y_values, title: str,
                         unit: str, color: str):
        self.clear_canvas(canvas)
        width = max(canvas.winfo_width(), 250)
        height = max(canvas.winfo_height(), 140)
        left, right, top, bottom = 42, width - 12, 24, height - 24
        minimum = min(0.0, *y_values)
        maximum = max(0.0, *y_values)
        if maximum == minimum:
            maximum += 1.0
            minimum -= 1.0
        x_min, x_max = x_values[0], x_values[-1]
        x_span = x_max - x_min or 1.0

        def sx(value):
            return left + (value - x_min) / x_span * (right - left)

        def sy(value):
            return top + (maximum - value) / (maximum - minimum) * (bottom - top)

        y_zero = sy(0.0)
        canvas.create_text(5, 8, text=title, anchor="nw", font=("TkDefaultFont", 9, "bold"))
        canvas.create_line(left, y_zero, right, y_zero, fill="#9aa5b1")
        points = []
        for x, y in zip(x_values, y_values):
            points.extend((sx(x), sy(y)))
        canvas.create_line(points, fill=color, width=2)
        canvas.create_text(left, bottom + 5, text=f"{x_min:.1f}", anchor="nw", font=("TkDefaultFont", 8))
        canvas.create_text(right, bottom + 5, text=f"{x_max:.1f} ft", anchor="ne", font=("TkDefaultFont", 8))
        canvas.create_text(left + 3, top + 3, text=f"{maximum:.2f}", anchor="nw", font=("TkDefaultFont", 8),
                           fill="#667085")
        canvas.create_text(left + 3, bottom - 12, text=f"{minimum:.2f}", anchor="nw", font=("TkDefaultFont", 8),
                           fill="#667085")

    def draw_beam(self):
        canvas = self.beam_canvas
        self.clear_canvas(canvas)
        width = max(canvas.winfo_width(), 700)
        height = max(canvas.winfo_height(), 170)
        left, right, y = 70, width - 70, 72
        r = self.result

        canvas.create_text(12, 8, text="Beam with reactions and loads", anchor="nw",
                           font=("TkDefaultFont", 10, "bold"))
        canvas.create_line(left, y, right, y, fill="#26384e", width=8)
        if r["support"] == "simple":
            canvas.create_polygon(left, y, left - 18, y + 31, left + 18, y + 31, fill="#9eabb9")
            canvas.create_polygon(right, y, right - 18, y + 31, right + 18, y + 31, fill="#9eabb9")
            canvas.create_line(left - 23, y + 31, left + 23, y + 31, fill="#26384e", width=3)
            canvas.create_line(right - 23, y + 31, right + 23, y + 31, fill="#26384e", width=3)
        else:
            canvas.create_rectangle(left - 18, y - 25, left, y + 25, fill="#9eabb9", outline="")
            for offset in range(-18, 19, 9):
                canvas.create_line(left - 18, y + offset, left - 6, y + offset + 12,
                                   fill="#26384e", width=1)

        beam_length = right - left
        for load in r["loads"].point:
            px = left + load.position / r["span"] * beam_length
            canvas.create_line(px, y - 48, px, y - 8, fill="#c03b35", width=3,
                               arrow=tk.LAST)
            canvas.create_text(px, y - 55, text=f"{load.value:g} kip",
                               anchor="s", font=("TkDefaultFont", 9), fill="#c03b35")
        for load in r["loads"].uniform:
            x1 = left + load.start / r["span"] * beam_length
            x2 = left + load.end / r["span"] * beam_length
            canvas.create_rectangle(x1, y - 38, x2, y - 8, fill="#dbeafe", outline="#3b82f6")
            canvas.create_text((x1 + x2) / 2, y - 44, text=f"{load.value:g} kip/ft",
                               anchor="s", font=("TkDefaultFont", 9), fill="#344054")
        canvas.create_text((left + right) / 2, y + 58, text=f"{r['span']:.2f} ft",
                           font=("TkDefaultFont", 9), fill="#667085")

    def draw_all(self):
        r = self.result
        self.draw_beam()
        self.draw_line_chart(self.shear_canvas, r["x"], r["shear"], "Shear (kip)", "kip", "#2563eb")
        self.draw_line_chart(self.moment_canvas, r["x"], r["moment"], "Moment (kip-ft)", "kip-ft", "#18864b")
        self.draw_line_chart(
            self.deflection_canvas,
            r["deflection_x"],
            r["deflection"],
            "Deflection (in)",
            "in",
            "#d97706",
        )


def main():
    root = tk.Tk()
    BeamDesignerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
