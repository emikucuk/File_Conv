"""Convert selected images via a local Pillow GUI (Explorer context menu)."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
OUTPUT_FOLDER_NAME = "converted"

# (key, display label, output suffix)
FORMAT_CHOICES: list[tuple[str, str, str]] = [
    ("png", "PNG", ".png"),
    ("jpeg", "JPEG", ".jpg"),
    ("webp", "WebP", ".webp"),
]
FORMAT_LABELS = [label for _, label, _ in FORMAT_CHOICES]
# key -> (suffix, pillow_format)
TARGETS: dict[str, tuple[str, str]] = {
    "png": (".png", "PNG"),
    "jpeg": (".jpg", "JPEG"),
    "webp": (".webp", "WEBP"),
}
PLACEHOLDER = "Seçin..."


def unique_path(directory: Path, name: str) -> Path:
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem, suffix = Path(name).stem, Path(name).suffix
    n = 1
    while True:
        candidate = directory / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def collect_files(args: list[str]) -> tuple[list[Path], int]:
    files: list[Path] = []
    skipped = 0
    seen: set[Path] = set()
    for arg in args:
        path = Path(arg).resolve()
        if not path.is_file():
            skipped += 1
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            skipped += 1
            continue
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
    return files, skipped


def prepare_image(image: Image.Image, pillow_format: str) -> Image.Image:
    if pillow_format == "JPEG":
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        return image.convert("RGB")

    if image.mode == "P":
        return image.convert("RGBA")
    return image


def convert_file(source: Path, destination: Path, pillow_format: str) -> None:
    """Save with size-biased settings. Lossy targets step quality down if still larger."""
    original_size = source.stat().st_size

    with Image.open(source) as image:
        image.load()
        prepared = prepare_image(image, pillow_format)

        if pillow_format == "PNG":
            # Lossless: max zlib compression (JPEG/WebP → PNG often still grows)
            prepared.save(
                destination,
                format="PNG",
                optimize=True,
                compress_level=9,
            )
            return

        qualities = (82, 76, 70, 64, 58) if pillow_format == "JPEG" else (78, 72, 66, 60, 54)
        for quality in qualities:
            if pillow_format == "JPEG":
                prepared.save(
                    destination,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )
            else:
                prepared.save(
                    destination,
                    format="WEBP",
                    quality=quality,
                    method=6,
                )
            if destination.stat().st_size <= original_size:
                break


def label_to_target(label: str) -> tuple[str, str] | None:
    """Return (suffix, pillow_format) or None if placeholder / invalid."""
    if not label or label == PLACEHOLDER:
        return None
    for key, lab, suffix in FORMAT_CHOICES:
        if lab == label:
            return TARGETS[key]
    return None


class ConvertApp(tk.Tk):
    def __init__(self, files: list[Path], skipped: int) -> None:
        super().__init__()
        self.title("Formata dönüştür")
        self.minsize(520, 360)
        self.geometry("640x480")
        self.files = files
        self.skipped = skipped
        self.row_vars: list[tk.StringVar] = []
        self.row_combos: list[ttk.Combobox] = []

        self.same_format_var = tk.BooleanVar(value=True)
        self.global_format_var = tk.StringVar(value=PLACEHOLDER)

        self._build_ui()
        self._apply_mode()
        self._refresh_ok_state()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(50, self._focus_raise)

    def _focus_raise(self) -> None:
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 8}
        top = ttk.Frame(self)
        top.pack(fill="x", **pad)

        self.same_check = ttk.Checkbutton(
            top,
            text="Hepsini aynı formata çevir",
            variable=self.same_format_var,
            command=self._on_mode_toggle,
        )
        self.same_check.pack(side="left")

        self.global_combo = ttk.Combobox(
            top,
            textvariable=self.global_format_var,
            values=[PLACEHOLDER, *FORMAT_LABELS],
            state="readonly",
            width=12,
        )
        self.global_combo.pack(side="left", padx=(12, 0))
        self.global_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_ok_state())

        hint = ttk.Label(
            self,
            text="Hedef format seçilmeden Tamam kullanılamaz.",
            foreground="#666",
        )
        hint.pack(anchor="w", padx=12)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(8, 0))
        ttk.Label(header, text="Görsel", font=("", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Hedef format", font=("", 9, "bold")).pack(side="right")

        list_wrap = ttk.Frame(self)
        list_wrap.pack(fill="both", expand=True, padx=12, pady=8)

        canvas = tk.Canvas(list_wrap, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)
        self.list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        for path in self.files:
            row = ttk.Frame(self.list_frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=path.name, anchor="w").pack(
                side="left", fill="x", expand=True, padx=(0, 8)
            )
            var = tk.StringVar(value=PLACEHOLDER)
            combo = ttk.Combobox(
                row,
                textvariable=var,
                values=[PLACEHOLDER, *FORMAT_LABELS],
                state="readonly",
                width=12,
            )
            combo.pack(side="right")
            combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_ok_state())
            self.row_vars.append(var)
            self.row_combos.append(combo)

        self.status_var = tk.StringVar(value=f"{len(self.files)} görsel")
        if self.skipped:
            self.status_var.set(
                f"{len(self.files)} görsel · {self.skipped} atlandı (desteklenmeyen)"
            )
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", padx=12)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=12, pady=12)
        ttk.Button(buttons, text="İptal", command=self.destroy).pack(side="right")
        self.ok_btn = ttk.Button(buttons, text="Tamam", command=self._on_ok)
        self.ok_btn.pack(side="right", padx=(0, 8))

    def _on_mode_toggle(self) -> None:
        self._apply_mode()
        self._refresh_ok_state()

    def _apply_mode(self) -> None:
        same = self.same_format_var.get()
        if same:
            self.global_combo.configure(state="readonly")
            for combo in self.row_combos:
                combo.configure(state="disabled")
        else:
            self.global_combo.configure(state="disabled")
            for combo in self.row_combos:
                combo.configure(state="readonly")

    def _is_valid(self) -> bool:
        if self.same_format_var.get():
            return label_to_target(self.global_format_var.get()) is not None
        return all(label_to_target(var.get()) is not None for var in self.row_vars)

    def _refresh_ok_state(self) -> None:
        state = "normal" if self._is_valid() else "disabled"
        self.ok_btn.configure(state=state)

    def _targets_for_files(self) -> list[tuple[Path, str, str]]:
        """List of (source, out_suffix, pillow_format)."""
        result: list[tuple[Path, str, str]] = []
        if self.same_format_var.get():
            target = label_to_target(self.global_format_var.get())
            assert target is not None
            suffix, pillow = target
            for path in self.files:
                result.append((path, suffix, pillow))
        else:
            for path, var in zip(self.files, self.row_vars):
                target = label_to_target(var.get())
                assert target is not None
                suffix, pillow = target
                result.append((path, suffix, pillow))
        return result

    def _on_ok(self) -> None:
        if not self._is_valid():
            messagebox.showwarning(
                "Eksik seçim",
                "Tüm gerekli format seçimlerini yapmadan devam edilemez.",
                parent=self,
            )
            return

        jobs = self._targets_for_files()
        self.ok_btn.configure(state="disabled")
        self.same_check.configure(state="disabled")
        self.global_combo.configure(state="disabled")
        for combo in self.row_combos:
            combo.configure(state="disabled")

        success = 0
        failed = 0
        total = len(jobs)
        errors: list[str] = []
        bytes_in = 0
        bytes_out = 0

        for index, (source, suffix, pillow) in enumerate(jobs, start=1):
            self.status_var.set(f"İşleniyor {index}/{total}: {source.name}")
            self.update_idletasks()
            out_dir = source.parent / OUTPUT_FOLDER_NAME
            out_name = f"{source.stem}{suffix}"
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                destination = unique_path(out_dir, out_name)
                src_size = source.stat().st_size
                convert_file(source, destination, pillow)
                dst_size = destination.stat().st_size
                bytes_in += src_size
                bytes_out += dst_size
                success += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append(f"{source.name}: {exc}")

        def _fmt(n: int) -> str:
            if n >= 1_048_576:
                return f"{n / 1_048_576:.2f} MB"
            if n >= 1024:
                return f"{n / 1024:.1f} KB"
            return f"{n} B"

        summary = (
            f"Başarılı: {success}\n"
            f"Atlanan: {self.skipped}\n"
            f"Hatalı: {failed}"
        )
        if success:
            delta = bytes_in - bytes_out
            if delta > 0:
                pct = delta / bytes_in * 100 if bytes_in else 0
                summary += (
                    f"\nBoyut: {_fmt(bytes_in)} → {_fmt(bytes_out)} "
                    f"(%{pct:.1f} küçüldü)"
                )
            elif delta < 0:
                pct = (-delta) / bytes_in * 100 if bytes_in else 0
                summary += (
                    f"\nBoyut: {_fmt(bytes_in)} → {_fmt(bytes_out)} "
                    f"(%{pct:.1f} büyüdü)"
                )
            else:
                summary += f"\nBoyut: {_fmt(bytes_in)} (değişmedi)"
        if errors:
            summary += "\n\n" + "\n".join(errors[:8])
            if len(errors) > 8:
                summary += f"\n… ve {len(errors) - 8} hata daha"

        self.status_var.set(f"Bitti · başarılı {success} · hatalı {failed}")
        if failed:
            messagebox.showwarning("Dönüştürme tamamlandı", summary, parent=self)
        else:
            messagebox.showinfo("Dönüştürme tamamlandı", summary, parent=self)
        self.destroy()


def main() -> int:
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Formata dönüştür",
            "Dosya seçilmedi.\nExplorer'da görsel(ler) seçip sağ tık → Formata dönüştür kullanın.",
        )
        root.destroy()
        return 1

    files, skipped = collect_files(sys.argv[1:])
    if not files:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Formata dönüştür",
            "İşlenecek geçerli görsel bulunamadı.\nDesteklenen: PNG, JPEG, WebP",
        )
        root.destroy()
        return 1

    app = ConvertApp(files, skipped)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
