import shlex
import shutil
import subprocess

from . import BINDIR, N_JOBS, VERSION
from .godot import get_current_platform, get_editor_data_path


def copy_export_template(artifact_name, template_name):
    artifact = BINDIR.joinpath(artifact_name)
    export_templates = get_editor_data_path() / "export_templates" / VERSION
    assert artifact.exists(), f"Artifact ({artifact}) does not exist"
    assert artifact.is_file(), f"Artifact ({artifact}) is not a file"
    assert export_templates.exists(), f"Export templates directory ({export_templates}) does not exist"
    assert export_templates.is_dir(), f"Export templates directory ({export_templates}) is not a directory"
    print("Copying %s to %s" % (artifact, export_templates / template_name))
    shutil.copy(artifact, export_templates / template_name)


def sync():
    subprocess.run(["gh", "repo", "sync", "billuo/godot", "-b", "master"], check=True)
    subprocess.run(["git", "checkout", "master"], check=True)
    subprocess.run(["git", "pull"], check=True)
    subprocess.run(["git", "checkout", "custom-build"], check=True)
    subprocess.run(["git", "merge", "master"], check=True)


def build(target=["editor"], platform=get_current_platform(), branch=None, dry=False, scons_args=[]):
    if branch:
        subprocess.run(["git", "checkout", branch], check=True)
    default_args = [f"-j{N_JOBS}", "compiledb=no", "debug_symbols=yes", "separate_debug_symbols=yes"]
    if platform:
        default_args.append(f"platform={platform}")
    for t in target:
        cmd = ["scons", *default_args, f"target={t}", *scons_args]
        print("Command to run: %s" % " ".join(map(shlex.quote, cmd)))
        if not dry:
            subprocess.run(cmd, check=True)


def copy(target):
    for t in target:
        if t.startswith("template"):
            pass
        elif t == "editor":
            pass
