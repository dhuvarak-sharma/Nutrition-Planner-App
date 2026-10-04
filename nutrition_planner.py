import tkinter as tk
from tkinter import font as tkfont
import threading

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import database_mysql as db

# Colour palete 
BG        = "#FAF0DC"
ORANGE    = "#F5A623"
DARK_ORG  = "#E08C10"
CARD_BG   = "#F5A623"
CARD_TEXT = "#3B2000"
TITLE_CLR = "#2B1800"
BODY_CLR  = "#3B2000"
LIGHT_ORG = "#FFD580"
SCROLLBAR = "#E09A1A"

'''
temp={"Paneer Butter Masala":[250,18,6,300]}
x=int(input("How many grams?"))
a=temp["Paneer Butter Masala"][0]*x/100

'''


# Image helpers
image_cache = {}

def make_placeholder(w, h):
    # Solid orange placeholder when no image is available.
    if PIL_AVAILABLE:
        img = Image.new("RGB", (w, h), ORANGE)
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2
        draw.ellipse([cx-20, cy-20, cx+20, cy+20], fill=LIGHT_ORG, outline=DARK_ORG, width=2)
        return ImageTk.PhotoImage(img)
    return None

def load_local_image_async(path, size, callback):
    
    # Load a local image file in a background thread. Falls back to placeholder if the file doesn't exist or fails.
    
    key = (path, size)
    if key in image_cache:
        callback(image_cache[key])
        return

    def _load():
        if not PIL_AVAILABLE:
            callback(None)
            return
        try:
            img = Image.open(path).convert("RGB")
            # Cover-crop to fill target size
            w, h = img.size
            tw, th = size
            src_ratio = w / h
            tgt_ratio = tw / th
            if src_ratio > tgt_ratio:
                new_w = int(h * tgt_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / tgt_ratio)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))
            img = img.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_cache[key] = photo
            callback(photo)
        except Exception:
            callback(None)   # file missing - caller will keep placeholder

    threading.Thread(target=_load, daemon=True).start()


# Main Part
class RecipePlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nutrition Planner")
        self.geometry("780x560")
        self.resizable(True, True)
        self.configure(bg=BG)

        # Load saved favourites on startup
        self.favourites = db.load_favourites()

        self._setup_fonts()

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for S in (HomeScreen, DishListScreen, DishDetailScreen,
                  FilterScreen, FilteredResultsScreen, FavouritesScreen):
            frame = S(container, self)
            self.frames[S] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomeScreen)

        # Save favourites when window closes
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        db.save_favourites(self.favourites)
        self.destroy()

    def _setup_fonts(self):
        self.font_title = tkfont.Font(family="Helvetica", size=22, weight="bold")
        self.font_head  = tkfont.Font(family="Helvetica", size=14, weight="bold")
        self.font_body  = tkfont.Font(family="Helvetica", size=11)
        self.font_small = tkfont.Font(family="Helvetica", size=10)
        self.font_btn   = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.font_card  = tkfont.Font(family="Helvetica", size=13, weight="bold")

    def show_frame(self, screen_class, **kwargs):
        frame = self.frames[screen_class]
        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)
        frame.tkraise()


#Button helpers 
def orange_btn(parent, text, command, width=18, font=None):
    f = font or ("Helvetica", 11, "bold")
    return tk.Button(parent, text=text, command=command,
                     bg=ORANGE, fg=CARD_TEXT, activebackground=DARK_ORG,
                     relief="flat", bd=0, padx=14, pady=8,
                     font=f, cursor="hand2", width=width)

def home_btn(parent, command):
    return tk.Button(parent, text="  Home  ", command=command,
                     bg=ORANGE, fg=CARD_TEXT, activebackground=DARK_ORG,
                     relief="flat", bd=0, padx=10, pady=5,
                     font=("Helvetica", 10, "bold"), cursor="hand2")



#  Screen 1 – Home

