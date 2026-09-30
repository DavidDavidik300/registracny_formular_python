"""
Servis PC - objednávka opravy
Okenná aplikácia v tkinter (Python 3.8+), bez externých knižníc.

Spustenie:  python servis.py
"""
import re
import sys
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont
from tkinter import ttk

# =====================================================================
#  CENNÍK A NASTAVENIA
# =====================================================================
ZARIADENIA = {
    "Stolový PC": 50,
    "Notebook": 65,
    "Tablet": 30,
}
SLUZBY = {
    "Čistenie od prachu": 10,
    "Záloha dát": 15,
    "Inštalácia OS": 20,
    "Antivirus": 20,
}
PREDVOLENE_ZARIADENIE = "Stolový PC"
MAX_POPIS = 300          # max. počet znakov v popise poruchy
PADX_VYSTUP = 16         # vnútorný okraj výstupného poľa

# =====================================================================
#  FARBY (chladná šedá + tmavomodrá + jeden tyrkysový akcent)
#  Kontrasty sú overené na WCAG AA (text >= 4.5:1, ovládacie prvky >= 3:1)
# =====================================================================
BG = "#eef1f5"            # pozadie okna
CARD = "#ffffff"          # panely
FIELD = "#f7f9fb"         # pozadie vstupných polí
NAVY = "#14213d"          # nadpisy, panel s cenou
NAVY_TEXT = "#c3cce0"     # svetlejší text na tmavomodrom
TEXT = "#1b2436"
MUTED = "#5b6472"
BORDER = "#d5dbe4"        # jemné orámovanie panelov
INPUT_BORDER = "#8a94a6"  # orámovanie polí (kontrast >= 3:1)
ACCENT = "#0f766e"
ACCENT_DARK = "#0b5e58"
SOFT = "#e3e8ef"          # sekundárne tlačidlá
SOFT_HOVER = "#d3dbe6"
ERROR = "#b42318"
OK = "#166534"

IS_MAC = sys.platform == "darwin"

# =====================================================================
#  HLAVNÉ OKNO
# =====================================================================
root = tk.Tk()
root.title("Servis PC - objednávka")
root.configure(bg=BG)
root.resizable(False, False)          # pevná veľkosť okna


def vyber_pismo(kandidati, zaloha):
    """Vyberie prvé písmo, ktoré je v systéme dostupné."""
    dostupne = set(tkfont.families())
    for meno in kandidati:
        if meno in dostupne:
            return meno
    return zaloha


FAM = vyber_pismo(["Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu",
                   "Noto Sans", "DejaVu Sans"], "Helvetica")
FONT = (FAM, 10)
FONT_SMALL = (FAM, 9)
FONT_BOLD = (FAM, 10, "bold")
FONT_SECTION = (FAM, 11, "bold")
FONT_TITLE = (FAM, 22, "bold")
FONT_SUBTITLE = (FAM, 11)
FONT_PRICE = (FAM, 28, "bold")
FONT_SPIN = (FAM, 12)

# ---------- Premenné (StringVar, BooleanVar, IntVar) ----------
var_zariadenie = tk.StringVar(value=PREDVOLENE_ZARIADENIE)
var_sluzby = {nazov: tk.BooleanVar(value=False) for nazov in SLUZBY}
var_pocet = tk.IntVar(value=1)

cislo_objednavky = 0      # počítadlo odoslaných objednávok


# =====================================================================
#  POMOCNÉ FUNKCIE PRE VZHĽAD
# =====================================================================
def karta(parent, nadpis, poznamka=""):
    """Biely panel s nadpisom. Vráti (panel, telo, štítok poznámky)."""
    panel = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                     highlightcolor=BORDER, highlightthickness=1)
    hlavicka = tk.Frame(panel, bg=CARD)
    hlavicka.pack(fill="x", padx=16, pady=(10, 4))
    tk.Label(hlavicka, text=nadpis, font=FONT_SECTION, bg=CARD,
             fg=TEXT).pack(side="left")
    stitok = tk.Label(hlavicka, text=poznamka, font=FONT_SMALL, bg=CARD,
                      fg=MUTED)
    stitok.pack(side="right")
    telo = tk.Frame(panel, bg=CARD)
    telo.pack(fill="x", padx=16, pady=(0, 12))
    return panel, telo, stitok


