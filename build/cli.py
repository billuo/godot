import click

from . import core
from .godot import Platform, get_current_platform


@click.command(help="Sync remote master, pull, then merge to custom-build")
def sync():
    core.sync()


@click.command(help="Build the specified target")
@click.option("-t", "--target", help="Targets to build", default=["editor"], show_default=True, multiple=True)
@click.option("--platform", help="Platform for which to build", default=get_current_platform())
@click.option("--dry", help="Dry run; only print the command to be run", is_flag=True)
@click.argument("scons-args", nargs=-1)
def build(target, platform, dry, scons_args):
    CURRENT_PLATFORM = get_current_platform()
    core.build(target=target, platform=platform, dry=dry, scons_args=scons_args)
    for t in target:
        if t == "template_debug":
            core.copy_export_template(
                f"godot.{CURRENT_PLATFORM}.template_debug.x86_64.exe", f"{CURRENT_PLATFORM}_debug_x86_64.exe"
            )
        elif t == "template_release":
            core.copy_export_template(
                f"godot.{CURRENT_PLATFORM}.template_release.x86_64.exe", f"{CURRENT_PLATFORM}_release_x86_64.exe"
            )


# NOTE: For 4.3.x.rc web export templates, run precisely `emsdk activate 3.1.64`.
# Otherwise, build fails like this: bin\godot.web.template_debug.wasm32.worker.js: No such file or directory
@click.command(help="Helper for building all useful targets")
@click.option("--sync", help="Sync remote master, pull, then merge to custom-build", is_flag=True)
def build_all(sync):
    CURRENT_PLATFORM = get_current_platform()
    if sync:
        core.sync()
    core.build(scons_args=["compiledb=yes"])

    # build and copy native export templates
    core.build(target=["template_debug", "template_release"])
    core.copy_export_template(
        f"godot.{CURRENT_PLATFORM}.template_debug.x86_64.exe", f"{CURRENT_PLATFORM}_debug_x86_64.exe"
    )
    core.copy_export_template(
        f"godot.{CURRENT_PLATFORM}.template_release.x86_64.exe", f"{CURRENT_PLATFORM}_release_x86_64.exe"
    )

    # build and copy web export templates
    core.build(
        target=["template_debug", "template_release"],
        platform=Platform.WEB,
        scons_args=[
            "optimize=size",
            "debug_symbols=no",
            "thread=yes",
            "lto=thin",
            "javascript_eval=no",
            "dlink_enabled=yes",  # GDExtension support
        ],
    )
    core.copy_export_template("godot.web.template_debug.x86_64.zip", "web_debug.zip")
    core.copy_export_template("godot.web.template_release.x86_64.zip", "web_release.zip")

    # build and copy android export templates
    core.build(
        target=["template_debug", "template_release"],
        platform=Platform.ANDROID,
        scons_args=["optimize=size", "debug_symbols=no", "thread=yes", "lto=thin", "arch=arm32"],
    )
    core.build(
        target=["template_debug", "template_release"],
        platform=Platform.ANDROID,
        scons_args=["optimize=size", "debug_symbols=no", "thread=yes", "lto=thin", "arch=arm64"],
    )
    # TODO: copy android export templates


@click.group(help="Build helper script")
def cli():
    pass


cli.add_command(sync)
cli.add_command(build)
# cli.add_command(copy)
cli.add_command(build_all)

if __name__ == "__main__":
    cli()