class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="️", font=("Helvetica", 52), bg=BG).pack(pady=(60, 0))
        tk.Label(self, text="Nutrition Planner", font=self.app.font_title,
                 bg=BG, fg=TITLE_CLR).pack(pady=(8, 4))
       # tk.Label(self, text="Discover, filter & savour",
                # font=("Helvetica", 12, "italic"), bg=BG, fg="#8B6020").pack(pady=(0, 40))

        for text, cmd in [
            (" View Dishes",   lambda: self.app.show_frame(DishListScreen)),
            (" Filter Dishes", lambda: self.app.show_frame(FilterScreen)),
            (" Favourites",    lambda: self.app.show_frame(FavouritesScreen)),
        ]:
            orange_btn(self, text, cmd, width=24,
                       font=("Helvetica", 13, "bold")).pack(pady=8)



#  Shared scrollable dish-list

class DishListWidget(tk.Frame):
    def __init__(self, parent, app, detail_source, show_remove=False):
        super().__init__(parent, bg=BG)
        self.app = app
        self.detail_source = detail_source
        self.show_remove = show_remove   # True on Favourites screen
        self._photo_refs = []
        self._build()

    def _build(self):
        # Search bar
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=16, pady=(10, 6))
        tk.Label(bar, text="", bg=BG, font=("Helvetica", 13)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        entry = tk.Entry(bar, textvariable=self.search_var,
                         font=("Helvetica", 12), bg=LIGHT_ORG, fg=CARD_TEXT,
                         relief="flat", bd=0, insertbackground=CARD_TEXT)
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(6, 0))
        entry.insert(0, "Search")
        entry.bind("<FocusIn>",  lambda e: entry.delete(0, "end") if entry.get() == "Search" else None)
        entry.bind("<FocusOut>", lambda e: entry.insert(0, "Search") if not entry.get() else None)

        # Scrollable canvas
        canvas_frame = tk.Frame(self, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=10)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical",
                                 command=self.canvas.yview, bg=SCROLLBAR)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=BG)
        win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(win_id, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self.dishes_to_show = db.get_all_dishes()

    def load_dishes(self, dishes):
        self.dishes_to_show = dishes
        self._render()

    def _filter(self):
        q = self.search_var.get().lower()
        if q in ("", "search"):
            self._render()
        else:
            filtered = [d for d in self.dishes_to_show
                        if q in d["name"].lower() or q in d["cuisine"].lower()]
            self._render(filtered)

    def _render(self, dishes=None):
        if dishes is None:
            dishes = self.dishes_to_show
        for w in self.inner.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        for dish in dishes:
            self._make_dish_row(dish)

    def _make_dish_row(self, dish):
        row = tk.Frame(self.inner, bg=ORANGE, bd=0)
        row.pack(fill="x", padx=6, pady=5)

        # Thumbnail
        img_lbl = tk.Label(row, bg=ORANGE, width=70, height=70)
        img_lbl.pack(side="left", padx=(8, 10), pady=8)
        ph = make_placeholder(70, 70)
        if ph:
            img_lbl.config(image=ph)
            self._photo_refs.append(ph)

        def set_img(photo, lbl=img_lbl):
            if photo:
                lbl.config(image=photo)
                self._photo_refs.append(photo)
            self.canvas.update_idletasks()

        load_local_image_async(dish["image"], (70, 70), set_img)

        # Text block
        text_frame = tk.Frame(row, bg=ORANGE)
        text_frame.pack(side="left", fill="both", expand=True, pady=8)

        tk.Label(text_frame, text=dish["name"],
                 font=("Helvetica", 13, "bold"), bg=ORANGE, fg=CARD_TEXT,
                 anchor="w").pack(anchor="w")
        tk.Label(text_frame, text=f"Cuisine: {dish['cuisine']}",
                 font=("Helvetica", 10), bg=ORANGE, fg="#5A3000",
                 anchor="w").pack(anchor="w")
        tk.Label(text_frame, text=dish["description"],
                 font=("Helvetica", 10), bg=ORANGE, fg=CARD_TEXT,
                 wraplength=380, justify="left", anchor="w").pack(anchor="w")

        #  Remove button (only on Favourites screen) 
        if self.show_remove:
            def remove(d=dish):
                self.app.favourites.discard(d["id"])
                db.save_favourites(self.app.favourites)          # persist immediately
                # Re-render the list
                updated = [x for x in self.dishes_to_show if x["id"] != d["id"]]
                self.load_dishes(updated)
                # Refresh FavouritesScreen empty-label logic
                self.app.frames[FavouritesScreen].on_show()

            tk.Button(row, text="Remove", command=remove,
                      bg="#C0392B", fg="white", activebackground="#A93226",
                      relief="flat", bd=0, padx=8, pady=4,
                      font=("Helvetica", 9, "bold"), cursor="hand2").pack(
                          side="right", padx=10, pady=8, anchor="center")

        # Make row clickable (except remove button)
        for widget in [row, img_lbl, text_frame] + list(text_frame.winfo_children()):
            widget.bind("<Button-1>", lambda e, d=dish: self._open_detail(d))
            widget.config(cursor="hand2")

    def _open_detail(self, dish):
        self.app.show_frame(DishDetailScreen,
                            dish=dish,
                            source=self.detail_source)


#  Screen 2 – View All Dishes

class DishListScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg="#2B1800")
        topbar.pack(fill="x")
        home_btn(topbar, lambda: self.app.show_frame(HomeScreen)).pack(side="left", padx=12, pady=8)
        tk.Label(topbar, text="All Dishes", font=("Helvetica", 13),
                 bg="#2B1800", fg="#FAD98A").pack(side="left", padx=20, pady=8)

        self.list_widget = DishListWidget(self, self.app, DishListScreen)
        self.list_widget.pack(fill="both", expand=True)

    def on_show(self, **kwargs):
        self.list_widget.load_dishes(db.get_all_dishes())



