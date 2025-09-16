# ----------------------------- Imports ---------------------------------------
import tkinter as tk  # import the base Tkinter GUI toolkit
from tkinter import ttk, filedialog, messagebox, colorchooser  # import themed widgets and dialogs
from PIL import Image  # import Pillow's Image for image I/O and processing
import numpy as np  # import NumPy for fast array operations
import matplotlib  # import Matplotlib top-level package
matplotlib.use("TkAgg")  # select TkAgg backend so Matplotlib can render inside Tkinter
import matplotlib.pyplot as plt  # import pyplot for plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # connector between Matplotlib figure and Tkinter

# -------------------------- Constants / Palettes -----------------------------
QUAL_PALETTES = [  # list of qualitative palettes the user can choose from
    "tab10","tab20","Set1","Set2","Set3","Paired","Accent","Dark2","Pastel1","Pastel2"  # palette names available in Matplotlib
]  # end of QUAL_PALETTES list

# ----------------------------- Main App Class --------------------------------
class CrochetPatternApp(tk.Tk):  # define a subclass of Tkinter's Tk as our main application window
    def __init__(self):  # constructor initializes window, state, UI, and bindings
        super().__init__()  # call the parent constructor to initialize the Tk window
        self.title("Crochet Pattern Generator")  # set the window title
        self.geometry("1340x980")  # set initial window size (width x height in pixels)
        self.minsize(1080, 820)  # prevent the window from being resized too small

        # --------------------------- State variables --------------------------
        self.img = None  # will hold the loaded PIL Image in grayscale
        self.pattern = None  # will hold the quantized tone array as integers 0..(tones-1)

        # Grid size state (rows = height, cols = width in stitches)  # explain next variables
        self.height_rows = tk.IntVar(value=139)  # number of rows (height in stitches)
        self.width_stitches = tk.IntVar(value=100)  # number of columns (width in stitches)

        # Display / processing options  # explain processing options
        self.keep_aspect = tk.BooleanVar(value=True)  # whether to maintain source aspect ratio
        self.bold_every = tk.IntVar(value=10)  # guide line frequency (every N stitches)
        self.show_guides = tk.BooleanVar(value=True)  # toggle guide lines
        self.invert_image = tk.BooleanVar(value=False)  # invert brightness before quantization
        self.contrast_boost = tk.IntVar(value=0)  # brightness offset (-100..+100) prior to quantization

        # Tone options  # explain tone options
        self.num_tones = tk.IntVar(value=4)  # number of tones (2..10); 0=darkest, last=lightest

        # Color options  # explain color options
        self.use_colors = tk.BooleanVar(value=False)  # if False, grayscale; custom colors still override per tone
        self.palette_name = tk.StringVar(value="tab10")  # selected base palette for color mode
        self.show_legend = tk.BooleanVar(value=True)  # whether to show the tone legend
        self.custom_colors = {}  # dict mapping tone index -> "#RRGGBB" custom color overrides

        # Padding options (in stitches)  # explain padding options
        self.pad_left = tk.IntVar(value=0)  # padding on left side (stitches)
        self.pad_right = tk.IntVar(value=0)  # padding on right side (stitches)
        self.pad_top = tk.IntVar(value=0)  # padding on top side (stitches)
        self.pad_bottom = tk.IntVar(value=0)  # padding on bottom side (stitches)
        self.auto_pad_percent = tk.IntVar(value=10)  # percentage used for automatic equal padding

        # Internal flags  # explain internal helpers
        self._updating = False  # guards against recursive trace updates when linking width/height

        # Build UI and wire up event traces  # explain the next method calls
        self._build_ui()  # create all widgets and layout
        self._set_traces()  # attach change listeners for linked aspect behavior

    # ----------------------------- UI Construction ----------------------------
    def _build_ui(self):  # method to build all Tkinter widgets
        top = ttk.Frame(self, padding=8)  # create a frame for the top control row
        top.pack(side=tk.TOP, fill=tk.X)  # place the frame at the top and stretch horizontally

        ttk.Button(top, text="Open Image…", command=self.open_image).grid(row=0, column=0, padx=(0,8), sticky="w")  # button to load an image

        ttk.Label(top, text="Rows:").grid(row=0, column=1, sticky="e")  # label for rows input
        ttk.Spinbox(top, from_=5, to=4000, width=7, textvariable=self.height_rows).grid(row=0, column=2, padx=(2,12))  # rows spinbox

        ttk.Label(top, text="Stitches wide:").grid(row=0, column=3, sticky="e")  # label for width input
        ttk.Spinbox(top, from_=5, to=4000, width=7, textvariable=self.width_stitches).grid(row=0, column=4, padx=(2,12))  # width spinbox

        ttk.Checkbutton(top, text="Keep aspect (link W/H)", variable=self.keep_aspect).grid(row=0, column=5, padx=(0,12))  # toggle aspect linkage

        ttk.Label(top, text="Tones:").grid(row=0, column=6, sticky="e")  # label for tones input
        ttk.Spinbox(top, from_=2, to=10, width=4, textvariable=self.num_tones, command=self._on_tones_changed).grid(row=0, column=7, padx=(2,10))  # tone count spinbox

        ttk.Label(top, text="Brightness offset").grid(row=0, column=8, sticky="e")  # label for brightness slider
        ttk.Scale(top, from_=-100, to=100, orient=tk.HORIZONTAL, length=140, variable=self.contrast_boost, command=lambda v: self.render()).grid(row=0, column=9, padx=(4,12))  # brightness slider

        ttk.Checkbutton(top, text="Invert", variable=self.invert_image, command=self.render).grid(row=0, column=10, padx=(0,12))  # invert toggle

        ttk.Checkbutton(top, text="Guide every", variable=self.show_guides, command=self.render).grid(row=0, column=11, sticky="e")  # guide toggle
        ttk.Spinbox(top, from_=2, to=400, width=4, textvariable=self.bold_every, command=self.render).grid(row=0, column=12, padx=(2,2))  # guide frequency spinbox
        ttk.Label(top, text="stitches").grid(row=0, column=13, padx=(2,8))  # label "stitches" for clarity

        ttk.Button(top, text="Export PNG", command=lambda: self.export("png")).grid(row=0, column=14, padx=4)  # export PNG button
        ttk.Button(top, text="Export PDF", command=lambda: self.export("pdf")).grid(row=0, column=15, padx=4)  # export PDF button

        # ----------------------- Color & Legend Controls ----------------------
        color_row = ttk.Frame(self, padding=(8,2))  # frame for color controls
        color_row.pack(side=tk.TOP, fill=tk.X)  # place below the top row

        ttk.Checkbutton(color_row, text="Use colors instead of grayscale", variable=self.use_colors, command=self.render).grid(row=0, column=0, padx=(0,12), sticky="w")  # toggle color mode
        ttk.Label(color_row, text="Palette:").grid(row=0, column=1, sticky="e")  # label for palette
        self.palette_combo = ttk.Combobox(color_row, textvariable=self.palette_name, values=QUAL_PALETTES, width=10, state="readonly")  # palette dropdown
        self.palette_combo.grid(row=0, column=2, padx=(4,12))  # place combo
        self.palette_combo.bind("<<ComboboxSelected>>", lambda e: self.render())  # re-render on palette change

        ttk.Checkbutton(color_row, text="Show legend", variable=self.show_legend, command=self.render).grid(row=0, column=3, padx=(0,12))  # toggle legend visibility

        # ------------------- Per-tone Custom Color Controls -------------------
        custom = ttk.Frame(self, padding=(8,2))  # frame for custom color controls
        custom.pack(side=tk.TOP, fill=tk.X)  # place below color row

        ttk.Label(custom, text="Custom tone color (applies in both modes):").grid(row=0, column=0, padx=(0,8))  # label explaining custom colors
        ttk.Label(custom, text="Tone index:").grid(row=0, column=1, sticky="e")  # label for tone index
        self.tone_select = ttk.Spinbox(custom, from_=0, to=9, width=4)  # spinbox to choose tone index (will be clamped)
        self.tone_select.grid(row=0, column=2, padx=(4,8))  # place spinbox
        ttk.Button(custom, text="Pick Color…", command=self.pick_tone_color).grid(row=0, column=3, padx=(2,8))  # button to open color picker
        ttk.Button(custom, text="Reset This Tone", command=self.reset_tone_color).grid(row=0, column=4, padx=(2,8))  # reset selected tone override
        ttk.Button(custom, text="Reset All Custom Colors", command=self.reset_all_colors).grid(row=0, column=5, padx=(2,8))  # reset all overrides

        # ------------------------ Padding Controls ---------------------------
        pad = ttk.Frame(self, padding=(8,2))  # frame for padding widgets
        pad.pack(side=tk.TOP, fill=tk.X)  # place under custom color controls

        ttk.Label(pad, text="Padding (stitches):").grid(row=0, column=0, padx=(0,10))  # label for padding section
        ttk.Label(pad, text="Left").grid(row=0, column=1, sticky="e")  # "Left" label
        ttk.Spinbox(pad, from_=0, to=800, width=5, textvariable=self.pad_left, command=self.render).grid(row=0, column=2, padx=(2,10))  # left padding spinbox
        ttk.Label(pad, text="Right").grid(row=0, column=3, sticky="e")  # "Right" label
        ttk.Spinbox(pad, from_=0, to=800, width=5, textvariable=self.pad_right, command=self.render).grid(row=0, column=4, padx=(2,10))  # right padding spinbox
        ttk.Label(pad, text="Top").grid(row=0, column=5, sticky="e")  # "Top" label
        ttk.Spinbox(pad, from_=0, to=800, width=5, textvariable=self.pad_top, command=self.render).grid(row=0, column=6, padx=(2,10))  # top padding spinbox
        ttk.Label(pad, text="Bottom").grid(row=0, column=7, sticky="e")  # "Bottom" label
        ttk.Spinbox(pad, from_=0, to=800, width=5, textvariable=self.pad_bottom, command=self.render).grid(row=0, column=8, padx=(2,10))  # bottom padding spinbox

        ttk.Label(pad, text="Auto pad %:").grid(row=0, column=9, sticky="e", padx=(12,2))  # label for auto pad percentage
        ttk.Spinbox(pad, from_=0, to=90, width=5, textvariable=self.auto_pad_percent).grid(row=0, column=10, padx=(2,4))  # spinbox to set percentage
        ttk.Button(pad, text="Apply Auto Padding", command=self.apply_auto_padding).grid(row=0, column=11, padx=(2,2))  # button to apply auto padding

        # ------------------------ Figure & Canvas ----------------------------
        self.fig = plt.Figure(figsize=(8.6, 10.6), dpi=100)  # create a Matplotlib figure for on-screen rendering
        self.ax = self.fig.add_subplot(111)  # add a single subplot (axes) to the figure
        self.ax.axis("off")  # hide axes spines/ticks to keep the view clean
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # embed the figure into Tkinter
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # place the canvas to fill remaining space

        # --------------------------- Status Bar ------------------------------
        self.status = tk.StringVar(value="Open an image to begin.")  # status message string
        ttk.Label(self, textvariable=self.status, anchor="w").pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=4)  # label bound to status

    # -------------------------- Variable Traces -------------------------------
    def _set_traces(self):  # set up change listeners to keep width/height linked
        def on_rows_changed(*_):  # callback when rows value changes
            if self._updating:  # avoid recursion while we update the paired value
                return  # do nothing if already updating
            if not self.keep_aspect.get():  # if not keeping aspect, just re-render
                self.render()  # update view
                return  # exit the callback
            if self.img is None:  # if no image loaded, nothing to sync, just render
                self.render()  # update view
                return  # exit
            self._updating = True  # set flag to prevent feedback loop
            try:  # protect critical section
                rows = max(5, int(self.height_rows.get()))  # clamp rows to sensible minimum
                w0, h0 = self.img.size  # get original image size
                aspect = (w0 / h0) if h0 else 1.0  # compute source aspect ratio safely
                self.width_stitches.set(max(5, int(round(rows * aspect))))  # set corresponding width
            finally:  # always executed
                self._updating = False  # release the update lock
            self.render()  # redraw with new dimensions

        def on_cols_changed(*_):  # callback when width value changes
            if self._updating:  # avoid recursion
                return  # bail out
            if not self.keep_aspect.get():  # if aspect not enforced, just render
                self.render()  # redraw
                return  # exit
            if self.img is None:  # if no image, nothing to sync
                self.render()  # redraw
                return  # exit
            self._updating = True  # lock updates
            try:  # protected section
                cols = max(5, int(self.width_stitches.get()))  # clamp columns
                w0, h0 = self.img.size  # original size
                aspect = (w0 / h0) if h0 else 1.0  # compute aspect
                self.height_rows.set(max(5, int(round(cols / aspect))))  # set rows to match aspect
            finally:  # release lock
                self._updating = False  # unlock
            self.render()  # redraw view

        self.height_rows.trace_add("write", on_rows_changed)  # attach rows change handler
        self.width_stitches.trace_add("write", on_cols_changed)  # attach width change handler
        self.keep_aspect.trace_add("write", lambda *_: self.render())  # re-render when toggling keep_aspect

    # ------------------------------ Open Image --------------------------------
    def open_image(self):  # handler for "Open Image…" button
        path = filedialog.askopenfilename(title="Select image", filetypes=[  # show a file open dialog
            ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff"),  # common image formats
            ("All files", "*.*")  # fallback to any file
        ])  # end of filetypes list
        if not path:  # user cancelled dialog
            return  # do nothing
        try:  # attempt to open the selected file
            img = Image.open(path).convert("L")  # load image and convert to grayscale ("L" mode)
        except Exception as e:  # catch any I/O or decoding errors
            messagebox.showerror("Error", f"Failed to open image:\n{e}")  # show error dialog
            return  # abort
        self.img = img  # store the grayscale image
        self.status.set(f"Loaded: {path}")  # update status bar
        if self.keep_aspect.get():  # if aspect linking is enabled
            self._updating = True  # lock updates while syncing paired dim
            try:  # protected
                rows = int(self.height_rows.get())  # get current rows
                w0, h0 = self.img.size  # source size
                aspect = (w0 / h0) if h0 else 1.0  # compute aspect
                self.width_stitches.set(max(5, int(round(rows * aspect))))  # sync width
            finally:  # always
                self._updating = False  # unlock updates
        self.render()  # render the image into the grid

    # --------------------------- Auto Padding ---------------------------------
    def apply_auto_padding(self):  # set equal padding based on percentage of min(rows, cols)
        pct = max(0, min(90, int(self.auto_pad_percent.get())))  # clamp percent to 0..90
        rows = max(5, int(self.height_rows.get()))  # current rows
        cols = max(5, int(self.width_stitches.get()))  # current cols
        border = int(round(min(rows, cols) * (pct / 100.0)))  # compute border in stitches
        self.pad_left.set(border)  # apply to left
        self.pad_right.set(border)  # apply to right
        self.pad_top.set(border)  # apply to top
        self.pad_bottom.set(border)  # apply to bottom
        self.render()  # redraw with new padding

    # ------------------------ Quantization Helpers ----------------------------
    def _quantize_even(self, arr, tones):  # map 0..255 grayscale to 0..tones-1 with even bins
        if tones <= 1:  # degenerate case: single tone
            return np.zeros_like(arr, dtype=np.uint8)  # return zeros
        bins = np.linspace(0, 255, tones+1, endpoint=True)[1:-1]  # compute internal bin edges
        q = np.digitize(arr, bins, right=False).astype(np.uint8)  # assign each pixel to a bin index
        return q  # return the quantized array

    # --------------------------- Pattern Construction -------------------------
    def _make_pattern_array(self, rows, cols, tones, invert, bright_shift):  # build the final tone array
        if self.img is None:  # if no image loaded
            return None  # nothing to do

        # Compute inner area after padding (where the image will be placed)  # explain next calculations
        pl = max(0, int(self.pad_left.get()))  # left padding stitches
        pr = max(0, int(self.pad_right.get()))  # right padding stitches
        pt = max(0, int(self.pad_top.get()))  # top padding stitches
        pb = max(0, int(self.pad_bottom.get()))  # bottom padding stitches

        inner_w = max(1, cols - pl - pr)  # width available for the image
        inner_h = max(1, rows - pt - pb)  # height available for the image

        # Resize the source image to fit inside the inner area  # explain resizing
        img = self.img  # alias the source image
        if self.keep_aspect.get():  # keep aspect: fit within inner box
            w0, h0 = img.size  # get source size
            target_aspect = inner_w / inner_h  # aspect of inner area
            src_aspect = (w0 / h0) if h0 else 1.0  # aspect of source
            if src_aspect > target_aspect:  # source is relatively wider
                new_w = inner_w  # match inner width
                new_h = max(1, int(round(inner_w / src_aspect)))  # compute height from aspect
            else:  # source is relatively taller
                new_h = inner_h  # match inner height
                new_w = max(1, int(round(inner_h * src_aspect)))  # compute width from aspect
        else:  # don't keep aspect: stretch to inner box
            new_w, new_h = inner_w, inner_h  # fill the inner area completely

        small = img.resize((new_w, new_h), Image.NEAREST)  # resize using nearest-neighbor to preserve blockiness

        # Create base canvas in range 0..255 with zeros (0) for padding  # explain canvas
        canvas = np.zeros((rows, cols), dtype=np.int16)  # start with zeros so padding becomes darkest tone (0 after quantization)

        arr = np.array(small, dtype=np.int16)  # convert resized image to array
        if invert:  # if invert option is set
            arr = 255 - arr  # invert brightness
        if bright_shift != 0:  # if brightness offset is non-zero
            arr = np.clip(arr + int(bright_shift), 0, 255)  # shift and clamp to valid range

        off_x = pl + (inner_w - new_w) // 2  # compute x offset to center image within inner area
        off_y = pt + (inner_h - new_h) // 2  # compute y offset to center image within inner area
        canvas[off_y:off_y+new_h, off_x:off_x+new_w] = arr  # paste resized image values into the canvas

        q = self._quantize_even(canvas.astype(np.uint8), tones)  # quantize the entire canvas to tone indices
        return q  # return the tone array

    # ------------------------------ Colormap ----------------------------------
    def _build_palette_list(self, tones):  # get a list of RGBA colors from the chosen palette
        try:  # attempt to fetch the selected palette
            base = matplotlib.cm.get_cmap(self.palette_name.get())  # get the named colormap
            base_colors = base(np.linspace(0, 1, tones))  # sample it at 'tones' evenly spaced points
        except Exception:  # fallback if palette name is invalid
            base = matplotlib.cm.get_cmap("tab10")  # default palette
            base_colors = base(np.linspace(0, 1, tones))  # sample default palette
        return base_colors  # return RGBA array

    def _get_cmap(self, tones):  # build the effective colormap considering mode and custom overrides
        if self.use_colors.get():  # when in color mode
            base_colors = self._build_palette_list(tones)  # get base palette colors
            colors = []  # list to hold final colors
            for i in range(tones):  # for each tone index
                if i in self.custom_colors:  # if custom color override is present
                    rgb = matplotlib.colors.to_rgb(self.custom_colors[i])  # parse hex color to RGB
                    colors.append((*rgb, 1.0))  # append RGBA with full alpha
                else:  # otherwise
                    colors.append(tuple(base_colors[i]))  # use palette color
            return matplotlib.colors.ListedColormap(colors)  # return a discrete colormap
        else:  # grayscale mode
            levels = np.linspace(0, 1, tones)  # compute grayscale levels from black to white
            gray_colors = [matplotlib.colors.to_rgba(str(v)) for v in levels]  # convert gray levels to RGBA
            for i in range(len(gray_colors)):  # apply any custom overrides even in grayscale mode
                if i in self.custom_colors:  # if user set a custom color for this tone
                    rgb = matplotlib.colors.to_rgb(self.custom_colors[i])  # parse hex
                    gray_colors[i] = (*rgb, 1.0)  # override with chosen color
            return matplotlib.colors.ListedColormap(gray_colors)  # return discrete colormap

    # --------------------------- Drawing / Rendering ---------------------------
    def _draw_contrast_grid(self, ax, arr, tones):  # render the pattern to the given axes
        H, W = arr.shape  # extract height and width of the pattern
        cmap = self._get_cmap(tones)  # build the colormap based on settings
        ax.imshow(arr, cmap=cmap, interpolation="none", vmin=0, vmax=tones-1)  # draw the tone array as an image

        # Draw high-contrast gridlines so cell borders are visible on any tone  # explain gridlines
        for x in range(W+1):  # iterate vertical grid lines
            ax.plot([x-0.5, x-0.5], [-0.5, H-0.5], color="white", linewidth=0.6)  # white line on top for light-on-dark
            ax.plot([x-0.5, x-0.5], [-0.5, H-0.5], color="black", linewidth=0.3, alpha=0.7)  # thin black for dark-on-light
        for y in range(H+1):  # iterate horizontal grid lines
            ax.plot([-0.5, W-0.5], [y-0.5, y-0.5], color="white", linewidth=0.6)  # white line
            ax.plot([-0.5, W-0.5], [y-0.5, y-0.5], color="black", linewidth=0.3, alpha=0.7)  # black line

        # Optional thicker guide lines every N stitches (both directions)  # explain guides
        if self.show_guides.get() and self.bold_every.get() >= 2:  # only if enabled and step is at least 2
            step = int(self.bold_every.get())  # guide frequency
            for x in range(0, W+1, step):  # every 'step' columns
                ax.plot([x-0.5, x-0.5], [-0.5, H-0.5], color="black", linewidth=1.2)  # thicker vertical guide
            for y in range(0, H+1, step):  # every 'step' rows
                ax.plot([-0.5, W-0.5], [y-0.5, y-0.5], color="black", linewidth=1.2)  # thicker horizontal guide

        # Row numbers along the left side: 1 at bottom, H at top  # explain numbering
        for r in range(H):  # iterate each row index
            ax.text(-2.5, r, str(H - r), va="center", ha="right", fontsize=6, color="black")  # draw row label

        # Optional tone legend showing color swatches for each tone  # explain legend
        if self.show_legend.get():  # if legend is enabled
            cmap_arr = np.arange(tones).reshape(1, -1)  # build a 1xT array to visualize tones as blocks
            legend_ax = ax.inset_axes([1.01, 0.0, 0.08, 0.9], transform=ax.transAxes)  # create an inset axes to the right
            legend_ax.imshow(cmap_arr, cmap=cmap, aspect="auto", interpolation="nearest", vmin=0, vmax=tones-1)  # draw tone blocks
            legend_ax.set_yticks([])  # hide y ticks
            legend_ax.set_xticks(range(tones))  # put x ticks at each tone index
            legend_ax.set_xticklabels([str(i) for i in range(tones)], rotation=90, fontsize=7)  # label tones 0..T-1 vertically
            legend_ax.set_title("Tone", fontsize=8, pad=4)  # title for the legend

        ax.set_xlim(-3.5, W-0.5)  # extend left limit to leave room for row numbers
        ax.set_ylim(H-0.5, -0.5)  # flip y-axis so 0 is at top visually but numbers read bottom-up
        ax.axis("off")  # turn off axis lines and ticks
        mode = "Colors" if self.use_colors.get() else "Grayscale"  # build a mode label
        ax.set_title(f"Crochet Grid Pattern ({W}×{H}, {tones} tones, {mode}) — Row numbers: 1 bottom, {H} top", fontsize=10)  # descriptive title

    # ------------------------------- Tone Colors -------------------------------
    def pick_tone_color(self):  # handler to pick a custom color for a specific tone index
        tones = max(2, min(10, int(self.num_tones.get())))  # clamp tone count
        try:  # parse the requested tone index
            idx = int(self.tone_select.get())  # get tone index from spinbox
        except Exception:  # invalid integer
            messagebox.showerror("Invalid tone", "Please enter a valid tone index.")  # show error
            return  # abort
        if idx < 0 or idx >= tones:  # ensure index in range
            messagebox.showerror("Invalid tone", f"Tone index must be between 0 and {tones-1}.")  # show error
            return  # abort
        initial = self.custom_colors.get(idx, "#ffffff")  # default color is white or previous custom
        color = colorchooser.askcolor(color=initial, title=f"Pick color for tone {idx}")  # show OS color picker
        if not color or not color[1]:  # user cancelled or invalid
            return  # bail
        self.custom_colors[idx] = color[1]  # save hex color string for this tone
        self.render()  # redraw to apply the change

    def reset_tone_color(self):  # remove a custom color for the selected tone
        try:  # parse tone index
            idx = int(self.tone_select.get())  # read tone index
        except Exception:  # invalid input
            messagebox.showerror("Invalid tone", "Please enter a valid tone index.")  # show error
            return  # abort
        if idx in self.custom_colors:  # if there is an override set
            del self.custom_colors[idx]  # delete the override
            self.render()  # redraw to reflect default color

    def reset_all_colors(self):  # clear all custom color overrides
        self.custom_colors = {}  # reset dictionary to empty
        self.render()  # redraw to use defaults everywhere

    def _on_tones_changed(self):  # when tone count changes, update controls and prune overrides
        tones = max(2, min(10, int(self.num_tones.get())))  # clamp tone count
        self.tone_select.config(from_=0, to=max(0, tones-1))  # update tone index spinbox bounds
        self.custom_colors = {k:v for k,v in self.custom_colors.items() if 0 <= k < tones}  # drop out-of-range overrides
        self.render()  # redraw with new tone count

    # ------------------------------- Rendering --------------------------------
    def render(self):  # recompute pattern and draw it on the canvas
        if self.img is None:  # if no image loaded yet
            self.ax.clear()  # clear axes
            self.ax.text(0.5, 0.5, "Open an image to generate a pattern.", ha="center", va="center", transform=self.ax.transAxes)  # show helper text
            self.ax.axis("off")  # hide axes
            self.canvas.draw_idle()  # request canvas redraw
            return  # exit
        rows = max(5, int(self.height_rows.get()))  # read rows and clamp
        cols = max(5, int(self.width_stitches.get()))  # read columns and clamp
        tones = max(2, min(10, int(self.num_tones.get())))  # clamp tone count
        invert = bool(self.invert_image.get())  # read invert flag
        bright_shift = int(self.contrast_boost.get())  # read brightness offset

        arr = self._make_pattern_array(rows, cols, tones, invert, bright_shift)  # build the quantized pattern
        if arr is None:  # ensure array exists
            return  # bail
        self.pattern = arr  # store the current pattern

        self.ax.clear()  # clear previous drawing
        self._draw_contrast_grid(self.ax, arr, tones)  # draw current pattern
        self.canvas.draw_idle()  # update the Tkinter canvas

    # -------------------------------- Export ----------------------------------
    def export(self, kind="png"):  # export pattern to PNG or PDF
        if self.pattern is None:  # ensure we have something to save
            messagebox.showinfo("Nothing to export", "Load an image and generate a pattern first.")  # info dialog
            return  # abort
        filetypes = [("PNG image","*.png")] if kind=="png" else [("PDF file","*.pdf")]  # choose dialog filters
        path = filedialog.asksaveasfilename(defaultextension="."+kind, filetypes=filetypes,  # show save-as dialog
                                            title=f"Save pattern as {kind.upper()}")  # set dialog title
        if not path:  # user cancelled
            return  # abort
        tones = max(2, min(10, int(self.num_tones.get())))  # clamp tones for rendering
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)  # create a high-DPI figure for crisp export
        ax = fig.add_subplot(111)  # add a single axes
        self._draw_contrast_grid(ax, self.pattern, tones)  # draw onto the export figure
        try:  # guard file writing
            fig.savefig(path, bbox_inches="tight")  # save to chosen path
            messagebox.showinfo("Saved", f"Exported pattern to:\n{path}")  # success message
        except Exception as e:  # handle write errors
            messagebox.showerror("Error", f"Failed to save:\n{e}")  # show error
        finally:  # cleanup
            plt.close(fig)  # close the figure to free memory

# ------------------------------- Entrypoint -----------------------------------
if __name__ == "__main__":  # check if this file is executed directly
    app = CrochetPatternApp()  # instantiate the application
    app.mainloop()  # enter the Tkinter main event loop
