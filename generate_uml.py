"""
generate_uml.py
Renders a UML class diagram for PawPal+ and saves it as uml_final.png.

Phase 3 additions are marked with ★ in the Scheduler methods section.

Run:  python3 generate_uml.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── Colour palette ─────────────────────────────────────────────────────────────
C_HEADER  = "#1e3a5f"   # dark navy  – class name banner
C_ATTR    = "#dce8f8"   # light blue – attributes section
C_METHOD  = "#f4f7fb"   # near-white – methods section
C_BORDER  = "#2c4d7a"   # mid-navy   – box borders
C_NEW     = "#0d6e35"   # dark green – Phase-3 additions (★)
C_BG      = "#ffffff"   # white background

LINE_H    = 0.30   # height of each text row
PAD       = 0.18   # internal vertical padding per section
HDR_H     = 0.52   # height of class-name banner
FONT_SIZE = 7.8
FONT_MONO = "monospace"

# ── Helper: draw one class box ─────────────────────────────────────────────────

def draw_class(ax, x, y_top, width, name, stereotype, attrs, methods):
    """Draw a UML class box.  Returns the y coordinate of the bottom edge.

    args
        x, y_top   — top-left corner in data coordinates
        width      — box width
        name       — class name (shown in header)
        stereotype — e.g. "«dataclass»" or "" (shown above name)
        attrs      — list of strings for the attributes section
        methods    — list of (text, is_new) tuples; is_new=True → green ★
    """
    def rect(ax, lx, ly, w, h, fc, ec):
        ax.add_patch(mpatches.FancyBboxPatch(
            (lx, ly), w, h,
            boxstyle="square,pad=0",
            facecolor=fc, edgecolor=ec, linewidth=1.3, zorder=3
        ))

    cur_y = y_top

    # ── header ──
    rect(ax, x, cur_y - HDR_H, width, HDR_H, C_HEADER, C_BORDER)
    if stereotype:
        ax.text(x + width / 2, cur_y - 0.13, stereotype,
                ha="center", va="center", fontsize=6.5,
                color="#aecbf0", fontstyle="italic", zorder=4)
        name_y = cur_y - HDR_H + 0.14
    else:
        name_y = cur_y - HDR_H / 2
    ax.text(x + width / 2, name_y, name,
            ha="center", va="center", fontsize=9.5,
            fontweight="bold", color="white", fontfamily=FONT_MONO, zorder=4)
    cur_y -= HDR_H

    # ── attributes ──
    attr_h = PAD + len(attrs) * LINE_H + PAD / 2
    rect(ax, x, cur_y - attr_h, width, attr_h, C_ATTR, C_BORDER)
    for i, text in enumerate(attrs):
        ty = cur_y - PAD - (i + 0.5) * LINE_H
        ax.text(x + 0.12, ty, text, ha="left", va="center",
                fontsize=FONT_SIZE, fontfamily=FONT_MONO, color="#1a1a2e", zorder=4)
    cur_y -= attr_h

    # thin divider line
    ax.plot([x, x + width], [cur_y, cur_y], color=C_BORDER, lw=0.8, zorder=4)

    # ── methods ──
    meth_h = PAD + len(methods) * LINE_H + PAD / 2
    rect(ax, x, cur_y - meth_h, width, meth_h, C_METHOD, C_BORDER)
    for i, (text, is_new) in enumerate(methods):
        ty = cur_y - PAD - (i + 0.5) * LINE_H
        color = C_NEW if is_new else "#1a1a2e"
        label = ("★ " if is_new else "  ") + text
        ax.text(x + 0.12, ty, label, ha="left", va="center",
                fontsize=FONT_SIZE, fontfamily=FONT_MONO, color=color, zorder=4)
    cur_y -= meth_h

    return cur_y   # bottom y of the drawn box


# ── Helper: draw a relationship arrow ──────────────────────────────────────────

def draw_arrow(ax, x1, y1, x2, y2, style="->", dashed=False, label="", label_offset=(0, 0.18)):
    ls = (0, (4, 3)) if dashed else "solid"
    arrowprops = dict(
        arrowstyle=style,
        color=C_BORDER,
        lw=1.4,
        linestyle=ls,
        connectionstyle="arc3,rad=0.0",
    )
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=arrowprops, zorder=5)
    if label:
        mx = (x1 + x2) / 2 + label_offset[0]
        my = (y1 + y2) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="bottom",
                fontsize=7, fontstyle="italic", color="#444", zorder=6)


# ── Figure setup ───────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(22, 18))
ax.set_xlim(0, 22)
ax.set_ylim(0, 18)
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor(C_BG)

# ── Class data ─────────────────────────────────────────────────────────────────

TASK_ATTRS = [
    "+ description: str",
    "+ duration: int  # minutes",
    '+ frequency: Literal["daily"|"weekly"|"as needed"]',
    '+ priority: Literal["low"|"medium"|"high"]',
    '+ time: str = "00:00"  # HH:MM',
    "+ completed: bool = False",
]
TASK_METHODS = [
    ("mark_complete()", False),
    ("mark_incomplete()", False),
    ("__str__() → str", False),
]

PET_ATTRS = [
    "+ name: str",
    "+ species: str",
    "+ age: int",
    "+ tasks: list[Task]",
]
PET_METHODS = [
    ("add_task(task: Task)", False),
    ("remove_task(description: str) → bool", False),
    ("get_tasks() → list[Task]", False),
    ("get_pending_tasks() → list[Task]", False),
    ("total_task_time() → int", False),
    ("__str__() → str", False),
]

OWNER_ATTRS = [
    "+ name: str",
    "+ available_minutes: int",
    "+ pets: list[Pet]",
]
OWNER_METHODS = [
    ("add_pet(pet: Pet)", False),
    ("remove_pet(name: str) → bool", False),
    ("get_all_tasks() → list[Task]", False),
    ("get_all_pending_tasks() → list[Task]", False),
    ("summary() → str", False),
]

SCHED_ATTRS = [
    "+ PRIORITY_ORDER: dict",
    "+ FREQUENCY_ORDER: dict",
    "+ owner: Owner",
    "+ scheduled: list[Task]",
    "+ skipped: list[Task]",
]
SCHED_METHODS = [
    # (text, is_phase3_addition)
    ("build_schedule() → list[Task]  # 2nd-pass bin-packing added", False),
    ("mark_task_complete(description: str) → bool", False),
    ("renew_recurring_tasks() → list[Task]", True),
    ("get_tasks_by_priority(priority) → list[Task]", False),
    ("get_tasks_by_frequency(frequency) → list[Task]", False),
    ("get_tasks_sorted_by_duration(ascending) → list[Task]", True),
    ("sort_by_time(ascending) → list[Task]", True),
    ("get_tasks_by_pet(pet_name) → list[Task]", True),
    ("get_tasks_by_status(completed) → list[Task]", True),
    ("filter_tasks(pet_name, completed) → list[Task]", True),
    ("get_recurring_summary() → dict[str, list[Task]]", True),
    ("detect_conflicts() → list[str]", True),
    ("total_time_scheduled() → int", False),
    ("explain() → str", False),
]

# ── Draw classes ───────────────────────────────────────────────────────────────
#
#   Top row (left → right):  Task  |  Pet  |  Owner
#   Bottom:                     Scheduler (full width)

TOP_Y     = 17.2
COL_W     = 6.5    # width of each top-row class box
SCHED_W   = 20.5   # full-width scheduler box
GAP       = 0.55   # horizontal gap between top boxes

task_x  = 0.5
pet_x   = task_x + COL_W + GAP
owner_x = pet_x  + COL_W + GAP

task_bottom  = draw_class(ax, task_x,  TOP_Y, COL_W, "Task",  "«dataclass»", TASK_ATTRS,  TASK_METHODS)
pet_bottom   = draw_class(ax, pet_x,   TOP_Y, COL_W, "Pet",   "«dataclass»", PET_ATTRS,   PET_METHODS)
owner_bottom = draw_class(ax, owner_x, TOP_Y, COL_W, "Owner", "",             OWNER_ATTRS, OWNER_METHODS)

# Scheduler sits below the tallest top-row box, with a gap
sched_top_y = min(task_bottom, pet_bottom, owner_bottom) - 0.9
sched_bottom = draw_class(ax, 0.5, sched_top_y, SCHED_W, "Scheduler", "", SCHED_ATTRS, SCHED_METHODS)

# ── Relationships ──────────────────────────────────────────────────────────────

# 1. Pet ──◆──► Task  (composition: Pet contains list[Task])
#    Arrow from Pet left edge → Task right edge, at vertical midpoint of both headers
pet_arrow_y   = TOP_Y - HDR_H / 2
task_arrow_y  = TOP_Y - HDR_H / 2
draw_arrow(ax,
           pet_x,           pet_arrow_y,
           task_x + COL_W,  task_arrow_y,
           style="-|>", label="contains  list[Task]", label_offset=(0, 0.15))

# 2. Owner ──◆──► Pet  (composition)
draw_arrow(ax,
           owner_x,         pet_arrow_y,
           pet_x + COL_W,   pet_arrow_y,
           style="-|>", label="owns  list[Pet]", label_offset=(0, 0.15))

# 3. Scheduler ──────► Owner  (association: Scheduler uses Owner)
#    From top of Scheduler, right side → bottom of Owner box
sched_own_x = owner_x + COL_W * 0.55    # point on scheduler top edge below Owner
draw_arrow(ax,
           sched_own_x,  sched_top_y,
           owner_x + COL_W * 0.55, owner_bottom,
           style="-|>", label="uses", label_offset=(0.55, 0.12))

# 4. Scheduler ─ ─ ─ ► Task  (dependency: manages scheduled/skipped lists)
sched_task_x = task_x + COL_W * 0.55
draw_arrow(ax,
           sched_task_x, sched_top_y,
           sched_task_x, task_bottom,
           style="-|>", dashed=True,
           label="manages (scheduled / skipped)", label_offset=(-1.6, 0.12))

# ── Legend ─────────────────────────────────────────────────────────────────────

leg_x, leg_y = 0.5, sched_bottom - 0.35
ax.text(leg_x, leg_y, "Legend:", fontsize=8, fontweight="bold", color="#333", zorder=6)
ax.plot([leg_x + 1.0, leg_x + 1.6], [leg_y - 0.22, leg_y - 0.22],
        color=C_BORDER, lw=1.4, zorder=6)
ax.annotate("", xy=(leg_x + 1.6, leg_y - 0.22), xytext=(leg_x + 1.3, leg_y - 0.22),
            arrowprops=dict(arrowstyle="-|>", color=C_BORDER, lw=1.4), zorder=6)
ax.text(leg_x + 1.7, leg_y - 0.22, "Association / Composition",
        fontsize=7.5, va="center", color="#333", zorder=6)

ax.plot([leg_x + 4.8, leg_x + 5.4], [leg_y - 0.22, leg_y - 0.22],
        color=C_BORDER, lw=1.4, linestyle=(0, (4, 3)), zorder=6)
ax.annotate("", xy=(leg_x + 5.4, leg_y - 0.22), xytext=(leg_x + 5.1, leg_y - 0.22),
            arrowprops=dict(arrowstyle="-|>", color=C_BORDER, lw=1.4,
                            linestyle=(0, (4, 3))), zorder=6)
ax.text(leg_x + 5.5, leg_y - 0.22, "Dependency (manages tasks)",
        fontsize=7.5, va="center", color="#333", zorder=6)

# Green star legend
ax.text(leg_x + 9.0, leg_y - 0.22, "★", fontsize=9, color=C_NEW,
        va="center", zorder=6)
ax.text(leg_x + 9.4, leg_y - 0.22, "= Added in Phase 3 (sorting, filtering, recurrence, conflict detection)",
        fontsize=7.5, va="center", color=C_NEW, zorder=6)

# ── Title ──────────────────────────────────────────────────────────────────────

ax.text(11.25, 17.75, "PawPal+  —  Final UML Class Diagram",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=C_HEADER, zorder=6)

# ── Save ───────────────────────────────────────────────────────────────────────

out_path = "uml_final.png"
plt.savefig(out_path, dpi=160, bbox_inches="tight",
            facecolor=C_BG, edgecolor="none")
plt.close()
print(f"Saved → {out_path}")
