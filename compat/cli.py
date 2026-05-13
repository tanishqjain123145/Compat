"""
compat CLI - manage cached runtime environments.
by Tanishq Jain

Usage:
    compat list                          List all cached runtimes
    compat invalidate <requirements>     Delete a cached runtime (force rebuild)
    compat clear                         Delete ALL cached runtimes
"""

import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "list":
        _cmd_list()
    elif cmd == "invalidate":
        if len(args) < 2:
            print("Usage: compat invalidate <requirements.txt>", file=sys.stderr)
            sys.exit(1)
        _cmd_invalidate(args[1])
    elif cmd == "clear":
        _cmd_clear()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Run 'compat --help' for usage.", file=sys.stderr)
        sys.exit(1)


def _cmd_list():
    from compat.manager import RuntimeManager

    mgr = RuntimeManager()
    runtimes = mgr.list_runtimes()
    if not runtimes:
        print("No cached runtimes.")
        return
    print(f"{'NAME':<50}  {'SIZE':>8}  {'STATUS'}")
    print("-" * 70)
    for runtime in runtimes:
        status = "ready" if runtime["ready"] else "BROKEN"
        print(f"{runtime['name']:<50}  {runtime['size_mb']:>6.1f}MB  {status}")
    total = sum(runtime["size_mb"] for runtime in runtimes)
    print(f"\n{len(runtimes)} runtime(s), {total:.1f} MB total")


def _cmd_invalidate(req_path: str):
    from compat.manager import RuntimeManager

    mgr = RuntimeManager()
    mgr.invalidate(req_path)


def _cmd_clear():
    import shutil

    from compat.manager import RuntimeManager

    mgr = RuntimeManager()
    runtimes = mgr.list_runtimes()
    if not runtimes:
        print("Nothing to clear.")
        return
    total_mb = sum(runtime["size_mb"] for runtime in runtimes)
    confirm = input(
        f"Delete {len(runtimes)} runtime(s) ({total_mb:.1f} MB)? [y/N] "
    ).strip().lower()
    if confirm != "y":
        print("Aborted.")
        return
    shutil.rmtree(mgr.base_dir)
    mgr.base_dir.mkdir(parents=True, exist_ok=True)
    print(f"Cleared {len(runtimes)} runtime(s).")


if __name__ == "__main__":
    main()