def vytvor_entry(parent):
    e = tk.Entry(parent, font=FONT, bg=FIELD, fg=TEXT, relief="flat", bd=5,
                 width=1, highlightthickness=1, highlightbackground=INPUT_BORDER,
                 highlightcolor=ACCENT, insertbackground=TEXT)
    # Enter presunie kurzor na ďalšie pole
    e.bind("<Return>", lambda ev: ev.widget.tk_focusNext().focus_set())
    # pri písaní zmizne červené orámovanie chyby
    e.bind("<KeyRelease>", lambda ev: oznac_chybu(ev.widget, False))
    return e


def pole(parent, popis, riadok, stlpec=0, sirka=1, posledne=False):
    """Popis (Label) nad vstupným poľom (Entry), umiestnené v mriežke."""
    okraj = (0, 0) if stlpec == 0 else (10, 0)
    tk.Label(parent, text=popis, font=FONT_SMALL, bg=CARD, fg=MUTED
             ).grid(row=riadok, column=stlpec, columnspan=1, sticky="w",
                    padx=okraj)
    e = vytvor_entry(parent)
    e.grid(row=riadok + 1, column=stlpec, sticky="ew", padx=okraj,
           pady=(2, 0 if posledne else 8), ipady=2)
    return e


def oznac_chybu(entry, chyba):
    """Prepne orámovanie poľa na červené (chyba) alebo späť na normálne."""
    if chyba:
        entry.config(highlightbackground=ERROR, highlightcolor=ERROR)
    else:
        entry.config(highlightbackground=INPUT_BORDER, highlightcolor=ACCENT)


def vytvor_button(parent, text, command, bg, hover, fg):
    """Ploché tlačidlo s hoverom, viditeľným fokusom a ovládaním klávesnicou."""
    if IS_MAC:
        # macOS ignoruje farby tlačidiel, preto použijeme natívny vzhľad
        b = tk.Button(parent, text=text, command=command)
    else:
        b = tk.Button(parent, text=text, command=command, font=FONT_BOLD,
                      bg=bg, fg=fg, activebackground=hover,
                      activeforeground=fg, relief="flat", bd=0,
                      padx=18, pady=9, cursor="hand2",
                      highlightthickness=2, highlightbackground=BG,
                      highlightcolor=NAVY)
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
    b.bind("<Return>", lambda e: b.invoke())   # Enter aktivuje tlačidlo
    return b


def styl_dlazdice(widget, vybrana):
    """Vzhľad dlaždice: vybraná je plná tyrkysová, ostatné sú svetlé."""
    if vybrana:
        widget.config(bg=ACCENT, fg="white", activebackground=ACCENT_DARK,
                      activeforeground="white", highlightbackground=ACCENT)
    else:
        widget.config(bg=FIELD, fg=TEXT, activebackground=SOFT,
                      activeforeground=TEXT, highlightbackground=BORDER)


def styl_volby():
    """Spoločné nastavenie dlaždíc (Radiobutton a Checkbutton bez štvorčeka)."""
    return dict(font=FONT_BOLD, indicatoron=False, selectcolor=ACCENT,
                relief="flat", offrelief="flat", overrelief="flat", bd=0,
                width=1, padx=8, pady=4, justify="center",
                highlightthickness=2, highlightcolor=NAVY,
                highlightbackground=BORDER, bg=FIELD, fg=TEXT,
                cursor="hand2")


# =====================================================================
#  HLAVIČKA
# =====================================================================
hlavicka = tk.Frame(root, bg=BG)
hlavicka.grid(row=0, column=0, columnspan=2, sticky="w", padx=28,
              pady=(14, 8))
tk.Label(hlavicka, text="Servis PC", font=FONT_TITLE, bg=BG,
         fg=NAVY).pack(side="left")
tk.Label(hlavicka, text="Objednávka opravy zariadenia", font=FONT_SUBTITLE,
         bg=BG, fg=MUTED).pack(side="left", anchor="s", padx=(14, 0),
                               pady=(0, 6))

lavy = tk.Frame(root, bg=BG)
pravy = tk.Frame(root, bg=BG)
lavy.grid(row=1, column=0, sticky="nsew", padx=(28, 12), pady=(0, 20))
pravy.grid(row=1, column=1, sticky="nsew", padx=(12, 28), pady=(0, 20))
root.columnconfigure(0, minsize=460)
root.columnconfigure(1, minsize=470)
root.rowconfigure(1, weight=1)

