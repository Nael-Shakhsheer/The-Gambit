"""Server-side English profanity/insult masking without substring false positives."""
import re
import unicodedata

# Whole words and common compounds. Ordinary words such as class, assassin,
# Scunthorpe and skill are deliberately not matched as substrings.
WORDS = (
    'fuck', 'fucking', 'fucked', 'fucker', 'fuckers', 'motherfucker', 'wtf',
    'shit', 'shitty', 'shithead', 'bullshit', 'bitch', 'bitches', 'bastard',
    'ass', 'asshole', 'arsehole', 'dumbass', 'jackass', 'piss', 'pissed',
    'cunt', 'cock', 'dick', 'dickhead', 'prick', 'damn',
    'slut', 'whore', 'idiot', 'idiots', 'idiotic', 'moron', 'stupid',
    'retard', 'retarded', 'faggot', 'fag', 'nigger', 'nigga',
    'kys', 'kill yourself', 'go die',
)
LEET = str.maketrans({'0':'o', '1':'i', '3':'e', '4':'a', '5':'s', '7':'t',
                     '@':'a', '$':'s', '!':'i'})
GAP = r'[^a-z0-9]*'
PATTERNS = [re.compile(r'(?<![a-z0-9])' + GAP.join(re.escape(c)+'+' for c in word if c != ' ')
                       + r'(?![a-z0-9])') for word in sorted(WORDS, key=len, reverse=True)]


def _visible(text):
    return ''.join(' ' if c.isspace() else c for c in str(text)
                   if c.isspace() or not unicodedata.category(c).startswith('C'))


def filter_text(text):
    text = _visible(text)
    normalized, positions = [], []
    for index, char in enumerate(text):
        # Recognize camel-case names without changing their display formatting.
        if index and char.isupper() and text[index-1].islower():
            normalized.append(' '); positions.append(index)
        substitutions = LEET
        if char in '@$!' and (index+1 == len(text) or not text[index+1].isalnum()
                              or char == '@' and (not index or not text[index-1].isalnum())):
            substitutions = {}
        for letter in unicodedata.normalize('NFKD', char).casefold().translate(substitutions):
            if unicodedata.category(letter).startswith('M'):
                continue
            normalized.append(letter); positions.append(index)
    searchable = ''.join(normalized)
    masked = set()
    for pattern in PATTERNS:
        for match in pattern.finditer(searchable):
            indices = positions[match.start():match.end()]
            masked.update(range(min(indices), max(indices)+1))
    return ''.join('*' if i in masked and not c.isspace() else c for i, c in enumerate(text))


def clean_name(name):
    cleaned = filter_text(' '.join(_visible(name).split()))[:18].strip()
    return cleaned if any(c.isalnum() for c in cleaned) else 'Adventurer'
