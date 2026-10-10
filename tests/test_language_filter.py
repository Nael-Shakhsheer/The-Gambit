import unittest

from game import GameWorld
from language_filter import clean_name, filter_text


class LanguageFilterTests(unittest.TestCase):
    def test_profanity_insults_and_harassment_are_masked(self):
        for text in ['fuck!', 'SHIT', 'idiot', 'stupid', 'kill yourself', 'kys',
                     'f.u.c.k', 'f u c k', 'fuuuck', 'sh1t', '$hit$', 'sh!t',
                     'ｆｕｃｋ', 'f\u200bu\u200bc\u200bk', 'fück', 'ShitLord']:
            self.assertIn('*', filter_text(text), text)
        self.assertEqual(filter_text('help, you idiot!'), 'help, you *****!')

    def test_normal_gameplay_words_and_names_are_preserved(self):
        for text in ['Class Assassin', 'Scunthorpe', 'grass cover', 'skill tree',
                     'Kill the dragon', 'Mossgate', 'The Gauntlet', 'Knight Companion',
                     'Gather here!', 'Revive me', '12345']:
            self.assertEqual(filter_text(text), text)

    def test_names_and_chat_are_filtered_at_the_server_boundary(self):
        world = GameWorld()
        code, host = world.create_room('Fuck')
        _, friend = world.join_room(code, 'ShitLord')
        self.assertEqual(world.rooms[code]['players'][host]['name'], 'Adventurer')
        self.assertEqual(world.rooms[code]['players'][friend]['name'], '****Lord')
        world.action(code, friend, {'action':'chat', 'message':'you idiot, help'})
        for pid in (host, friend):
            message = world.state(code, pid)['chat'][-1]
            self.assertEqual(message['message'], 'you *****, help')
            self.assertEqual(message['name'], '****Lord')
        self.assertEqual(clean_name('\n\u200b'), 'Adventurer')
