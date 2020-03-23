import unittest
from time import time

from breach.parser import LineParser
from breach.splitter import get_output_file
from breach.utils import alpha_num_lookup

from breach.cparser import c_parseline

p_fast = c_parseline
p_slow = LineParser.parseline

p = p_fast


class ParserTest(unittest.TestCase):

    def test_parse_1(self):
        self.assertIsNotNone(p('hello@gmail.com:123'))
        self.assertIsNotNone(p('hello@@gmail.com:123'))
        self.assertIsNotNone(p('hello @ gmail.com:123'))
        self.assertIsNotNone(p('hello @@ gmail.com:123'))
        self.assertIsNotNone(p('hello @@ gmail.com:123:'))
        self.assertIsNone(p('keyless.immo@gmail.com:'))
        self.assertIsNotNone(p('premy.enseirb@gmail.com 2296'))
        self.assertIsNotNone(p('hello @@ gmail.com,123'))
        self.assertIsNotNone(p('123,hello @@ gmail.com'))
        self.assertIsNone(p('hello@gmail.com123'))
        self.assertIsNone(p('gauntletskd@gmail.com:?????? ??? ?????'))
        self.assertIsNone(p('geoffroy.fogeoff4q@yahoo.co.uk.depth66charge:85.242.201.81,felix'))
        self.assertIsNone(p('thakhuy.step129@hotmail.com.kkk111:125.26.106.158,nopparat'))
        self.assertIsNone(p('bitebackbulldog@gmail.com:INSERT INTO `users'
                            '`(`id`, `verify`, `username`, `email`, `password'))
        self.assertIsNotNone(p('aferrer@e-vende.com:Login'))
        self.assertIsNotNone(p('misseme21@yahoo.jp ilovebois3'))
        self.assertIsNotNone(p('.y.heine@gmail.com atohiyamamot'))
        self.assertIsNotNone(p('taa06@hotmail.com@hotmail.com:8765432f'))
        self.assertIsNotNone(p('neanta,buru@ezweb.ne,jp:123'))
        self.assertIsNotNone(p('iemongozalu@gmail@com mizo1210'))
        self.assertIsNotNone(p('violet28@hotmail.co.jp@hotmail.com:sayonara'))
        self.assertIsNone(p('iemongozalu@gmail@com:'))
        self.assertIsNone(p('iemongozalu@gmail@com,'))
        self.assertIsNotNone(p('josephinejekyl@hotmail.co.uk chi chi 123'))
        self.assertIsNotNone(p('h.umehara@seedinc.co.jp@34589@@@@@@:19820429'))
        self.assertIsNotNone(p('heavenz_klein@zpost.plala.or.jp@33584@@@@@@ 03260702'))

        self.assertIsNotNone(p('<seda34.23@gmail.com:sedagirl'))
        self.assertIsNotNone(p('<cookiecutekitty@icloud.com>:<phoenix>'))
        self.assertIsNotNone(p('patricksullivan88@hotmail.jp< gorillague'))
        self.assertIsNone(p('</td>@bk.ru:peng7788525'))
        self.assertIsNone(p('<admin/>@mail.ru:andrew123'))
        self.assertIsNone(p('<i>test</i>@bk.ru:lippens'))
        self.assertIsNone(p('ESSENTIALWAY'))
        self.assertIsNone(p('ESTARRON-ESPINOSA'))
        self.assertIsNone(p('ERLONMIRANDA:sha98ne'))
        self.assertIsNotNone(p('hookturn54@hotmail.com:3318flindo2003@yahoo.ca:victory'))
        self.assertIsNotNone(p('mbssundaram@gmail.com;;shanmuga6'))
        self.assertIsNotNone(p('mbssundaram@gmail.com::shanmuga6'))
        self.assertIsNotNone(p('mbssundaram@gmail.com::hell@'))
        self.assertIsNotNone(p('mbssundaram@gmail.com::hell@:'))
        self.assertIsNotNone(p('Aliulfat 05@gmail.com:4849040'))
        self.assertIsNotNone(p('harry gill@ yaho.com:7087096771'))
        self.assertIsNotNone(p('shaheen .jafri @gmail.com:destinyuntold'))
        self.assertIsNotNone(p('mail@ottino snc.it:04921540011'))
        self.assertIsNone(p('sssssssandhya@gmail.:puleyar1'))

        self.assertIsNotNone(p('cjywzy%40eyou.com:Aebdd797'))
        self.assertIsNotNone(p('finanza.rapido2013%40yahoo.it:123456'))
        self.assertIsNotNone(p('habitacasa3%40yahoo.it:cesira89'))
        self.assertIsNotNone(p('harry gill@ yaho.com:7087096771'))
        self.assertIsNone(p('uwe kopka <ukopka@gwdg.de>:biochemie'))

        # multi-line.
        self.assertIsNotNone(p('INLOVE12:::1920-05-02:MENDHER4LIFE@yahoo.com:INLOVE12'))
        self.assertIsNotNone(p('Nicesweetboobs:1983-10-05:happy.house@outlook.com:ilovekiss'))
        self.assertIsNotNone(p('Katiya_ivanova1997@mail.ru:Katiya_ivanova1997@mail.ru;97tata1'))

        multi_lines = [
            'piabersas@libero.it;stefano.ripamonti@rpmtlc.it:CAROLINAPIANTA',
            'Nicesweetboobs:1983-10-05:happy.house@outlook.com:ilovekiss',
            '190.40.252.191,XabelciberX,abelciber@latinmail.com,gatita9685567',
            '201.245.164.50,andres vergara,anfeveres@hotmail.com,barcelona10',
            '65.94.11.229,stephane,fraisinoo@hotmail.com,ste264',
            'INLOVE12:::1920-05-02:MENDHER4LIFE@yahoo.com:INLOVE12',
            'agaliha84:::1969-07-02:jumbalaya684@privacyharbor.com:agaliha84',
            'happy8360:::1963-09-12:shabby407@yahoo.com:jdj407',
            'tinkertailor99:1947-10-12:terry@anymouse.com:77880577',
            'Cash5178:1970-11-06:littlejohn2dajr@yahoo.com:hulk1234',
            'Creecher0275:1972-04-22:creech.peter@yahoo.com:complete',
            'Katiya_ivanova1997@mail.ru:Katiya_ivanova1997@mail.ru;97tata1',
            'krasotka.1.zwezda@mail.ru:krasotka.1.zwezda@mail.ru;zwezda',
            'SavvySummer:1973-03-17:savvysummer1@gmail.com:sunshine0699',
            'RaWRrr:1990-12-02:ogaboga_12@hotmail.com:nitsua',
            'piabersas@libero.it;stefano.ripamonti@rpmtlc.it:CAROLINAPIANTA',
            'raffaele@puntolingue.it;info@hotelbrumansalerno.it:RRAHOTEL',
            'silent4463:1980-10-14:yancey.robert10@yahoo.com:salinas'
        ]

        for multi_line in multi_lines:
            self.assertIsNotNone(p(multi_line))

        self.assertIsNone(p('300396	matelymaly	rune_scape_player@hotmail.com	222.155.173.78	'
                            '3d2c5414a041f518b03b750e62e4ebc3:Nhc'))
        self.assertIsNone(p('05-02-2012;5721869;melanie2032003@yahoo.fr:f02368945726d5fc2a14eb576f7276c0'))
        self.assertIsNotNone(p('diet3rix@gmail.com::g1u3ck'))
        self.assertIsNotNone(p('asuss_85@mail.ru:asuss_85@mail.ru:2904198'))
        self.assertIsNotNone(p('sanda ostojic.todor@gmail.com:vasafultv'))
        self.assertIsNone(p('jsjjd.@Com.:love melon'))

    def test_parse_2(self):
        t = time()
        for i in range(20000):  # 10,000 * 13 = 130,000 in 4.0 seconds.
            # => 32B in in 10 days. That's a lot.
            p('hello@gmail.com:123')
            p('hello@@gmail.com:123')
            p('hello @ gmail.com:123')
            p('hello @@ gmail.com:123')
            p('hello @@ gmail.com:123:')
            p('hello @@ gmail.com,123')
            p('123,hello @@ gmail.com')
            p('hello@gmail.com123')
            p('gauntletskd@gmail.com:?????? ??? ?????')
            p('geoffroy.fogeoff4q@yahoo.co.uk.depth66charge:85.242.201.81,felix')
            p('thakhuy.step129@hotmail.com.kkk111:125.26.106.158,nopparat')
            p('bitebackbulldog@gmail.com:INSERT INTO `users'
              '`(`id`, `verify`, `username`, `email`, `password')
            p('aferrer@e-vende.com:Login')
        print(time() - t)

    def test_parse_3(self):
        alpha = alpha_num_lookup()
        self.assertEqual('j/o/s', get_output_file(alpha, 'josemariacanyero@hotmail.com'))
        self.assertEqual('c/e/o', get_output_file(alpha, 'ceo21w@gmail.com'))
        self.assertEqual('x/symbols', get_output_file(alpha, 'x_fear_238@hotmail.fr'))
        self.assertEqual('x/a/symbols', get_output_file(alpha, 'xa_fear_238@hotmail.fr'))
        self.assertEqual('x/symbols', get_output_file(alpha, 'x@hotmail.com'))
        self.assertEqual('k/e/v', get_output_file(alpha, 'kevmedic13@yahoo.com'))


if __name__ == '__main__':
    unittest.main()
