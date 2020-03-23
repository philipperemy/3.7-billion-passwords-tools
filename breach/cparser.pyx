import re
import string

import cython
from validate_email import validate_email

from breach.utils import PasswordType

cdef inline c_is_md5(str password):
    if len(password) == 32:
        for e in password:
            if not ((ord('0') <= ord(e) <= ord('9')) or
                    (ord('A') <= ord(e) <= ord('F')) or
                    (ord('a') <= ord(e) <= ord('f'))):
                return False
        return True
    else:
        return False

cdef inline c_is_sha1(str password):
    if len(password) == 40:
        for e in password:
            if not ((ord('0') <= ord(e) <= ord('9')) or
                    (ord('A') <= ord(e) <= ord('F')) or
                    (ord('a') <= ord(e) <= ord('f'))):
                return False
        return True
    else:
        return False

cdef inline c_is_sha_256(str password):
    if len(password) == 64:
        for e in password:
            if not ((ord('0') <= ord(e) <= ord('9')) or
                    (ord('A') <= ord(e) <= ord('F')) or
                    (ord('a') <= ord(e) <= ord('f'))):
                return False
        return True
    else:
        return False

cdef inline c_is_b_crypt(str password):
    if 50 < len(password) < 70:
        b_crypt_pattern_cond = password[0:4] == "$2a$" or password[0:4] == "$2b$" or password[0:4] == "$2y$"
        if b_crypt_pattern_cond:
            return True
    return False

cdef inline c_get_password_type(str password):
    if c_is_md5(password):
        return PasswordType.MD5
    elif c_is_sha1(password):
        return PasswordType.SHA1
    elif c_is_sha_256(password):
        return PasswordType.SHA256
    elif c_is_b_crypt(password):
        return PasswordType.B_CRYPT
    else:
        return PasswordType.DECRYPTED

@cython.boundscheck(False)
def c_parseline(str s):
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
        result = c_parse_line(b, valid_separator, flip=False)
        if result is not None:
            return result
    # FLIP=TRUE
    for valid_separator in valid_separators:
        result = c_parse_line(b, valid_separator, flip=True)
        if result is not None:
            return result
    # print(f'DISCARD: {s.strip()}')
    return None

@cython.boundscheck(False)
cdef inline c_our_validate_email(str candidate):
    parts = candidate.split('@')
    if len(parts) != 2:
        return False
    if '.' not in parts[-1]:  # .com or .fr
        return False
    return validate_email(candidate)

@cython.boundscheck(False)
cdef c_parse_line(str row, str separator, bint flip=False):
    cdef bint is_sep_in_row = separator in row
    cdef bint sep_count_cond = False
    cdef str mail = ''
    cdef str password = ''
    if not is_sep_in_row:  # return fast.
        return None
    if separator != ' ':
        parts = row.split(separator)
        sep_count_cond = len(parts) == 2
        if len(parts) > 2:
            row = separator.join(parts[-2:])
            # sh_karimian@yahoo.com:kiyan1365:16
            # wgwendlee@aol.com:godis2good:
            sep_count_cond = True
    elif is_sep_in_row:
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
        if not c_our_validate_email(mail):
            # some people replace neanta,buru@ezweb.ne,jp
            mail = mail.replace(',', '.')
            parts = mail.split('@')
            if len(parts) > 2:
                mail = '@'.join(parts[0:2])
        # TODO: do it for most common domain names.
        if mail.count('@hotmail.com') == 2:  # taa06@hotmail.com@hotmail.com:8765432f
            mail = mail.replace('@hotmail.com', '', 1)
        if c_our_validate_email(mail) and not c_our_validate_email(password):
            password_type = c_get_password_type(password)
            return mail, password, password_type
    return None
