from random import choice, choices, randint, random, sample, shuffle

# taken as-is from https://github.com/JRHard771/NameGenerator

PHONEMES = {}
PHO_CON = []
PHO_VOW = []

class Phoneme:
    def __init__(self, key, **kwargs):
        self.start = [key]
        self.mid = [key]
        self.end = [key]
        self.vowel = False
        self.no_start = False
        self.no_mid = False
        self.no_end = False
        for keyword in kwargs:
            self.__setattr__(keyword, kwargs[keyword])
        PHONEMES[key] = self
        if self.vowel:
            PHO_VOW.append(self)
        else:
            PHO_CON.append(self)

Phoneme('A', start=['a'], mid=['a','ai','a_e'], end=['a','ae','ay'], vowel=True)
Phoneme('a', vowel=True)
Phoneme('b')
Phoneme('k', start=['c','k'], end=['c','ck','k'])
Phoneme('d')
Phoneme('E', start=['e', 'ee', 'ea'], mid=['e','e_e','ea','ie'],
        end=['e','ie','y'], vowel=True)
Phoneme('e', mid=['e','ea'], no_end=True, vowel=True)
Phoneme('f', start=['f','ph'], mid=['f','ph'], end=['f','ph'])
Phoneme('g')
Phoneme('h')
Phoneme('I', start=['i','ai'], mid=['i_e','igh','y'], end=['ai','ie','igh','ye'],
        vowel=True)
Phoneme('i', no_end=True, vowel=True)
Phoneme('j', start=['j','g'], mid=['dge','j','g'], end=['dge'])
Phoneme('l')
Phoneme('m', end=['m','mn'])
Phoneme('n', start=['n','gn','kn'])
Phoneme('O', start=['o', 'oa'], mid=['o','o_e','oa'], end=['o','oe','oah'],
        vowel=True)
Phoneme('o', vowel=True)
Phoneme('p')
Phoneme('kw', start=['qu'], no_mid=True, no_end=True)
Phoneme('r', start=['r','wr'])
Phoneme('s', start=['s','sc','ce','ci','cy'], mid=['s','c'], end=['s','ce'])
Phoneme('t')
Phoneme('U', end=['u_e','ew'], vowel=True)
Phoneme('u', start=['a','u'], mid=['u','o'], no_end=True, vowel=True)
Phoneme('v')
Phoneme('w')
Phoneme('ks', mid=['x','xc'], end=['x'], no_start=True)
Phoneme('y')
Phoneme('z')
Phoneme('oo', mid=['oo','u'], end=['oo','u_e','ew'], vowel=True)
Phoneme('oi', mid=['oi','oy'], end=['oy'], no_start=True, vowel=True)
Phoneme('ou', start=['ou','ow'], mid=['ou'], end=['ow'], vowel=True)
Phoneme('aw', start=['aw','au'], mid=['aw','au'], end=['aw','au'], vowel=True)
Phoneme('ar', mid=['_ar'], end=['_ar'])
Phoneme('sh')
Phoneme('wh', no_mid=True, no_end=True)
Phoneme('ch', mid=['ch','tch'], end=['ch','tch'])
Phoneme('th')
Phoneme('ng', mid=['ng','nk'], end=['ng','nk'], no_start=True)
Phoneme('er', start=['er','ur'], mid=['_er','_ir','_ur'], end=['_er','_ir','_ur'])

def generate_name(theme, syllables=2):
    next_vowel = False
    if random() < 0.5:
        name = choices(theme.c_start, theme.c_start_weight)[0]
        next_vowel = True
    else:
        name = choices(theme.v_start, theme.v_start_weight)[0]
    syllables -= 1
    for i in range(syllables):
        if next_vowel:
            if i == syllables - 1:
                name += choices(theme.v_end, theme.v_end_weight)[0]
            else:
                name += choices(theme.v_mid, theme.v_mid_weight)[0]
        else:
            if i == syllables - 1:
                name += choices(theme.c_end, theme.c_end_weight)[0]
            else:
                name += choices(theme.c_mid, theme.c_mid_weight)[0]
        next_vowel = not next_vowel
    name = name.replace('_',choices(theme.c_mid, theme.c_mid_weight)[0])
    name = name.replace('_','')
    return name.title()


def generate_dialogue(theme):
    words = []
    length = randint(3,9)
    for i in range(length):
        words.append(generate_name(theme,choice([2,3,3,4,4,5])))
        if i > 0 and not caps:
            words[i] = words[i].lower()
        caps = False
        if i == length - 1 or random() < 0.25:
            punc = choice(',.?!')
            if punc == ',' and i == length - 1:
                punc = '.'
            words[i] = words[i] + punc
            if punc != ',':
                caps = True
    return ' '.join(words)

class Theme:
    def __init__(self):
        self.reset()

    def reset(self):
        self.consonants = sample(PHO_CON, 9)
        self.vowels = sample(PHO_VOW, 5)
        self.c_start = []
        self.c_start_weight = []
        self.c_mid = []
        self.c_mid_weight = []
        self.c_end = []
        self.c_end_weight = []
        self.v_start = []
        self.v_start_weight = []
        self.v_mid = []
        self.v_mid_weight = []
        self.v_end = []
        self.v_end_weight = []
        w = 1
        for p in self.consonants:
            if not p.no_start:
                self.c_start.append(choice(p.start))
                self.c_start_weight.append(w)
            if not p.no_mid:
                self.c_mid.append(choice(p.mid))
                self.c_mid_weight.append(w)
            if not p.no_end:
                self.c_end.append(choice(p.end))
                self.c_end_weight.append(w)
            w += 1
        w = 1
        for p in self.vowels:
            if not p.no_start:
                self.v_start.append(choice(p.start))
                self.v_start_weight.append(w)
            if not p.no_mid:
                self.v_mid.append(choice(p.mid))
                self.v_mid_weight.append(w)
            if not p.no_end:
                self.v_end.append(choice(p.end))
                self.v_end_weight.append(w)
            w += 1