# =====================================================================
#  ĽAVÝ STĹPEC: ÚDAJE ZÁKAZNÍKA
# =====================================================================
k1, telo1, _ = karta(lavy, "Údaje zákazníka", "* povinné údaje")
k1.pack(fill="x", pady=(0, 8))
telo1.columnconfigure(0, weight=2, uniform="kontakt")
telo1.columnconfigure(1, weight=3, uniform="kontakt")
entry_meno = pole(telo1, "Meno a priezvisko *", 0)
entry_meno.grid_configure(columnspan=2)
entry_tel = pole(telo1, "Telefón *", 2, stlpec=0, posledne=True)
entry_email = pole(telo1, "E-mail", 2, stlpec=1, posledne=True)

# =====================================================================
#  ĽAVÝ STĹPEC: TYP ZARIADENIA + POČET  (Radiobutton ako dlaždice)
# =====================================================================
k2, telo2, _ = karta(lavy, "Typ zariadenia")
k2.pack(fill="x", pady=(0, 8))

dlazdice_zar = {}
for i, (nazov, cena) in enumerate(ZARIADENIA.items()):
    telo2.columnconfigure(i, weight=1, uniform="zariadenie")
    rb = tk.Radiobutton(telo2, text=f"{nazov}\n{cena} €",
                        variable=var_zariadenie, value=nazov, **styl_volby())
    rb.grid(row=0, column=i, sticky="ew", padx=(0, 8 if i < 2 else 0))
    dlazdice_zar[nazov] = rb

blok_pocet = tk.Frame(telo2, bg=CARD)
blok_pocet.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))
tk.Label(blok_pocet, text="Počet zariadení", font=FONT, bg=CARD,
         fg=TEXT).pack(side="left")
spin_pocet = tk.Spinbox(blok_pocet, from_=1, to=5, textvariable=var_pocet,
                        width=4, font=FONT_SPIN, justify="center",
                        state="readonly", readonlybackground=FIELD, fg=TEXT,
                        relief="flat", wrap=False, highlightthickness=1,
                        highlightbackground=INPUT_BORDER,
                        highlightcolor=ACCENT)
spin_pocet.pack(side="left", padx=(12, 0), ipady=4)
tk.Label(blok_pocet, text="od 1 do 5", font=FONT_SMALL, bg=CARD,
         fg=MUTED).pack(side="left", padx=(10, 0))

# =====================================================================
#  ĽAVÝ STĹPEC: DOPLNKOVÉ SLUŽBY  (Checkbutton ako dlaždice)
# =====================================================================
k3, telo3, _ = karta(lavy, "Doplnkové služby", "vyberte podľa potreby")
k3.pack(fill="x", pady=(0, 8))
telo3.columnconfigure(0, weight=1, uniform="sluzby")
telo3.columnconfigure(1, weight=1, uniform="sluzby")

