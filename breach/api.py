import os
import random
import shutil
import subprocess
from glob import glob
from pathlib import Path

from tqdm import tqdm

from breach.parser import parse_to_files
from breach.query import QueryAPI, get_query_manager
from breach.splitter import get_output_file, write_line_to_file
from breach.utils import alpha_num_lookup, shuffle, read_lines


class API:

    @staticmethod
    def evaluate(old, new):
        hit_count = 0
        total_count = 0
        files = [p for p in Path(old).expanduser().glob('**/*') if p.is_file()]
        for i in range(1000):
            lines = read_lines(random.choice(files))
            shuffle(lines)
            random_lines = lines[0:10]
            for random_line in random_lines:
                password_list = QueryAPI.query(new, random_line.split(':')[0], 'email')
                total_count += 1
                if len(password_list) == 0:
                    print(f'OLD: {random_line}, NEW: miss, HIT_RATE = {hit_count / total_count:.3f}.')
                else:
                    hit_count += 1
                    print(f'OLD: {random_line}, NEW: hit, HIT_RATE = {hit_count / total_count:.3f}.')

    @staticmethod
    def merge(src, dest):
        src_files = find_files(src)
        dest_files = find_files(dest)
        for src_index, src_file in src_files.items():
            if src_index in dest_files:
                merge(src_file, dest_files[src_index])
            else:
                move(src_file, dest + src_index)

    @staticmethod
    def parse(path, success_file, failure_file, cython_acceleration=False):
        parse_to_files(path, success_file, failure_file, cython_acceleration)

    @staticmethod
    def sort(path):
        path = str(Path(path).expanduser())
        paths = [Path(a) for a in glob(path + '/**/*', recursive=True) if Path(a).is_file()
                 and Path(a).suffix != '.sorted']
        for path in tqdm(paths, desc='Unique > Sorting > Replacing existing files'):
            output_path = path.with_suffix('.sorted')
            lines = read_lines(path)
            unique_sorted_lines = sorted(set(lines))
            with open(output_path, 'w', encoding='utf8') as w:
                w.write('\n'.join(unique_sorted_lines) + '\n')
            shutil.move(output_path, path)

    @staticmethod
    def clean(path):
        files = list(find_files(Path(path).expanduser()).values())
        shuffle(files)
        alpha = alpha_num_lookup()
        num_files_moved = 0
        files_handlers = {}  # u limit here!
        with tqdm(files, desc='clean') as bar:
            for file in bar:
                lines_to_delete = []
                lines = read_lines(file)
                for line in lines:
                    line_split = line.split(':')
                    ground_truth_file = get_output_file(alpha, line_split[0])
                    key = str(file).replace(path, '')
                    if key.startswith('/'):
                        key = key[1:]
                    if ground_truth_file != key:
                        output_file = Path(path) / ground_truth_file
                        # print(f'MOVE: {line_split[0]} -> {output_file}.')
                        write_line_to_file(files_handlers, line_split, output_file, buffer_scale=10)
                        lines_to_delete.append(line)
                        num_files_moved += 1
                        if num_files_moved % 100_000 == 0:
                            truncated_file = str(file).replace(path, "")
                            truncated_output_file = str(output_file).replace(path, "")
                            bar.set_description(f'clean. {num_files_moved:,} moved. '
                                                f'move: {line_split[0]}: {truncated_file}'
                                                f' -> {truncated_output_file}')
                lines2 = sorted(set(lines) - set(lines_to_delete))
                if len(lines) != len(lines2):
                    with open(str(file), 'w', encoding='utf8') as w:
                        w.write('\n'.join(lines2) + '\n')

    @staticmethod
    def test(file: str, dataset: str):
        qm = get_query_manager(dataset)
        cracked_rate = 0
        lines = read_lines(file)
        for line in lines:
            results = qm.perform_query(line.strip(), 'email')
            if len(results) > 0:
                passwords = [p.split(':', 1)[-1] for p in results]
                print('FOUND:', line, ':'.join(passwords))
                cracked_rate += 1
        print(f'Cracked rate: {cracked_rate / len(lines)}')

    @staticmethod
    def chunk_files(path: str, max_size: int):
        # split -b 50000000 file.txt file.txt.
        # -d to have .00 and .01 is not compatible with MacOS...
        files = list(find_files(Path(path).expanduser()).values())
        for f in tqdm(files, desc='chunk large files'):
            if f.stat().st_size / 1e6 > max_size:
                cmd = ['split', '-b', str(int(max_size * 1e6)), str(f), str(f) + '_']
                print(f'File size: {f.stat().st_size / 1e6:.2f} Mb. ' + ' '.join(cmd))
                subprocess.check_output(cmd)
                f.unlink()


def find_files(path: str):
    path2 = Path(path).expanduser()
    files = [p for p in path2.glob('**/*') if p.is_file()]
    index = {str(f).replace(str(path2), ''): f for f in files}
    assert len(index) == len(files)
    return index


def merge(src, dst):
    print(f'merge {src} {dst}')
    with open(src, 'r', encoding='utf8', errors='ignore') as r:
        content1 = r.read()
    with open(dst, 'a', encoding='utf8', errors='ignore') as w:
        w.write(content1)
    print(f'del {src}')
    os.remove(src)


def move(src, dst):
    print(f'mv {src} {dst}')
    shutil.move(src, dst)
