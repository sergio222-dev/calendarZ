#!/usr/bin/env python3
"""Hook the calendarz plugin into an illogical-impulse (ii) quickshell config.

ii has no plugin system and its updater runs `rsync --delete` over
~/.config/quickshell/ii, so this script re-applies the (tiny) integration:

  1. symlink  ii/calendarz -> ./plugin
  2. four marker-tagged lines in two ii files (each ends with `// calendarz`)

Usage: install.py [apply|status|remove] [--quiet]   (apply is the default, idempotent)
"""
import os
import sys

II = os.path.expanduser(os.environ.get("CALENDARZ_II_DIR", "~/.config/quickshell/ii"))
PLUGIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin")
LINK = os.path.join(II, "calendarz")
MARK = "// calendarz"

# (file, anchor line (stripped), where to insert relative to it, line to insert)
PATCHES = [
    ("panelFamilies/IllogicalImpulseFamily.qml", "import qs.modules.ii.background", "after",
     f"import qs.calendarz {MARK}"),
    ("panelFamilies/IllogicalImpulseFamily.qml", "PanelLoader { component: Background {} }", "after",
     f"PanelLoader {{ component: CalendarAlert {{}} }} {MARK}"),
    ("modules/ii/bar/BarContent.qml", "import qs.modules.common.functions", "after",
     f"import qs.calendarz {MARK}"),
    ("modules/ii/bar/BarContent.qml", "// Weather", "before",
     f"MeetingsBar {{}} {MARK}"),
]


def log(msg, quiet):
    if not quiet:
        print(msg)


def patch_file(rel, patches, quiet):
    path = os.path.join(II, rel)
    with open(path) as f:
        lines = f.read().split("\n")
    changed = False
    for _, anchor, where, new in patches:
        if any(l.strip() == new for l in lines):
            continue
        idx = next((i for i, l in enumerate(lines) if l.strip() == anchor), None)
        if idx is None:
            raise SystemExit(f"anchor not found in {rel}: {anchor!r} "
                             "(ii changed upstream; update PATCHES in install.py)")
        indent = lines[idx][: len(lines[idx]) - len(lines[idx].lstrip())]
        lines.insert(idx + (1 if where == "after" else 0), indent + new)
        changed = True
    if changed:
        with open(path, "w") as f:
            f.write("\n".join(lines))
        log(f"patched {rel}", quiet)


def apply(quiet):
    if not os.path.isdir(II):
        raise SystemExit(f"ii config not found: {II}")
    if os.path.islink(LINK):
        if os.path.realpath(LINK) != os.path.realpath(PLUGIN):
            os.remove(LINK)
    elif os.path.exists(LINK):
        raise SystemExit(f"{LINK} exists and is not a symlink; refusing to touch it")
    if not os.path.lexists(LINK):
        os.symlink(PLUGIN, LINK)
        log(f"linked {LINK} -> {PLUGIN}", quiet)
    for rel in dict.fromkeys(p[0] for p in PATCHES):
        patch_file(rel, [p for p in PATCHES if p[0] == rel], quiet)


def state():
    link = os.path.islink(LINK) and os.path.realpath(LINK) == os.path.realpath(PLUGIN)
    patched = {}
    for rel, _, _, new in PATCHES:
        with open(os.path.join(II, rel)) as f:
            patched[(rel, new)] = any(l.strip() == new for l in f.read().split("\n"))
    return link, patched


def status():
    link, patched = state()
    print(f"symlink: {'ok' if link else 'MISSING'}")
    for (rel, new), ok in patched.items():
        print(f"{'ok     ' if ok else 'MISSING'} {rel}: {new}")
    return link and all(patched.values())


def remove(quiet):
    if os.path.islink(LINK):
        os.remove(LINK)
        log(f"removed {LINK}", quiet)
    for rel in dict.fromkeys(p[0] for p in PATCHES):
        path = os.path.join(II, rel)
        with open(path) as f:
            lines = f.read().split("\n")
        kept = [l for l in lines if not l.rstrip().endswith(MARK)]
        if kept != lines:
            with open(path, "w") as f:
                f.write("\n".join(kept))
            log(f"unpatched {rel}", quiet)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    cmd = args[0] if args else "apply"
    if cmd == "apply":
        apply(quiet)
    elif cmd == "status":
        sys.exit(0 if status() else 1)
    elif cmd == "remove":
        remove(quiet)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