#  Screen 3 – Dish Details

class DishDetailScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._photo_ref = None
        self._current_dish = None
        self._source = DishListScreen

    def on_show(self, dish=None, source=DishListScreen, **kwargs):
        if dish is None:
            return
        self._current_dish = dish
        self._source = source
        for w in self.winfo_children():
            w.destroy()
        self._build(dish)

    def _build(self, dish):
        # Top bar
        topbar = tk.Frame(self, bg="#2B1800")
        topbar.pack(fill="x")
        home_btn(topbar, lambda: self.app.show_frame(HomeScreen)).pack(side="left", padx=12, pady=8)
        tk.Label(topbar, text="Dish Details", font=("Helvetica", 13),
                 bg="#2B1800", fg="#FAD98A").pack(side="left", padx=20, pady=8)

        # Scrollable body
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=BG)
        cw = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))

        # Hero
        hero = tk.Frame(body, bg=BG)
        hero.pack(fill="x", padx=20, pady=(18, 10))

        img_lbl = tk.Label(hero, bg=LIGHT_ORG, width=140, height=120)
        img_lbl.pack(side="left", padx=(0, 18))
        ph = make_placeholder(140, 120)
        if ph:
            img_lbl.config(image=ph)
            self._photo_ref = ph

        def set_img(photo):
            if photo:
                img_lbl.config(image=photo)
                self._photo_ref = photo

    
        load_local_image_async(dish["image"], (140, 120), set_img)

        info = tk.Frame(hero, bg=BG)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=dish["name"], font=("Helvetica", 20, "bold"),
                 bg=BG, fg=TITLE_CLR, anchor="w", wraplength=400,
                 justify="left").pack(anchor="w")
        tk.Label(info, text=dish["description"], font=("Helvetica", 11),
                 bg=BG, fg=BODY_CLR, wraplength=420, justify="left",
                 anchor="w").pack(anchor="w", pady=(6, 10))

        meta_row = tk.Frame(info, bg=BG)
        meta_row.pack(anchor="w")
        for label, value in [("Cuisine: ", dish["cuisine"]),
                              ("  Time: ", dish["time"])]:
            tk.Label(meta_row, text=label, font=("Helvetica", 11, "bold"),
                     bg=BG, fg=TITLE_CLR).pack(side="left")
            tk.Label(meta_row, text=value, font=("Helvetica", 11),
                     bg=BG, fg=BODY_CLR).pack(side="left")

        tk.Frame(body, bg=ORANGE, height=2).pack(fill="x", padx=20, pady=8)

        tk.Label(body, text="Ingredients:", font=("Helvetica", 12, "bold"),
                 bg=BG, fg=TITLE_CLR, anchor="w").pack(anchor="w", padx=20)
        tk.Label(body, text=dish["ingredients"], font=("Helvetica", 11),
                 bg=BG, fg=BODY_CLR, wraplength=700, justify="left",
                 anchor="w").pack(anchor="w", padx=20, pady=(2, 10))

        tk.Label(body, text="Nutritional Value (per 100 gm):",
                 font=("Helvetica", 12, "bold"), bg=BG, fg=TITLE_CLR,
                 anchor="w").pack(anchor="w", padx=20)
        tk.Label(body, text=dish["nutrition"], font=("Helvetica", 11),
                 bg=BG, fg=BODY_CLR, wraplength=700, justify="left",
                 anchor="w").pack(anchor="w", padx=20, pady=(2, 16))

        # Favourite toggle button
        is_fav = dish["id"] in self.app.favourites
        self.fav_btn = orange_btn(
            body,
            "Added to Favourites!" if is_fav else "Add to Favourites",
            lambda: self._toggle_fav(dish),
            width=24, font=("Helvetica", 13, "bold")
        )
        self.fav_btn.pack(pady=(8, 30))

    def _toggle_fav(self, dish):
        if dish["id"] in self.app.favourites:
            self.app.favourites.discard(dish["id"])
            self.fav_btn.config(text="Add to Favourites")
        else:
            self.app.favourites.add(dish["id"])
            self.fav_btn.config(text="✓ Added to Favourites")
        # Save immediately so it persists
        db.save_favourites(self.app.favourites)



