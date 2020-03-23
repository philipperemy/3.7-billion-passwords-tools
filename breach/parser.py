import os
import re
import string
from glob import glob
from pathlib import Path
from time import time

from breach.cparser import c_parseline
from tqdm import tqdm
from validate_email import validate_email

from breach.utils import chunks, read_lines, PasswordType
from breach.utils import parallel_function, shuffle


# slow functions.

def our_validate_email(candidate: str):
    if candidate.count('@') != 1:
        return False
    if '.' not in candidate.split('@')[-1]:  # .com or .fr
        return False
    return validate_email(candidate)


class LineParser:

    @staticmethod
    def _parse_line(row, separator, flip=False):
        if separator not in row:  # return fast.
            return None
        if separator != ' ':
            parts = row.split(separator)
            sep_count_cond = len(parts) == 2
            if len(parts) > 2:
                row = separator.join(parts[-2:])
                # sh_karimian@yahoo.com:kiyan1365:16
                # wgwendlee@aol.com:godis2good:
                sep_count_cond = True
        elif separator in row:
            sep_count_cond = True
        else:
            sep_count_cond = False
        if sep_count_cond:
            mail, password = row.split(separator, 1)
            if flip:
                password, mail = mail, password
            password = password.replace(' ', '')
            if len(password) > 30:  # Password of 30 chars look like this: adfsfdsgdfghkfdghdsdfgdfgdfgdf.
                return None
            if len(password) == 0:
                return None
            if '\n\n' in password:
                return None
            if set(password) == {'?'}:  # - gauntletskd@gmail.com:?????? ??? ?????
                return None
            if password.count('.') >= 3 and \
                    re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', password) is not None:
                return None
            mail = mail.replace(' ', '')
            # https://grox.net/utils/encoding.html
            if '@' not in mail:
                mail = mail.replace('%40', '@')
            # - thakhuy.step129@hotmail.com.kkk111:125.26.106.158,nopparat
            # count first because it's faster than compiling a regexp.

            if len(mail) == 0:
                return None

            last_char = mail[-1]
            first_char = mail[0]
            # misseme21@yahoo.jp\ ilovebois3
            if last_char in ['<', '.', '\\', '>', '_']:
                mail = mail[:-1]
            # .y.heine@gmail.com atohiyamamot [exists]
            if first_char in ['.', '<']:
                mail = mail[1:]
            if mail.endswith('@com'):
                # iemongozalu@gmail@com mizo1210
                mail = mail.replace('@com', '.com')
            if not our_validate_email(mail):
                # some people replace neanta,buru@ezweb.ne,jp
                mail = mail.replace(',', '.')
                parts = mail.split('@')
                if len(parts) > 2:
                    mail = '@'.join(parts[0:2])
            # TODO: do it for most common domain names.
            if mail.count('@hotmail.com') == 2:  # taa06@hotmail.com@hotmail.com:8765432f
                mail = mail.replace('@hotmail.com', '', 1)
            if our_validate_email(mail) and not our_validate_email(password):
                password_type = LineParser.get_password_type(password)
                return mail, password, password_type
        return None

    @staticmethod
    def is_md5(password):
        if len(password) == 32:
            for e in password:
                if not ((ord('0') <= ord(e) <= ord('9')) or
                        (ord('A') <= ord(e) <= ord('F')) or
                        (ord('a') <= ord(e) <= ord('f'))):
                    return False
            return True
        else:
            return False

    @staticmethod
    def is_sha1(password):
        if len(password) == 40:
            for e in password:
                if not ((ord('0') <= ord(e) <= ord('9')) or
                        (ord('A') <= ord(e) <= ord('F')) or
                        (ord('a') <= ord(e) <= ord('f'))):
                    return False
            return True
        else:
            return False

    @staticmethod
    def is_sha_256(password):
        if len(password) == 64:
            for e in password:
                if not ((ord('0') <= ord(e) <= ord('9')) or
                        (ord('A') <= ord(e) <= ord('F')) or
                        (ord('a') <= ord(e) <= ord('f'))):
                    return False
            return True
        else:
            return False

    @staticmethod
    def is_b_crypt(password):
        b_crypt_pattern_cond = password[0:4] == "$2a$" or password[0:4] == "$2b$" or password[0:4] == "$2y$"
        if 50 < len(password) < 70 and b_crypt_pattern_cond:
            return True
        return False

    @staticmethod
    def get_password_type(password):
        if LineParser.is_md5(password):
            return PasswordType.MD5
        elif LineParser.is_sha1(password):
            return PasswordType.SHA1
        elif LineParser.is_sha_256(password):
            return PasswordType.SHA256
        elif LineParser.is_b_crypt(password):
            return PasswordType.B_CRYPT
        else:
            return PasswordType.DECRYPTED

    @staticmethod
    def parseline(s: str):
        # case   mail@mail.com:password
        # case   mail@mail.com;password
        # case   mail@mail.com password
        valid_separators = [':', ';', ' ', '\t', '  ', '   ', ', ', ',', ';;', '::', ',']
        # https://github.com/swiftmailer/swiftmailer/issues/239
        b = s.strip()
        b = ''.join(list(filter(lambda x: x in string.printable, b)))
        while '..' in b:  # TODO: could be move just for the email.
            b = b.replace('..', '')
        if b.startswith('mailto:'):
            b = b[len('mailto:'):]
        if b.startswith('E-mail:'):
            b = b[len('E-mail:'):]
        if b.startswith(':'):
            b = b[1:]
        if b.endswith(':'):
            b = b[:-1]

        # TODO: could be move just for the email. but we dont need to be 100% accurate here.
        b = b.replace('.@', '@')  # just typo.
        b = b.replace('@.', '@')  # just typo.
        b = b.replace(' @ ', '@')  # just typo.
        b = b.replace('@@', '@')  # just typo.

        if ':' in b and ';' in b:
            b = b.replace(';', ':')

        # FLIP=FALSE
        for valid_separator in valid_separators:
            result = LineParser._parse_line(b, valid_separator, flip=False)
            if result is not None:
                return result
        # FLIP=TRUE
        for valid_separator in valid_separators:
            result = LineParser._parse_line(b, valid_separator, flip=True)
            if result is not None:
                return result
        # print(f'DISCARD: {s.strip()}')
        return None