dlazdice_sluzby = {}
for i, (nazov, cena) in enumerate(SLUZBY.items()):
    cb = tk.Checkbutton(telo3, text=f"{nazov}\n+{cena} €",
                        variable=var_sluzby[nazov], **styl_volby())
    cb.grid(row=i // 2, column=i % 2, sticky="ew",
            padx=(0, 8 if i % 2 == 0 else 0),
            pady=(0, 6 if i // 2 == 0 else 0))
    dlazdice_sluzby[nazov] = cb


def obnov_volby(*_):
    """Prekreslí dlaždice podľa aktuálnych hodnôt premenných."""
    vybrane = var_zariadenie.get()
    for nazov, w in dlazdice_zar.items():
        styl_dlazdice(w, nazov == vybrane)
    for nazov, w in dlazdice_sluzby.items():
        zapnute = var_sluzby[nazov].get()
        styl_dlazdice(w, zapnute)
        w.config(text=("✓  " if zapnute else "") + nazov
                 + f"\n+{SLUZBY[nazov]} €")


# =====================================================================
#  ĽAVÝ STĹPEC: POPIS PORUCHY
# =====================================================================
k4, telo4, label_pocitadlo = karta(lavy, "Popis poruchy",
                                   f"0 / {MAX_POPIS}")
k4.pack(fill="x")
text_porucha = tk.Text(telo4, height=4, width=10, font=FONT, bg=FIELD,
                       fg=TEXT, relief="flat", bd=0, wrap="word",
                       padx=8, pady=6, undo=True, highlightthickness=1,
                       highlightbackground=INPUT_BORDER,
                       highlightcolor=ACCENT, insertbackground=TEXT)
text_porucha.pack(fill="x")


def pocitadlo(event=None):
    """Obmedzí dĺžku popisu a aktualizuje počítadlo znakov."""
    obsah = text_porucha.get("1.0", "end-1c")
    if len(obsah) > MAX_POPIS:
        text_porucha.delete(f"1.0+{MAX_POPIS}c", "end-1c")
        obsah = text_porucha.get("1.0", "end-1c")
    label_pocitadlo.config(text=f"{len(obsah)} / {MAX_POPIS}")


def dalsie_pole(event):
    event.widget.tk_focusNext().focus_set()
    return "break"          # v Text poli Tab nevkladá tabulátor


def predchadzajuce_pole(event):
    event.widget.tk_focusPrev().focus_set()
    return "break"


text_porucha.bind("<KeyRelease>", pocitadlo)
for udalost in ("<<Paste>>", "<<Cut>>", "<<PasteSelection>>",
                "<<Undo>>", "<<Redo>>"):
    text_porucha.bind(udalost, lambda e: root.after_idle(pocitadlo))
text_porucha.bind("<Tab>", dalsie_pole)
text_porucha.bind("<Shift-Tab>", predchadzajuce_pole)
try:
    text_porucha.bind("<ISO_Left_Tab>", predchadzajuce_pole)   # Linux
except tk.TclError:
    pass

# =====================================================================
#  PRAVÝ STĹPEC: PANEL S CENOU (aktualizuje sa hneď pri každej zmene)
# =====================================================================
panel_ceny = tk.Frame(pravy, bg=NAVY)
panel_ceny.pack(fill="x")
panel_ceny.columnconfigure(0, weight=1)
tk.Label(panel_ceny, text="Cena spolu", font=FONT_SMALL, bg=NAVY,
         fg=NAVY_TEXT).grid(row=0, column=0, sticky="w", padx=18,
                            pady=(12, 0))
label_cena = tk.Label(panel_ceny, text="", font=FONT_PRICE, bg=NAVY,
                      fg="white")
label_cena.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))
label_vzorec = tk.Label(panel_ceny, text="", font=FONT_SMALL, bg=NAVY,
                        fg=NAVY_TEXT)
label_vzorec.grid(row=1, column=1, sticky="se", padx=18, pady=(0, 16))


def vypocitaj_cenu():
    """(cena zariadenia + súčet služieb) x počet zariadení."""
    zariadenie = var_zariadenie.get()
    cena_zar = ZARIADENIA[zariadenie]
    vybrane = [(n, c) for n, c in SLUZBY.items() if var_sluzby[n].get()]
    cena_sluzieb = sum(c for _, c in vybrane)
    try:
        pocet = var_pocet.get()
    except tk.TclError:
        pocet = 1
    return {
        "zariadenie": zariadenie,
        "cena_zar": cena_zar,
        "sluzby": vybrane,
        "cena_sluzieb": cena_sluzieb,
        "jednotka": cena_zar + cena_sluzieb,
        "pocet": pocet,
        "celkom": (cena_zar + cena_sluzieb) * pocet,
    }


def aktualizuj_cenu(*_):
    c = vypocitaj_cenu()
    label_cena.config(text=f"{c['celkom']} €")
    label_vzorec.config(
        text=f"({c['cena_zar']} + {c['cena_sluzieb']}) × {c['pocet']}")


# =====================================================================
#  PRAVÝ STĹPEC: TLAČIDLÁ, STAV, VÝSTUP
# =====================================================================
frame_btn = tk.Frame(pravy, bg=BG)
frame_btn.pack(fill="x", pady=(12, 0))

# width=1: štítok nikdy nerozšíri stĺpec; zalamovanie sa prispôsobí šírke
label_stav = tk.Label(pravy, text="", font=FONT_BOLD, bg=BG, fg=ERROR,
                      anchor="nw", justify="left", width=1, height=2)
label_stav.pack(fill="x", pady=(8, 0))
label_stav.bind("<Configure>",
                lambda e: label_stav.config(wraplength=max(e.width - 4, 50)))

