"""Explicit Drain comparison recipes; zero preserves the released game."""
import os

STYLE_NAMES = {
    1: 'Crown of Sludge',
    2: 'Crooked Brassworks',
    3: 'Moonlit Cistern',
    4: 'Rotten Reliquary',
    5: 'Royal Drains',
}
CATEGORIES = ('floor', 'masonry', 'water', 'metal', 'bridge', 'market',
              'sanctum', 'props', 'peddler', 'wizard')


def recipe(number):
    number = int(number)
    assert 0 <= number <= 8, ('BART_SEWER must be 0..8', number)
    if not number:
        return None
    if number <= 5:
        return {'id': number, 'name': STYLE_NAMES[number], 'style': number,
                **{category: number for category in CATEGORIES}}
    mixed = {
        6: ('Royal masonry / crooked market', 5,
            {'floor': 5, 'masonry': 5, 'water': 3, 'metal': 1, 'bridge': 2,
             'market': 2, 'sanctum': 3, 'props': 4, 'peddler': 2, 'wizard': 3}),
        7: ('Moonlit stone / crown brass', 3,
            {'floor': 3, 'masonry': 3, 'water': 2, 'metal': 1, 'bridge': 5,
             'market': 5, 'sanctum': 1, 'props': 2, 'peddler': 5, 'wizard': 1}),
        8: ('Reliquary grime / royal crossing', 4,
            {'floor': 4, 'masonry': 1, 'water': 4, 'metal': 5, 'bridge': 5,
             'market': 3, 'sanctum': 4, 'props': 4, 'peddler': 1, 'wizard': 5}),
    }
    name, base, components = mixed[number]
    return {'id': number, 'name': name, 'style': base, **components}


VARIANT = int(os.environ.get('BART_SEWER', '0'))
RECIPE = recipe(VARIANT)
