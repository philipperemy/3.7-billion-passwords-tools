import logging
import os
import random
import subprocess
from datetime import datetime
from multiprocessing import Pool

import click


def shuffle(lst):
    random.seed(123)
    random.shuffle(lst)


def num_open_files_limit():
    return int(subprocess.check_output('ulimit -n', shell=True).decode().strip())


def read_lines(filename: str):
    with open(filename, 'r', encoding='utf8', errors='ignore') as r:
        return r.read().strip().split('\n')


def create_dir(output_dir: str):
    if len(output_dir) > 0 and not os.path.exists(output_dir):
        os.makedirs(output_dir)


def create_dir_for_file(filename: str):
    create_dir(os.path.dirname(filename))


def alpha_num_lookup():
    alpha = list('abcdefghijklmnopqrstuvwxyz0123456789')
    alpha_lookup = {a: 1 for a in alpha}
    assert len(alpha) == 36
    return alpha_lookup


def init_logger(name):
    format_str = '%(asctime)12s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_str)
    log_dir = 'logs'
    create_dir(log_dir)
    log_filename = os.path.join(log_dir, name + '_' + datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + '.log')
    logging.basicConfig(format=format_str, filename=log_filename, level=logging.INFO)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def parallel_function(f, sequence, num_threads=None):
    if num_threads == 1:
        return [f(x) for x in sequence]
    pool = Pool(processes=num_threads)
    result = pool.map(f, sequence)
    cleaned = [x for x in result if x is not None]
    pool.close()
    pool.join()
    return cleaned


def chunks(lst, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Ct:

    @staticmethod
    def input_file(writable=False):
        return click.Path(exists=True, file_okay=True, dir_okay=False,
                          writable=writable, readable=True, resolve_path=True)

    @staticmethod
    def input_dir(writable=False):
        return click.Path(exists=True, file_okay=False, dir_okay=True,
                          writable=writable, readable=True, resolve_path=True)

    @staticmethod
    def output_file():
        return click.Path(exists=False, file_okay=True, dir_okay=False,
                          writable=True, readable=True, resolve_path=True)

    @staticmethod
    def output_dir():
        return click.Path(exists=False, file_okay=False, dir_okay=True,
                          writable=True, readable=True, resolve_path=True)


class PasswordType:
    MD5 = 'MD5'
    SHA1 = 'SHA1'
    SHA256 = 'SHA256'
    B_CRYPT = 'B_CRYPT'
    DECRYPTED = 'DECRYPTED'


class RingDictionary:

    def __init__(self, max_num_keys=100, debug=False):
        self.d = {}  # output_file -> file_handler.
        self.k = []
        self.max_num_keys = max_num_keys
        self.debug = debug

    def __getitem__(self, key):
        return self.d[key]

    def __del__(self):
        for k in self.k:
            self.d[k].flush()
            if self.debug:
                print(f'[RingDictionary] Flush stream: {k}.')

    def __setitem__(self, key, item):
        try:
            self.d[key]
        except KeyError:
            if len(self.k) >= self.max_num_keys:
                first_item = self.k.pop(0)
                try:
                    self.d[first_item].flush()  # for streams.
                    if self.debug:
                        print(f'[RingDictionary] Flush stream: {first_item}.')
                except Exception:
                    pass
                del self.d[first_item]
                if self.debug:
                    print(f'[RingDictionary] Drop: {first_item}.')
            if self.debug:
                print(f'[RingDictionary] Add: {key}.')
            self.k.append(key)
            self.d[key] = item

    def keys(self):
        return self.d.keys()

    def values(self):
        return self.d.values()
