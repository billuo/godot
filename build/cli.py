import click
from . import core
from .godot import get_current_platform, Platform


@click.command(help="Sync remote master, pull, then merge to custom-build")
def sync():
    core.sync()


@click.command(help="Build targets on branch")
@click.option("-t", "--target", help="Targets to build", default=["editor"], show_default=True, multiple=True)
@click.option("--platform", help="Platform for which to build", default=get_current_platform())
@click.option("-b", "--branch", help="Branch in which to build", default="custom-build", show_default=True)
@click.option("--dry", help="Dry run; only print the command to be run", is_flag=True)
@click.argument("scons-args", nargs=-1)
def build(target, platform, branch, dry, scons_args):
    core.build(target, platform, branch, dry, scons_args)


# @click.command(help="Copy build artifacts")
# @click.option("-t", "--target", help="Targets to copy", required=True, multiple=True)
# def copy(target):
#     # core.copy(target)
#     CURRENT_PLATFORM = get_current_platform()
#     core.copy_export_template(
#         f"godot.{CURRENT_PLATFORM}.template_debug.x86_64.exe", f"{CURRENT_PLATFORM}_debug_x86_64.exe"
#     )
#     core.copy_export_template(
#         f"godot.{CURRENT_PLATFORM}.template_release.x86_64.exe", f"{CURRENT_PLATFORM}_release_x86_64.exe"
#     )


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
        scons_args=["optimize=size", "debug_symbols=no", "thread=yes", "lto=thin"],
    )
    core.copy_export_template(f"godot.web.template_debug.x86_64.zip", "web_debug.zip")
    core.copy_export_template(f"godot.web.template_release.x86_64.zip", "web_release.zip")

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
