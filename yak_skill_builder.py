import os
import pathlib
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import anthropic

# ── theme ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

AGENTS_DIR = str(pathlib.Path.home() / ".claude" / "agents")


# ── file parsing ────────────────────────────────────────────────────────────
def parse_file(filepath: str) -> str:
    ext = pathlib.Path(filepath).suffix.lower()
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    if ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    # Everything else: read as text
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# ── Claude API ───────────────────────────────────────────────────────────────
SKILL_PROMPT = """\
You are creating a Claude skill file from the document content below.

A Claude skill is a markdown file saved to ~/.claude/agents/<skill-name>.md
It has YAML frontmatter followed by instructions that teach Claude specialized
knowledge or a step-by-step procedure.

Frontmatter format:
---
name: kebab-case-name
description: One or two sentences. State WHEN to use this skill and WHAT it does.
             Be specific enough that Claude immediately knows to use it when relevant.
---

Rules:
- Extract ONLY knowledge present in the document — do not invent anything.
- Organise content with clear ## headers.
- Keep instructions actionable and concise.
- The name should reflect the document's subject.
- The description must be genuinely useful as a trigger hint.

Suggested name: {name}

Document content:
---
{content}
---

Output ONLY the complete skill file content, starting with ---.
"""


def generate_skill_md(content: str, suggested_name: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = SKILL_PROMPT.format(
        name=suggested_name or "derive from content",
        content=content[:60_000],
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def extract_name_from_skill(skill_md: str) -> str:
    for line in skill_md.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return "new-skill"


# ── GUI ──────────────────────────────────────────────────────────────────────
class YakSkillBuilder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YakAI — Skill Builder")
        self.geometry("980x780")
        self.resizable(True, True)

        self._file_path: str = ""
        self._skill_md: str = ""

        self._build_ui()

    # ── layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="YakAI",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Skill Builder",
            font=ctk.CTkFont(size=28),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ctk.CTkLabel(
            header,
            text="Parse any file and teach it to Claude as a reusable skill.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray70"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # ── step 1 — API key ──
        step1 = ctk.CTkFrame(self)
        step1.grid(row=1, column=0, sticky="ew", padx=24, pady=(18, 0))
        step1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(step1, text="① Anthropic API Key", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4)
        )
        self._api_key_var = ctk.StringVar(
            value=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        api_entry = ctk.CTkEntry(
            step1,
            textvariable=self._api_key_var,
            show="•",
            placeholder_text="sk-ant-...",
            width=380,
        )
        api_entry.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(12, 4))

        show_btn = ctk.CTkButton(
            step1,
            text="Show",
            width=60,
            command=lambda: api_entry.configure(
                show="" if api_entry.cget("show") == "•" else "•"
            ),
        )
        show_btn.grid(row=0, column=2, padx=(0, 16), pady=(12, 4))

        # ── step 2 — file + name ──
        step2 = ctk.CTkFrame(self)
        step2.grid(row=2, column=0, sticky="ew", padx=24, pady=(14, 0))
        step2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(step2, text="② Source File", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4)
        )
        self._file_label = ctk.CTkLabel(
            step2,
            text="No file selected",
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        self._file_label.grid(row=0, column=1, sticky="ew", padx=8, pady=(12, 4))
        ctk.CTkButton(
            step2, text="Browse…", width=100, command=self._pick_file
        ).grid(row=0, column=2, padx=(0, 16), pady=(12, 4))

        ctk.CTkLabel(step2, text="Skill Name (optional)", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 12)
        )
        self._name_var = ctk.StringVar()
        ctk.CTkEntry(
            step2,
            textvariable=self._name_var,
            placeholder_text="auto-detected from file",
            width=300,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=(0, 12))

        # ── step 3 — save dir ──
        step3 = ctk.CTkFrame(self)
        step3.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 0))
        # We'll pack this inside step2 to keep layout tight — use a row below

        ctk.CTkLabel(step2, text="Save To", font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky="w", padx=16, pady=(0, 12)
        )
        self._save_dir_var = ctk.StringVar(value=AGENTS_DIR)
        ctk.CTkEntry(
            step2,
            textvariable=self._save_dir_var,
            width=420,
        ).grid(row=2, column=1, sticky="ew", padx=8, pady=(0, 12))
        ctk.CTkButton(
            step2,
            text="Change…",
            width=100,
            command=lambda: self._save_dir_var.set(
                filedialog.askdirectory(initialdir=self._save_dir_var.get()) or self._save_dir_var.get()
            ),
        ).grid(row=2, column=2, padx=(0, 16), pady=(0, 12))

        # ── preview area ──
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=3, column=0, sticky="nsew", padx=24, pady=(14, 0))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            preview_frame,
            text="③ Generated Skill — edit before saving",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        self._preview = ctk.CTkTextbox(
            preview_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self._preview.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._preview.insert("0.0", "# Skill preview will appear here after generation…")
        self._preview.configure(state="disabled")

        # ── bottom bar ──
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", padx=24, pady=(12, 20))
        bar.grid_columnconfigure(0, weight=1)

        self._status_var = ctk.StringVar(value="Ready.")
        ctk.CTkLabel(
            bar,
            textvariable=self._status_var,
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._progress = ctk.CTkProgressBar(bar, width=200)
        self._progress.grid(row=0, column=1, padx=(0, 12))
        self._progress.set(0)
        self._progress.grid_remove()

        self._gen_btn = ctk.CTkButton(
            bar,
            text="⚡  Generate Skill",
            width=160,
            command=self._on_generate,
            fg_color=("#2563EB", "#1D4ED8"),
            hover_color=("#1D4ED8", "#1E40AF"),
        )
        self._gen_btn.grid(row=0, column=2, padx=(0, 8))

        self._save_btn = ctk.CTkButton(
            bar,
            text="💾  Save Skill",
            width=140,
            state="disabled",
            command=self._on_save,
            fg_color=("#16A34A", "#15803D"),
            hover_color=("#15803D", "#166534"),
        )
        self._save_btn.grid(row=0, column=3)

    # ── actions ──────────────────────────────────────────────────────────────
    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Select a file to parse",
            filetypes=[
                ("All supported", "*.txt *.md *.pdf *.docx *.py *.js *.ts *.json *.yaml *.yml *.csv *.html *.xml"),
                ("Text files", "*.txt *.md"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("Code", "*.py *.js *.ts *.json *.yaml *.yml"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._file_path = path
            self._file_label.configure(
                text=pathlib.Path(path).name,
                text_color=("gray10", "gray90"),
            )
            if not self._name_var.get():
                stem = pathlib.Path(path).stem.lower().replace(" ", "-").replace("_", "-")
                self._name_var.set(stem)

    def _set_status(self, msg: str, colour: str = "gray60"):
        self._status_var.set(msg)

    def _on_generate(self):
        api_key = self._api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Missing API key", "Enter your Anthropic API key first.")
            return
        if not self._file_path:
            messagebox.showerror("No file", "Please select a file to parse.")
            return

        self._gen_btn.configure(state="disabled")
        self._save_btn.configure(state="disabled")
        self._progress.grid()
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        self._set_status("Parsing file…")

        threading.Thread(target=self._generate_worker, args=(api_key,), daemon=True).start()

    def _generate_worker(self, api_key: str):
        try:
            self.after(0, lambda: self._set_status("Parsing file…"))
            content = parse_file(self._file_path)

            self.after(0, lambda: self._set_status("Sending to Claude (claude-sonnet-4-6)…"))
            skill_md = generate_skill_md(content, self._name_var.get().strip(), api_key)
            self._skill_md = skill_md

            # Auto-fill name from generated frontmatter
            detected = extract_name_from_skill(skill_md)
            if not self._name_var.get().strip():
                self.after(0, lambda: self._name_var.set(detected))

            self.after(0, self._on_generation_done)
        except Exception as exc:
            self.after(0, lambda: self._on_generation_error(str(exc)))

    def _on_generation_done(self):
        self._progress.stop()
        self._progress.grid_remove()
        self._preview.configure(state="normal")
        self._preview.delete("0.0", "end")
        self._preview.insert("0.0", self._skill_md)
        self._gen_btn.configure(state="normal")
        self._save_btn.configure(state="normal")
        self._set_status("Skill generated — review and save when ready.", "green")

    def _on_generation_error(self, msg: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._gen_btn.configure(state="normal")
        self._set_status(f"Error: {msg}", "red")
        messagebox.showerror("Generation failed", msg)

    def _on_save(self):
        # Grab current (possibly edited) content from the textbox
        skill_md = self._preview.get("0.0", "end").strip()
        if not skill_md or skill_md.startswith("# Skill preview"):
            messagebox.showerror("Nothing to save", "Generate a skill first.")
            return

        name = self._name_var.get().strip() or extract_name_from_skill(skill_md)
        save_dir = self._save_dir_var.get().strip()

        if not save_dir:
            messagebox.showerror("No directory", "Set a save directory.")
            return

        os.makedirs(save_dir, exist_ok=True)
        dest = os.path.join(save_dir, f"{name}.md")

        if os.path.exists(dest):
            if not messagebox.askyesno(
                "Overwrite?",
                f"{name}.md already exists in that directory.\nOverwrite it?",
            ):
                return

        with open(dest, "w", encoding="utf-8") as f:
            f.write(skill_md)

        self._set_status(f"Saved → {dest}", "green")
        messagebox.showinfo(
            "Skill saved!",
            f"'{name}' has been saved to:\n{dest}\n\nClaude will use this skill in future sessions.",
        )


# ── entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = YakSkillBuilder()
    app.mainloop()
