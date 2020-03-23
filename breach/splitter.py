import csv
import io
import sys
from time import time

from breach.utils import alpha_num_lookup, create_dir, create_dir_for_file, RingDictionary

csv.field_size_limit(sys.maxsize)


def split_file(breach_compilation_file,
               output_dir='out',
               restart_from=0):
    # It seems like this function is not 100% correct as we need to clean the dataset after this.
    # It's not a big deal but I don't understand why we have to do that.
    # Could probably be to a limitation to the large number of files we open at the same time x increase of buffer.
    create_dir(output_dir)
    alpha = alpha_num_lookup()
    files_handlers = RingDictionary()
    t1 = time()
    with open(breach_compilation_file, 'r', encoding='utf8', errors='ignore') as r:
        for i, line in enumerate(r):
            if i % 10_000_000 == 0:
                elapsed_time = time() - t1
                t1 = time()
                print(f'|- Processed {i:,} rows in {elapsed_time:.2f} seconds.')
            if i < restart_from:
                continue
            try:  # faster than if: https://stackoverflow.com/questions/1835756/using-try-vs-if-in-python
                email, password = line.strip().split(':', 1)
            except ValueError:
                continue

            output_file = get_output_file(alpha, email)
            output_file = output_dir + '/' + output_file
            write_line_to_file(files_handlers, line, output_file)


def write_line_to_file(files_handlers, line, output_file, buffer_scale=100):
    try:  # faster than if: https://stackoverflow.com/questions/1835756/using-try-vs-if-in-python
        files_handlers[output_file].write(line)
    except KeyError:
        create_dir_for_file(output_file)
        files_handlers[output_file] = open(file=output_file,
                                           mode='a+',
                                           encoding='utf8',
                                           buffering=buffer_scale * io.DEFAULT_BUFFER_SIZE)
        files_handlers[output_file].write(line)


def get_output_file(alpha_lookup, email):
    try:  # most likely case.
        letter_0 = email[0].lower()
        letter_1 = email[1].lower()
        letter_2 = email[2].lower()
    except IndexError:
        email_len = len(email)
        if email_len == 0:
            letter_0 = ''
            letter_1 = ''
            letter_2 = ''
        elif email_len == 1:
            letter_0 = email[0].lower()
            letter_1 = ''
            letter_2 = ''
        elif email_len == 2:
            letter_0 = email[0].lower()
            letter_1 = email[1].lower()
            letter_2 = ''
        else:
            raise Exception('Error in program.')
    if letter_0 not in alpha_lookup:
        output_file = 'symbols'
    elif letter_1 not in alpha_lookup:
        output_file = letter_0 + '/symbols'
    elif letter_2 not in alpha_lookup:
        output_file = letter_0 + '/' + letter_1 + '/symbols'
    else:
        output_file = letter_0 + '/' + letter_1 + '/' + letter_2
    return output_file