frame_vystup = tk.Frame(pravy, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
frame_vystup.pack(fill="both", expand=True, pady=(4, 0))
vystup = tk.Text(frame_vystup, height=6, width=10, font=FONT, bg=CARD,
                 fg=TEXT, relief="flat", bd=0, highlightthickness=0,
                 padx=PADX_VYSTUP, pady=12, wrap="word", state="disabled",
                 cursor="arrow", spacing1=1, spacing3=1)
skrol = ttk.Scrollbar(frame_vystup, orient="vertical", command=vystup.yview)
vystup.configure(yscrollcommand=skrol.set)
skrol.pack(side="right", fill="y")
vystup.pack(side="left", fill="both", expand=True)

# štýly textu vo výstupe
vystup.tag_configure("nadpis", font=(FAM, 14, "bold"), foreground=NAVY)
vystup.tag_configure("tlumene", foreground=MUTED)
vystup.tag_configure("maly", font=FONT_SMALL, foreground=MUTED)
vystup.tag_configure("hrube", font=FONT_BOLD)
vystup.tag_configure("spolu", font=(FAM, 15, "bold"), foreground=ACCENT)
vystup.tag_configure("ciara", font=(FAM, 2), spacing1=0, spacing3=0)


def nastav_tabulator(event):
    """Pravý tabulátor drží ceny zarovnané na pravý okraj výstupu."""
    vystup.configure(tabs=(max(event.width - 2 * PADX_VYSTUP - 6, 100),
                           "right"))


vystup.bind("<Configure>", nastav_tabulator)


def pis(text, *tagy):
    vystup.insert("end", text, tagy)


def riadok(popis, hodnota):
    pis(popis, "tlumene")
    pis("\t" + hodnota + "\n")


def ciara():
    """Tenká vodorovná čiara (vložený Frame výšky 1 px)."""
    sirka = max(vystup.winfo_width() - 2 * PADX_VYSTUP - 6, 100)
    zaciatok = vystup.index("end-1c")
    vystup.window_create(
        "end", pady=5,
        window=tk.Frame(vystup, width=sirka, height=1, bg=BORDER))
    pis("\n")
    vystup.tag_add("ciara", zaciatok, "end-1c")


def zobraz_prazdny():
    """Prázdny stav výstupu: čo tu bude a ako to vyvolať."""
    vystup.config(state="normal")
    vystup.delete("1.0", "end")
    pis("Zatiaľ žiadna objednávka\n", "hrube")
    pis("Vyplňte formulár a kliknite na Odoslať objednávku. Prehľad a cenu "
        "uvidíte tu. Skratka: Ctrl + Enter.", "tlumene")
    vystup.config(state="disabled")


# =====================================================================
#  KONTROLA VSTUPU
# =====================================================================
def telefon_ok(telefon):
    if not re.fullmatch(r"\+?[\d\s()/\-]+", telefon):
        return False
    return 9 <= len(re.sub(r"\D", "", telefon)) <= 15


def email_ok(email):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", email) is not None


# =====================================================================
#  FUNKCIE TLAČIDIEL
# =====================================================================
def odoslat(event=None):
    global cislo_objednavky

    meno = entry_meno.get().strip()
    telefon = entry_tel.get().strip()
    email = entry_email.get().strip()
    porucha = text_porucha.get("1.0", "end-1c").strip()[:MAX_POPIS]

    for e in (entry_meno, entry_tel, entry_email):
        oznac_chybu(e, False)

    # ---- kontrola vstupu ----
    problemy = []
    if not meno:
        problemy.append(entry_meno)
    if not telefon:
        problemy.append(entry_tel)

    sprava = ""
    if len(problemy) == 2:
        sprava = ("Chýba meno a telefón. Vyplňte polia označené "
                  "hviezdičkou (*).")
    elif problemy and not meno:
        sprava = "Chýba meno a priezvisko. Vyplňte ho, aby sme vedeli, " \
                 "na koho objednávku vystaviť."
    elif problemy:
        sprava = "Chýba telefón. Zadajte číslo, na ktorom vás zastihneme."
    elif not telefon_ok(telefon):
        problemy = [entry_tel]
        sprava = ("Telefónne číslo nie je platné. Zadajte 9 až 15 číslic, "
                  "napríklad +421 900 123 456.")
    elif email and not email_ok(email):
        problemy = [entry_email]
        sprava = "E-mail nemá správny tvar. Skúste napríklad meno@domena.sk."

    if problemy:
        for e in problemy:
            oznac_chybu(e, True)
        problemy[0].focus_set()
        label_stav.config(text=sprava, fg=ERROR)
        zobraz_prazdny()          # neplatná objednávka sa nevypíše
        return

    # ---- výpočet a prehľad ----
    cislo_objednavky += 1
    teraz = datetime.now()
    cislo = f"SP-{teraz:%y%m%d}-{cislo_objednavky:03d}"
    c = vypocitaj_cenu()

    vystup.config(state="normal")
    vystup.delete("1.0", "end")
    pis(f"Objednávka {cislo}\n", "nadpis")
    pis(f"{teraz.day}. {teraz.month}. {teraz.year}, {teraz:%H:%M}\n",
        "tlumene")
    ciara()

    riadok("Meno", meno)
    riadok("Telefón", telefon)
    riadok("E-mail", email if email else "neuvedený")
    ciara()

    pis(f"{c['zariadenie']}\t{c['cena_zar']} €\n")
    if c["sluzby"]:
        for nazov, cena in c["sluzby"]:
            pis(f"{nazov}\t+{cena} €\n")
    else:
        pis("Bez doplnkových služieb\n", "tlumene")
    riadok("Počet zariadení", f"{c['pocet']} × {c['jednotka']} €")
    ciara()

    pis("Popis poruchy\n", "tlumene")
    if porucha:
        pis(porucha + "\n")
    else:
        pis("Bez popisu\n", "tlumene")
    ciara()

    pis(f"Cena spolu\t{c['celkom']} €\n", "spolu")
    pis(f"({c['cena_zar']} + {c['cena_sluzieb']}) × {c['pocet']} = "
        f"{c['celkom']} €\n", "maly")
    vystup.config(state="disabled")
    vystup.yview_moveto(0)

    label_stav.config(
        text=f"Objednávka {cislo} bola odoslaná. Prehľad nájdete nižšie.",
        fg=OK)


def vymazat():
    """Vráti formulár do pôvodného stavu."""
    entry_meno.delete(0, "end")
    entry_tel.delete(0, "end")
    entry_email.delete(0, "end")
    for e in (entry_meno, entry_tel, entry_email):
        oznac_chybu(e, False)
    text_porucha.delete("1.0", "end")
    pocitadlo()
    var_zariadenie.set(PREDVOLENE_ZARIADENIE)
    for v in var_sluzby.values():
        v.set(False)
    var_pocet.set(1)
    aktualizuj_cenu()
    label_stav.config(text="")
    zobraz_prazdny()
    entry_meno.focus_set()


# ---------- Tlačidlá (vytvorené v poradí, v akom sa cez ne chodí Tabom) ----------
btn_odoslat = vytvor_button(frame_btn, "Odoslať objednávku", odoslat,
                            ACCENT, ACCENT_DARK, "white")
btn_vymazat = vytvor_button(frame_btn, "Vymazať", vymazat, SOFT,
                            SOFT_HOVER, TEXT)
btn_koniec = vytvor_button(frame_btn, "Koniec", root.destroy, SOFT,
                           SOFT_HOVER, TEXT)
btn_odoslat.pack(side="left")
btn_koniec.pack(side="right")
btn_vymazat.pack(side="right", padx=(0, 8))

# =====================================================================
#  PREPOJENIA A ŠTART
# =====================================================================
# cena sa prepočíta pri každej zmene voľby
var_zariadenie.trace_add("write", aktualizuj_cenu)
var_zariadenie.trace_add("write", obnov_volby)
var_pocet.trace_add("write", aktualizuj_cenu)
for v in var_sluzby.values():
    v.trace_add("write", aktualizuj_cenu)
    v.trace_add("write", obnov_volby)

# Ctrl+Enter odošle objednávku aj z Text poľa (bez vloženia nového riadku)
root.bind("<Control-Return>", odoslat)
text_porucha.bind("<Control-Return>", lambda e: (odoslat(), "break")[1])

aktualizuj_cenu()
obnov_volby()
zobraz_prazdny()

# okno sa prispôsobí obsahu, zafixuje sa a vycentruje na obrazovke
root.update_idletasks()
sirka, vyska = root.winfo_reqwidth(), root.winfo_reqheight()
x = (root.winfo_screenwidth() - sirka) // 2
y = max((root.winfo_screenheight() - vyska) // 2 - 20, 0)
root.geometry(f"{sirka}x{vyska}+{x}+{y}")
entry_meno.focus_set()

root.mainloop()