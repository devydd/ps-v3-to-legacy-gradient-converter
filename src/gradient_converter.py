import pathlib
import re
import tkinter
import tkinter.messagebox
import tkinter.scrolledtext

import windnd
from psd_tools import PSDImage


def get_path_with_suffix_and_counter(file, suffix, create_numbered_files=True):
    extension = file.suffix
    output_file = file.with_name(f"{file.name[:-len(extension)]}-{suffix}{extension}")
    if not output_file.exists():
        return output_file

    if not create_numbered_files:
        raise FileExistsError(f"File {output_file} already exists and {create_numbered_files=}.")

    duplicate_numer = 1
    while True:
        output_file = file.with_name(f"{file.name[:-len(extension)]}-{suffix} ({duplicate_numer}){extension}")
        # output_file = filename.with_suffix(f"-{suffix}")
        if not output_file.exists():
            return output_file
        duplicate_numer += 1


class App:
    def __init__(self, root):
        self.root = root
        self.source_file = None
        self.source_settings = None
        self.at_least_one_converted = False
        root.minsize(800, 800)
        root.title("Gradient converter v3 to legacy, v2022_1")
        # root.iconbitmap('a')

        lbl_source = tkinter.Label(text="Files to convert\n[drag&drop here]", height=10, bg='#ffd700',
                                   font=("Courier", 30))
        windnd.hook_dropfiles(lbl_source, func=self.convert_files, force_unicode=True)
        lbl_source.pack(fill=tkinter.X)

        self.skip_if_exists = tkinter.BooleanVar(value=True)
        chk = tkinter.Checkbutton(root, text="Skip if the converted file already exists.", variable=self.skip_if_exists,
                                  justify=tkinter.LEFT)
        chk.pack(anchor=tkinter.W, expand=True)

        self.force_convert_all_gradient_styles = tkinter.BooleanVar()
        chk = tkinter.Checkbutton(root,
                                  text="Force convert Linear and Perceptual gradient methods to legacy (changes appearance!).",
                                  variable=self.force_convert_all_gradient_styles, justify=tkinter.LEFT)
        chk.pack(anchor=tkinter.W, expand=True)

        self.T = T = tkinter.scrolledtext.ScrolledText(root, bg="#002b36", fg="#839496", height=30,
                                                       font=("Courier", 8),
                                                       state="disabled", padx=10, pady=10)
        T.pack(fill=tkinter.BOTH, expand=True)
        T.tag_configure("base03", foreground="#002b36")
        T.tag_configure("base02", foreground="#073642")
        T.tag_configure("base01", foreground="#586e75")
        T.tag_configure("base00", foreground="#657b83")
        T.tag_configure("base0", foreground="#839496")
        T.tag_configure("base1", foreground="#93a1a1")
        T.tag_configure("base2", foreground="#eee8d5")
        T.tag_configure("base3", foreground="#fdf6e3")
        T.tag_configure("yellow", foreground="#b58900")
        T.tag_configure("orange", foreground="#cb4b16")
        T.tag_configure("red", foreground="#dc322f")
        T.tag_configure("magenta", foreground="#d33682")
        T.tag_configure("violet", foreground="#6c71c4")
        T.tag_configure("blue", foreground="#268bd2")
        T.tag_configure("cyan", foreground="#2aa198")
        T.tag_configure("green", foreground="#859900")

        self.log_line("[t:green]Waiting for files to convert (drag&drop on the field above)[/t]")

    def convert_gradient_maps(self, container, group_path=""):
        for layer in container:
            if layer.kind == 'group':
                self.convert_gradient_maps(layer, f"{group_path}{layer.name}/")
            if layer.kind == 'gradientmap' and layer._data.version == 3:
                layer_path = group_path + layer.name
                if not self.force_convert_all_gradient_styles.get() and layer._data.method != b'Gcls':
                    raise ValueError(f"Non-classic gradient layer \"{layer_path}\".")
                self.log_line(f"      - \"{layer_path}\": [t:green]done[/t]")
                layer._data.version = 1
                self.at_least_one_converted = True

    def convert_psd_file(self, input_file, output_file):
        self.log_line(f"   > [t:base3]Loading[/t] input PSD file from \"{input_file}\"... ", end='')
        psd2019saved_in_2022 = PSDImage.open(input_file)
        self.log_line("[t:green]done[/t].")

        try:
            self.log_line("   > [t:base3]Converting[/t] gradient map from \"Classic\" v3 to legacy v1 descriptor...")
            self.at_least_one_converted = False
            self.convert_gradient_maps(psd2019saved_in_2022)
            if not self.at_least_one_converted:
                self.log_line(f"   # [t:yellow]Skipping,[/t] no new-style gradients found.")
                return
            self.log_line(f"   > [t:base3]Saving[/t] converted PSD file at \"{output_file}\"... ", end='')
            psd2019saved_in_2022.save(output_file)
            self.log_line("[t:green]done[/t].")
        except ValueError as e:
            self.log_line(f"      [t:red]Error! {e}[/t] Skipping this file.")

    def convert_single_file(self, path):
        try:
            self.convert_psd_file(
                path,
                get_path_with_suffix_and_counter(path, "fixed_gradients",
                                                 create_numbered_files=not self.skip_if_exists.get())
            )
        except FileExistsError as e:
            self.log_line(f"   > [t:yellow]Skipped. Target file already exists.[/t]")

    def convert_files(self, files):
        self.T.configure(state='normal')
        self.T.delete('1.0', tkinter.END)

        n_files = len(files)
        self.log_line(f"Drag&dropped {n_files} file(s). Converting...")
        for i, f in enumerate(files, start=1):
            self.log_line(f"[t:base3][{i}/{n_files}][/t] Converting file \"{f}\".")
            self.convert_single_file(pathlib.Path(f))
            self.log_line()
        self.log_line(f"\n[t:green]========= DONE =========[/t]")

    def log_line(self, txt="", end="\n"):
        parts = re.split(r"\[t:([^]]+)]|\[/t]", txt + end)
        i = 0
        self.T.configure(state='normal')

        prev_tag = ''
        while i < len(parts):
            self.T.insert(tkinter.END, parts[i], prev_tag)
            i += 1
            if i >= len(parts):
                break
            tag = parts[i]
            prev_tag = tag or ''
            i += 1

        self.T.configure(state='disabled')
        self.T.see(tkinter.END)
        self.T.update()


def main():
    root = tkinter.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
