import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


# https://pypi.org/project/ripgrepy/

class BreachCompilationConstants:
    EMAIL_INDEX = '/media/philippe/DATA/datasets/BreachCompilation/data'
    PASSWORD_INDEX = '/media/philippe/DATA/datasets/BreachCompilation/passwords'


class Collections1:
    EMAIL_INDEX = '/media/philippe/8TB/datasets/passwords2/data'
    PASSWORD_INDEX = None


class Collections_2_5:
    EMAIL_INDEX = '/media/philippe/8TB/datasets/passwords2/data'
    PASSWORD_INDEX = None


DATASET_CHOICES = ['breach_compilation', 'collections_1', 'collections_2_5', 'all']


def get_query_manager(dataset_choice: str):
    if dataset_choice.lower() == 'breach_compilation':
        return QueryManager(BreachCompilationConstants)
    elif dataset_choice.lower() == 'collections_1':
        return QueryManager(Collections1)
    elif dataset_choice.lower() == 'collections_2_5':
        return QueryManager(Collections_2_5)
    elif os.path.exists(dataset_choice):
        class Custom:
            EMAIL_INDEX = dataset_choice
            PASSWORD_INDEX = None

        return QueryManager(Custom)
    else:
        return QueryMultiManager()  # all


def mask_pass_justin_rule(password: str, num_asterisks=-1) -> str:
    if len(password) >= 8:
        return password[0:2] + (len(password) - 3) * '*' + password[-1]
    return password[0] + '*' * (len(password) - 2) + password[-1]


def mask_pass(password: str, num_asterisks=2) -> str:
    if len(password) <= num_asterisks:
        return '*' * len(password)
    if len(password) >= 4:
        i = len(password) // 2
        even = num_asterisks % 2 == 0
        half = num_asterisks // 2
        if even:
            left = half
            right = half
        else:
            left = half
            right = half + 1
        return password[0:i - left] + '*' * num_asterisks + password[i + right:]
    else:
        return password


def extract_emails_and_passwords(txt_lines):
    emails_passwords = []
    for txt_line in txt_lines:
        try:
            if '@' in txt_line:  # does it contain an email address?
                if all([char in txt_line for char in [':', ';']]):  # which separator is it? : or ;?
                    separator = ':'
                elif ':' in txt_line:  # '_---madc0w---_@live.com:iskandar89
                    separator = ':'
                elif ';' in txt_line:  # '_---lelya---_@mail.ru;ol1391ga
                    separator = ';'
                else:
                    continue

                strip_txt_line = txt_line.strip()
                email, password = strip_txt_line.split(separator)
                emails_passwords.append((email, password))
        except Exception:
            pass
    return emails_passwords


def postprocess(results, num_asterisks_to_mask_password=0):
    response = [b for b in extract_emails_and_passwords(results)]
    if num_asterisks_to_mask_password > 0:
        response = [(b[0], mask_pass_justin_rule(b[1])) for b in response]
    response = [':'.join(b) for b in response]
    response = sorted(set(response))
    return response


class QueryAPI:

    @staticmethod
    def scanning(directory: Path):
        file_list, dir_list = {}, {}
        for x in directory.iterdir():
            if x.is_file():
                file_list[x.name] = x
            else:
                dir_list[x.name] = x
        return file_list, dir_list

    @staticmethod
    def search_in_file(path: Path, email):
        assert path.is_file(), path
        try:
            results = subprocess.check_output(['rg', '--no-line-number', '-ie', '^' +
                                               email, str(path)]).decode('utf8').split('\n')
            results = [a for a in results if a != '']
        except subprocess.CalledProcessError:
            results = []
        return results

    @staticmethod
    def recursive_search(path: Path, characters: list, index: int):
        fl, dl = QueryAPI.scanning(path)
        cur = characters[index].lower()
        if cur in fl:
            return QueryAPI.search_in_file(fl[cur], ''.join(characters))
        elif cur in dl:
            return QueryAPI.recursive_search(dl[cur], characters, index + 1)
        elif 'symbols' in fl:
            return QueryAPI.search_in_file(fl['symbols'], ''.join(characters))
        else:
            raise Exception('Hello.')

    @staticmethod
    def query(data_dir: str, request: str, query_type: str, num_asterisks_to_mask_password: int = 0):
        if len(request) <= 3:
            return []
        if query_type == 'email' and '@' not in request:
            return []
        response = QueryAPI.recursive_search(Path(data_dir), list(request), 0)
        return postprocess(response, num_asterisks_to_mask_password)


class QueryManagerStub:
    def __init__(self, constants):
        self.default_email_index = constants.EMAIL_INDEX
        self.default_password_index = constants.PASSWORD_INDEX
        self.counter = 0

    def perform_query(self, request: str, query_type: str, num_asterisks_to_mask_password=0):
        self.counter += 1
        if self.counter % 2 == 0:
            return [f'{request}:hello123', f'{request}:hello123456']
        else:
            return []


class QueryManager:

    def __init__(self, constants):
        self.default_email_index = constants.EMAIL_INDEX
        self.default_password_index = constants.PASSWORD_INDEX

    def perform_query(self, request: str, query_type: str, num_asterisks_to_mask_password=0):
        if query_type == 'email':
            index = self.default_email_index
        elif query_type == 'password':
            index = self.default_password_index
        else:
            raise Exception({'error': 'Index is either email or password.'})
        results = []
        if ' ' in request:  # batch.
            for single_req in request.split(' '):
                results.extend(QueryAPI.query(index, single_req, query_type, num_asterisks_to_mask_password))
        else:
            results.extend(QueryAPI.query(index, request, query_type, num_asterisks_to_mask_password))
        return results


class QueryMultiManager:

    def __init__(self):
        self.qm1 = QueryManager(BreachCompilationConstants)
        self.qm2 = QueryManager(Collections1)
        self.qm3 = QueryManager(Collections_2_5)

    def perform_query(self, request: str, query_type: str, num_asterisks_to_mask_password=0):
        results = self.qm1.perform_query(request, query_type, num_asterisks_to_mask_password)
        results.extend(self.qm2.perform_query(request, query_type, num_asterisks_to_mask_password))
        results.extend(self.qm3.perform_query(request, query_type, num_asterisks_to_mask_password))
        return sorted(set(results))