class Processor:

    def __init__(self, w=None, f=None, cython_acceleration=False):  # for big files -> writes to disk directly.
        if cython_acceleration:
            print('Cython acceleration enabled.')
            self.bind = c_parseline
        else:
            print('Cython acceleration disabled.')
            self.bind = LineParser.parseline
        self.w = w  # cannot be serialized for multi processing.
        self.f = f  # cannot be serialized for multi processing.

    def process(self, filename: Path, is_big_file: bool = False):
        success_list = []
        failure_list = []
        with open(str(filename), 'r', encoding='utf8', errors='ignore') as r:
            buf_size = 10 ** 6  # for very large files.
            while True:
                lines = r.readlines(buf_size)
                if len(lines) == 0:
                    break
                for line in lines:
                    result = self.bind(line)
                    if result is not None:
                        mail, password, password_type = result
                        if password_type == PasswordType.DECRYPTED:
                            # mail is case insensitive.
                            success_str = ':'.join([str(mail).lower().strip(), password.strip()]) + '\n'
                            if is_big_file:
                                self.w.write(success_str)
                            else:
                                success_list.append(success_str)
                    else:
                        # stop writing binary data to file...
                        fail_line = ''.join(list(filter(lambda x: x in string.printable, line)))
                        if is_big_file:
                            self.f.write(fail_line)
                        else:
                            failure_list.append(fail_line)
        return success_list, failure_list


def parse_to_files(input_dir, success_filename, failure_filename, cython_acceleration):
    files = [p for p in Path(input_dir).glob('**/*') if p.is_file()]
    shuffle(files)
    # restart from where we stopped.
    progress_filename = 'progress.txt'
    if os.path.exists(progress_filename):
        lines = read_lines(progress_filename)
    else:
        lines = []
    lines = {n: 1 for n in lines}
    files = [f for f in files if str(f) not in lines]
    shuffle(files)
    # files.sort(key=lambda f: os.stat(f).st_size)  # smallest to largest

    success_total = 0
    failure_total = 0
    num_threads = os.cpu_count()
    start_time = time()
    with open(progress_filename, 'a+') as p:
        with open(failure_filename, 'a+', encoding='utf8') as f:
            with open(success_filename, 'a+', encoding='utf8') as w:
                large_files_processor = Processor(w=w, f=f, cython_acceleration=cython_acceleration)
                small_files_processor = Processor(cython_acceleration=cython_acceleration)
                with tqdm(files) as bar:
                    for chunk in chunks(files, num_threads):
                        # more than 300MB?
                        any_large_files = any([c.stat().st_size / 1e6 > 300 for c in chunk])
                        if any_large_files:
                            # single thread and write directly to the files.
                            for chunky in chunk:
                                large_files_processor.process(chunky)
                        else:
                            # as many threads as we want.
                            results = parallel_function(small_files_processor.process, chunk, len(chunk))

                            for single_result in results:
                                success_list, failure_list = single_result

                                for single_success in success_list:
                                    w.write(single_success)
                                for single_success in failure_list:
                                    f.write(single_success)

                                success_total += len(success_list)
                                failure_total += len(failure_list)

                        bar.update(len(chunk))
                        bar.set_description(f'success = {success_total:,} failure = {failure_total:,}')
                        for single_chunk in chunk:
                            p.write(str(single_chunk) + '\n')
    print(f'Time elapsed {time() - start_time:.3f} seconds.')


def statistics(input_dir):
    files = glob(os.path.expanduser(input_dir) + '/**/*.*', recursive=True)
    files = [f for f in files if not f.endswith('.tar.gz')]
    shuffle(files)
    parsed_lines = 0
    with open('stats.txt', 'w') as w:
        w.write(','.join(['success', 'failure', 'failure_rate', 'filename']) + '\n')
        for filename in files:
            success = 0
            failure = 0
            lines = read_lines(filename)
            parsed_lines += len(lines)
            for line in lines:
                result = LineParser.parseline(line)
                if result is not None:
                    success += 1
                else:
                    failure += 1
            try:
                failure_rate = failure / (success + failure) * 100
            except ZeroDivisionError:
                failure_rate = 0.0
            w.write(','.join([str(success), str(failure), f'{failure_rate:.3f}', filename]) + '\n')
            print(f'Parsed lines = {parsed_lines:,}.')
            print(f'filename = {filename}, success = {success:,}, '
                  f'failure = {failure:,}, failure rate = {failure_rate:.3f}%')
