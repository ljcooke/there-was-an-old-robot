#!/usr/bin/env python3
"""
There Was an Old Woman Who Swallowed a Fly: Twitter Bot Edition

by Liam Cooke (@inky) Apr 2016

"""
import argparse
import random
import sys

import tracery
from tracery import modifiers
from tracery.modifiers import base_english


VERSES = 6

# Banned animals
BANIMALS = (
    'fly', # special case
    #'spider',  # rhymes with "inside her", but we've changed the gender
    'horse', # they're not dead, of course
    'hog', # what a hog! they swallowed a dog
)

# Tracery rules(!). The entries beginning with an underscore are filled in
# programmatically before running Tracery.
RULES = {
    'origin': '#_text#',  #'#_emoji# #_text#',

    'opening': 'There was an old robot who swallowed a fly.',
    'why_fly': "I don't know why #they# swallowed a fly. <br> Perhaps #they#'ll die.",
    'rip': "#they.capitalize#'re dead, of course.",

    'intro': 'There was an old robot who swallowed #_an_animal#.',

    'refrain': '#they.capitalize# swallowed #_an_animal##punc#',
    'refrain_exc': '#they.capitalize# swallowed #_an_animal#!',

    'desc_bird': 'How absurd! #refrain#',
    'desc_cat': [
        'Fancy that! #refrain#',
        'Imagine that! #refrain#',
    ],
    'desc_cow': "I don't know how #they# swallowed #_an_animal##punc#",
    'desc_dog': 'What a hog! #refrain#',
    'desc_fox': '#they_just.capitalize# opened the box and swallowed #_an_animal##punc#',
    'desc_goat': '#they_just.capitalize# opened #their# throat and swallowed #_an_animal##punc#',
    'desc_seal': 'Are you for real? #refrain_exc#',
    'desc_snail': [
        '#they_just.capitalize# lifted the veil and swallowed #_an_animal##punc#',
        'What a tale! #refrain#',
    ],

    'they_just': ['#they#', 'just'],

    'catch1': '#they.capitalize# swallowed the #_animal# to catch the #_animal2#...',
    'catch2': '...#they# swallowed the #_animal# to catch the #_animal2#...',

    'punc': ['!', '.'],
}

RHYMES = {
    'cat': """
        bat bat bat bat
        cat cat cat cat cat
        gnat
        rat rat rat
    """,

    'cow': """
        cow cow cow cow
        sow
    """,

    'bird': """
        bird bird bird bird bird
        nerd
    """,

    'dog': """
        dog dog dog
        frog frog
    """,

    'fox': """
        fox fox fox
        ox
    """,

    'goat': """
        goat goat goat goat
        stoat
    """,

    'seal': """
        eel
        seal
    """,

    'snail': """
        snail snail snail
        whale whale
    """,
}


def generate_animals(limit=VERSES):
    rhymes = list(RHYMES.items())
    random.shuffle(rhymes)
    for key, animals in rhymes[:limit]:
        yield key, random.choice(animals.split())


class Flycatcher(object):

    def __init__(self, animals=None, limit=VERSES):
        self.animals = animals or tuple(generate_animals(limit))
        self.emoji = '' #TODO

    def verses(self):
        yield self.verse('fly')

        for i in range(len(self.animals)):
            animals = self.animals[:i + 1]
            yield self.verse(animals)

        yield self.verse('horse')

    def verse(self, animals):
        """
        Generate a full list of tweets for a list of animals.

        """
        # Handle the opening and closing verses.
        if animals == 'fly':
            yield '{} <br> {}'.format(
                self.line('opening'),
                self.line('why_fly'),
            )
            return
        elif animals == 'horse':
            yield '{} <br> {}'.format(
                self.line('intro', 'horse'),
                self.line('rip'),
            )
            return

        # Here we handle a verse that introduces another animal.
        animals = tuple(reversed(animals))
        new_animal, old_animals = animals[0], animals[1:]

        # Introduce the animal with a description.
        key, animal = new_animal
        yield '{} <br> <i>{}</i>'.format(
            self.line('intro', animal),
            self.line('desc_' + key, animal),
        )

        # Revisit the other animals.
        old_animals = list(old_animals) + [(None, 'fly')]
        capital = True
        for prev_animal in old_animals:
            prev_key, prev_animal = prev_animal
            yield self.line('catch1' if capital else 'catch2',
                            animal, prev_animal)
            if prev_key and not random.randint(0, 3):
                yield '<exclaim>{}</exclaim>'.format(
                    self.line('desc_' + prev_key, prev_animal))
                capital = True
            else:
                capital = False
            animal = prev_animal

        # End the verse.
        yield self.line('why_fly')

    def line(self, text, animal=None, animal2=None):
        rules = RULES.copy()
        rules.update({
            '_text': '#%s#' % text,
            '_emoji': self.emoji,
            'they': 'they',
            'their': 'their',
            'them': 'them',
        })

        if animal:
            rules['_animal'] = animal
            rules['_an_animal'] = modifiers.a(animal)
        if animal2:
            rules['_animal2'] = animal2

        grammar = tracery.Grammar(rules)
        grammar.add_modifiers(base_english)

        result = grammar.flatten('#origin#')
        result = result.replace('...', '…')
        return result


def format_tex(verses, template=None):
    text = []
    for verse in verses:
        for line in verse:
            text.append(line + ' <br>\n')
        text.append('\n')

    text = ''.join(text).rstrip()
    text = text.replace('<br>\n\n', '\n\n')
    text = text.replace('<br>', r'\\')
    text = text.replace('<i>', r'\textit{').replace('</i>', '}')
    text = text.replace('…', r'\ldots ')
    text = text.replace('<exclaim>', r'\hspace{2em}---\textit{')
    text = text.replace('</exclaim>', r'}')

    if template:
        return template.replace('%VERSE%', text)
    else:
        return text

def format_tweets(verses):
    lines = []
    for verse in verses:
        for line in verse:
            line = ' '.join(line.replace('<br>', ' ').split())
            assert len(line) <= 140
            lines.append(line)
        lines.append('')

    text = '\n'.join(lines).rstrip()
    text = text.replace('<i>', '').replace('</i>', '')
    text = text.replace('<exclaim>', '').replace('</exclaim>', '')
    return text.strip()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()

    format_group = parser.add_argument_group('format options')
    excl_group = format_group.add_mutually_exclusive_group()
    excl_group.add_argument('-t', '--twitter', action='store_true',
                            help='plain text with one tweet per line')
    excl_group.add_argument('-x', '--tex', action='store_true',
                            help='TeX/LaTeX')

    tex_group = parser.add_argument_group('TeX options')
    tex_group.add_argument('-f', '--template',
                           help='TeX template file; must contain the magic '
                           'word: %%VERSE%%')

    args = parser.parse_args()
    verses = tuple(Flycatcher().verses())

    if args.tex:
        template = None
        if args.template:
            with open(args.template) as template_file:
                template = template_file.read()
        print(format_tex(verses, template))
    elif args.twitter:
        print(format_tweets(verses))
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