#  Screen 4 – Filter Dishes

class FilterScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg="#2B1800")
        topbar.pack(fill="x")
        home_btn(topbar, lambda: self.app.show_frame(HomeScreen)).pack(side="left", padx=12, pady=8)
        tk.Label(topbar, text="Filter Dishes", font=("Helvetica", 13),
                 bg="#2B1800", fg="#FAD98A").pack(side="left", padx=20, pady=8)

        tk.Label(self, text="Filter Dishes", font=("Helvetica", 18, "bold"),
                 bg=BG, fg=TITLE_CLR).pack(pady=(24, 18))

        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=40)

        self.vars = {}
        fields = [
            ("Ingredients", "e.g. paneer, tomato"),
            ("Nutrition",   "e.g. low calorie"),
            ("Cuisine",     "e.g. Italian, Indian"),
            ("Time Taken",  "e.g. under 30 mins"),
        ]
        for col, (label, hint) in enumerate(fields):
            tk.Label(grid, text=label, font=("Helvetica", 11, "bold"),
                     bg=BG, fg=TITLE_CLR).grid(row=0, column=col, padx=12, pady=4, sticky="w")
            var = tk.StringVar()
            self.vars[label] = var
            tk.Entry(grid, textvariable=var, font=("Helvetica", 11),
                     bg=LIGHT_ORG, fg=CARD_TEXT, relief="flat", bd=0,
                     width=16).grid(row=1, column=col, padx=12, pady=4, ipady=8)
            tk.Label(grid, text=hint, font=("Helvetica", 9, "italic"),
                     bg=BG, fg="#8B6020").grid(row=2, column=col, padx=12, sticky="w")

        orange_btn(self, "Search Dishes: ", self._search,
                   width=22, font=("Helvetica", 13, "bold")).pack(pady=30)

    def _search(self):
        import re
        ingredients = self.vars["Ingredients"].get().lower().strip()
        nutrition   = self.vars["Nutrition"].get().lower().strip()
        cuisine     = self.vars["Cuisine"].get().lower().strip()
        time_filter = self.vars["Time Taken"].get().lower().strip()

        result = []
        for d in db.get_all_dishes():
            #Cuisine filter
            if cuisine and cuisine not in d["cuisine"].lower():
                continue

            #Ingredients filter
            if ingredients:
                terms = [t.strip() for t in ingredients.split(",") if t.strip()]
                if not all(t in d["ingredients"].lower() for t in terms):
                    continue

            # Nutrition filter. Split user input by comma so they can type e.g. "calcium, protein"
            # Each term must appear somewhere in the dish's nutrition string
            if nutrition:
                terms = [t.strip() for t in nutrition.split(",") if t.strip()]
                if not all(t in d["nutrition"].lower() for t in terms):
                    continue

            # Time filter:
            # User types e.g. "30", "under 30", "30 mins". App extracts the limit number from user input, then compares against the maximum time of the dish
            if time_filter:
                user_nums = re.findall(r"\d+", time_filter)
                if user_nums:
                    limit = int(user_nums[0])
                    dish_nums = re.findall(r"\d+", d["time"])
                    if dish_nums:
                        # Use the last (maximum) number in the dish time range
                        dish_max = int(dish_nums[-1])
                        if dish_max > limit:
                            continue

            result.append(d)

        self.app.show_frame(FilteredResultsScreen, dishes=result)



