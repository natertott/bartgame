"""Drain recipes: nine is the final room; zero retains the original room art."""
import os

STYLE_NAMES = {
    1: 'Ashlar & Amber',
    2: 'Crooked Brickwork',
    3: 'Floodworn Flags',
    4: 'Crumbling Vault',
    5: 'Silted Cloister',
}
CATEGORIES = ('floor', 'masonry', 'water', 'metal', 'bridge', 'market',
              'sanctum', 'props', 'peddler', 'wizard')


def recipe(number):
    number = int(number)
    assert 0 <= number <= 9, ('BART_SEWER must be 0..9', number)
    if not number:
        return None
    if number <= 5:
        return {'id': number, 'name': STYLE_NAMES[number], 'style': number,
                **{category: number for category in CATEGORIES}}
    if number == 9:
        return {'id': 9, 'name': 'The Drain / selected final room', 'style': 1,
                'floor': 1, 'masonry': 3, 'water': 2, 'metal': 1,
                'bridge': 2, 'market': 1, 'sanctum': 2, 'props': 3,
                'peddler': 1, 'wizard': 1}
    mixed = {
        6: ('Cloister masonry / crooked market', 5,
            {'floor': 5, 'masonry': 5, 'water': 3, 'metal': 1, 'bridge': 2,
             'market': 2, 'sanctum': 3, 'props': 4, 'peddler': 2, 'wizard': 3}),
        7: ('Floodworn stone / amber brass', 3,
            {'floor': 3, 'masonry': 3, 'water': 2, 'metal': 1, 'bridge': 5,
             'market': 5, 'sanctum': 1, 'props': 2, 'peddler': 5, 'wizard': 1}),
        8: ('Vault grime / cloister crossing', 4,
            {'floor': 4, 'masonry': 1, 'water': 4, 'metal': 5, 'bridge': 5,
             'market': 3, 'sanctum': 4, 'props': 4, 'peddler': 1, 'wizard': 5}),
    }
    name, base, components = mixed[number]
    return {'id': number, 'name': name, 'style': base, **components}


VARIANT = int(os.environ.get('BART_SEWER', '9'))
RECIPE = recipe(VARIANT)
