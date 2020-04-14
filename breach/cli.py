import logging
from pathlib import Path

import click

from breach.api import API
from breach.splitter import split_file
from breach.utils import Ct, num_open_files_limit


# Extraction: nohup find . -name '*.tar.gz' -execdir tar --keep-newer-files -xzvf '{}' -C ../extracted \; &

def recursive_help(cmd, parent=None):
    ctx = click.core.Context(cmd, info_name=cmd.name, parent=parent)
    print(cmd.get_help(ctx))
    print()
    commands = getattr(cmd, 'commands', {})
    for sub in commands.values():
        recursive_help(sub, ctx)


@click.group()
@click.option('--debug/--no-debug')
@click.pass_context
def cli(ctx, debug):
    if debug:
        click.echo('Debugging mode enabled.')
    logging.basicConfig(format='%(asctime)12s - %(levelname)s - %(message)s', level=logging.INFO)
    if not debug and num_open_files_limit() < 60_000 and ctx.invoked_subcommand in ['split', 'clean']:
        click.echo('ERROR: Increase the limit of the number of open files to at least 60,000.')
        click.echo('ERROR: ulimit -n 60000')
        exit(1)


@cli.command()
def dumphelp():
    recursive_help(cli)


@cli.command(short_help='Converts a large FILE to a query friendly folder OUT (e.g. a/b/c). '
                        'Use RESTART_FROM to resume from the i-th line.')
@click.option('--file', required=True, type=Ct.input_file())
@click.option('--out', required=True, type=Ct.output_dir())
@click.option('--restart_from', default=0, type=int, show_default=True)
def split(file, out, restart_from):
    split_file(file, out, restart_from)


@cli.command(short_help='chunk large TXT files into smaller files.')
@click.option('--path', required=True, type=Ct.input_dir())
@click.option('--size', default=50, type=int, show_default=True)  # MB.
def chunk(path, size):
    API.chunk_files(path, size)


@cli.command(short_help='Sorts a query friendly folder PATH. Target is itself.')
@click.option('--path', required=True, type=Ct.input_dir())
def sort(path):
    API.sort(path)


@cli.command(short_help='Cleans a query friendly folder PATH. Move incorrect records and sort the files.')
@click.option('--path', required=True, type=Ct.input_dir())
def clean(path):
    API.clean(path)


@cli.command(short_help='Infers passwords of a list of emails defined in FILE with a query friendly folder DATASET.')
@click.option('--file', required=True, type=Ct.input_file())
# @click.option('--dataset', required=True, type=click.Choice(DATASET_CHOICES, case_sensitive=False))
@click.option('--dataset', required=True)
def test(file: str, dataset: str):
    API.test(file, dataset)


@cli.command(short_help='Parses an unstructured folder PATH of many files and generates two files: '
                        'SUCCESS_FILE and FAILURE_FILE. All valid email:password will go to SUCCESS_FILE.')
@click.option('--path', required=True, type=Ct.output_dir())
@click.option('--success_file', required=True, type=Ct.output_file())
@click.option('--failure_file', required=True, type=Ct.output_file())
@click.option('--cython_acceleration/--no-cython_acceleration', default=False)
def parse(path, success_file, failure_file, cython_acceleration):
    API.parse(Path(path).expanduser(), success_file, failure_file, cython_acceleration)


@cli.command(short_help='Merges dataset SRC into dataset DEST. Duplicates are removed in the second pass.')
@click.option('--src', required=True, type=Ct.input_dir())
@click.option('--dest', required=True, type=Ct.input_dir())
def merge(src: str, dest: str):
    API.merge(src, dest)
    API.clean(dest)


@cli.command(short_help='Evaluates some metrics such as precision/recall (e.g. is OLD into NEW).')
@click.option('--old', required=True, type=Ct.input_dir())
@click.option('--new', required=True, type=Ct.input_dir())
def evaluate(old: str, new: str):
    API.evaluate(old, new)


@cli.command(short_help='Filters lines less than N and more than M.')
@click.option('--file', required=True, type=Ct.input_file())
@click.option('--out', required=True, type=Ct.output_file())
@click.option('--less_than', required=True, type=int)
@click.option('--more_than', required=True, type=int)
def filter_lines(file: str, out: str, less_than: int, more_than: int):
    API.filter_lines(file, out, less_than, more_than)


if __name__ == '__main__':
    cli()
