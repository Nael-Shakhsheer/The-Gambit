import math
import unittest

import town_layout


class TownLayoutTests(unittest.TestCase):
    def test_seeded_layouts_vary_and_keep_every_service_and_spawn_accessible(self):
        kinds, styles = set(), set()
        for seed in range(80):
            village = town_layout.generate(seed)
            self.assertEqual(village, town_layout.generate(seed))
            houses = village['townLayout']
            kinds.add(village['townDecor']['layout'])
            styles.add(village['townDecor']['roadStyle'])
            self.assertEqual({h['id'] for h in houses}, {b[0] for b in town_layout.BUILDINGS})
            self.assertTrue(town_layout._valid_positions([(h['x'], h['y']) for h in houses]))
            for size in range(1, 5):
                for index in range(size):
                    self.assertTrue(town_layout.clear(houses, 480+(index-(size-1)/2)*42, 460, 23))
            ends = {tuple(path[-1]) for path in village['townPaths']}
            for house in houses:
                self.assertIn((house['x'], house['y']+47), ends)
            # Sample complete segments, including bends and the final door approach.
            for path in village['townPaths']:
                for a, b in zip(path, path[1:]):
                    samples = max(1, math.ceil(math.dist(a, b)/5))
                    for i in range(samples+1):
                        x, y = (a[j]+(b[j]-a[j])*i/samples for j in (0, 1))
                        self.assertTrue(town_layout.clear(houses, x, y), (seed, a, b))
        self.assertEqual(kinds, set(town_layout.LAYOUTS))
        self.assertEqual(styles, {'loop', 'lanes', 'branching'})

    def test_consecutive_visits_do_not_repeat_the_previous_shape(self):
        for previous in town_layout.LAYOUTS:
            for seed in range(7):
                village = town_layout.generate(seed, previous_layout=previous)
                self.assertNotEqual(village['townDecor']['layout'], previous)


if __name__ == '__main__':
    unittest.main()