#  Screen 5 – Filtered Results

class FilteredResultsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg="#2B1800")
        topbar.pack(fill="x")
        home_btn(topbar, lambda: self.app.show_frame(HomeScreen)).pack(side="left", padx=12, pady=8)
        tk.Label(topbar, text="Dishes Based on Requirements",
                 font=("Helvetica", 13), bg="#2B1800", fg="#FAD98A").pack(side="left", padx=12, pady=8)

        self.list_widget = DishListWidget(self, self.app, FilteredResultsScreen)
        self.list_widget.pack(fill="both", expand=True)

    def on_show(self, dishes=None, **kwargs):
        self.list_widget.load_dishes(dishes if dishes is not None else db.get_all_dishes())



#  Screen 6 – Favourites  (with Remove button + empty state)

class FavouritesScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg="#2B1800")
        topbar.pack(fill="x")
        home_btn(topbar, lambda: self.app.show_frame(HomeScreen)).pack(side="left", padx=12, pady=8)
        tk.Label(topbar, text="My Favourites", font=("Helvetica", 13),
                 bg="#2B1800", fg="#FAD98A").pack(side="left", padx=12, pady=8)

        
        self.list_widget = DishListWidget(self, self.app,
                                          FavouritesScreen, show_remove=True) # show_remove=True adds the red Remove button on each card

        self.empty_lbl = tk.Label(
            self,
            text="No favourites yet.\nBrowse dishes and tap 'Add to Favourites'.",
            font=("Helvetica", 13, "italic"), bg=BG, fg="#8B6020", justify="center"
        )

    def on_show(self, **kwargs):
        favs = [d for d in db.get_all_dishes() if d["id"] in self.app.favourites]
        if favs:
            self.empty_lbl.pack_forget()
            self.list_widget.pack(fill="both", expand=True)
            self.list_widget.load_dishes(favs)
        else:
            self.list_widget.pack_forget()
            self.empty_lbl.pack(expand=True)


if __name__ == "__main__":
    # Create the tables (if they don't exist) and fill them with the starting dishes (only if the dishes table is currently empty)
    db.init_db()
    db.seed_if_empty()

    app = RecipePlannerApp()
    app.mainloop()
