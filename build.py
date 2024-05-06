import click
import os
import subprocess
import shutil
import shlex

CPU_COUNT = os.cpu_count() or 1
N_JOBS = max(1, CPU_COUNT - 2)
BINDIR = os.path.join(os.path.dirname(__file__), "bin")


def get_default_platform():
    import sys

    if (
        sys.platform.startswith("linux")
        or sys.platform.startswith("dragonfly")
        or sys.platform.startswith("freebsd")
        or sys.platform.startswith("netbsd")
        or sys.platform.startswith("openbsd")
    ):
        return "linuxbsd"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"


def copy_artifact(name, dir):
    artifact = os.path.join(BINDIR, name)
    assert os.path.exists(artifact), f"Artifact {artifact} does not exist"
    assert os.path.exists(dir), f"{dir} does not exist"
    assert os.path.isdir(dir), f"{dir} is not a directory"
    shutil.copy(artifact, dir)


@click.group(help="Build helper script")
def cli():
    pass


@click.command(help="Sync remote master, pull, then merge to custom-build")
def sync():
    subprocess.run(["gh", "repo", "sync", "billuo/godot", "-b", "master"], check=True)
    subprocess.run(["git", "checkout", "master"], check=True)
    subprocess.run(["git", "pull"], check=True)
    subprocess.run(["git", "checkout", "custom-build"], check=True)
    subprocess.run(["git", "merge", "master"], check=True)


@click.command(help="Build targets on branch")
@click.option("-b", "--branch", help="Branch in which to build", default="custom-build", show_default=True)
@click.option("-t", "--target", help="Targets to build", default=["editor"], show_default=True, multiple=True)
@click.option("--platform", help="Platform for which to build", default=get_default_platform())
@click.option("--dry", help="Dry run; only print the command to be run", is_flag=True)
@click.argument("scons-args", nargs=-1)
def build(branch, target, platform, dry, scons_args):
    subprocess.run(["git", "checkout", branch], check=True)
    default_args = [f"-j{N_JOBS}", "compiledb=no", "debug_symbols=yes", "separate_debug_symbols=yes"]
    if platform:
        default_args.append(f"platform={platform}")
    for t in target:
        cmd = ["scons", *default_args, f"target={t}", *scons_args]
        print("Command to run: %s" % " ".join(map(shlex.quote, cmd)))
        if not dry:
            subprocess.run(cmd, check=True)


@click.command(help="Helper for building all useful targets")
def build_all():
    subprocess.run(["python3", "build.py", "sync"], check=True)

    # TODO: automatically copy artifacts
    # artifact_name = f"godot.{platform}.{t}.{arch}.{extension}"
    DEFAULT_PLATFORM = get_default_platform()
    GODOT_EXPORT_TEMPLATES = ""
    match DEFAULT_PLATFORM:
        case "linuxbsd":
            GODOT_EXPORT_TEMPLATES = ""
        case "windows":
            GODOT_EXPORT_TEMPLATES = os.environ["APPDATA"]

    # editor
    subprocess.run(["python3", "build.py", "build", "compiledb=yes"], check=True)
    # export templates
    subprocess.run(["python3", "build.py", "build", "--target=template_debug", "--target=template_release"], check=True)
    copy_artifact(f"godot.{DEFAULT_PLATFORM}.template_debug.64.zip", GODOT_EXPORT_TEMPLATES)
    # web export templates
    subprocess.run(
        [
            "python3",
            "build.py",
            "build",
            "--platform=web",
            "--target=template_debug",
            "--target=template_release",
            "optimize=size",
            "debug_symbols=no",
            "thread=yes",
            "lto=thin",
        ],
        check=True,
    )
    # android export templates
    subprocess.run(
        [
            "python3",
            "build.py",
            "build",
            "--platform=android",
            "--target=template_debug",
            "--target=template_release",
            "arch=arm32",
        ],
        check=True,
    )
    subprocess.run(
        [
            "python3",
            "build.py",
            "build",
            "--platform=android",
            "--target=template_debug",
            "--target=template_release",
            "arch=arm64",
        ],
        check=True,
    )


cli.add_command(sync)
cli.add_command(build)
cli.add_command(build_all)

if __name__ == "__main__":
    cli()
