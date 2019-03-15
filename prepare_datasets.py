import jsonpickle as jp
from pathlib import Path

from pybo import BoPipeline
jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False)

ending_particles = ['གོ་', 'ངོ་', 'དོ་', 'ནོ་', 'བོ་', 'མོ་', 'འོ་', 'རོ་', 'ལོ་', 'སོ་', 'ཏོ་']
clause_boundaries = ['སྟེ་', 'ཏེ་', 'དེ་', 'ནས་', 'ན་']
quote_particle = ['ཅེས་', 'ཞེས་']
shad = '།'


def is_word(token):
    return token and token.type == 'syl'


def is_ending_part(token):
    return token and token.pos == 'PART' and token.cleaned_content in ending_particles


def is_endpart_n_shad(token1, token2):
    return is_ending_part(token1) and shad in token2.content


def is_clause_boundary_n_shad(token1, token2):
    return token1.cleaned_content in clause_boundaries and shad in token2.content


def extract_chunks(test, subtokens, start, previous_end):
    chunks = []
    n = 0
    for n, token in enumerate(subtokens):
        if test(subtokens[n - 1], token):
            chunks.append({'start': previous_end, 'end': start + n, 'len': start + n - previous_end})
            previous_end = start + n + 1
    if chunks and previous_end < start + n:
        chunks.append({'start': previous_end, 'end': start + n, 'len': start + n - previous_end})

    return chunks


def get_token_str(sentence_idx, tokens):
    sentences = []
    for sentence in sentence_idx:
        start, end, l = sentence['start'], sentence['end'], sentence['len']
        sentences.append((l, tokens[start:end + 1]))

    return sentences


def sentencify(tokens):
    """
    from 1 to 3, we want to use the shad since it reflects the writer's own idea of where parts of the
    sentence end and start.
    1. ending particle + shad to not take all the quotations that potentially contain ending particles

    2. clause boundary particles  + shad: ན་ is often found within a sentence, but cuts it in a way that doesn't prevent
    the correct understanding, so for translation, we might want to remove it as translation units will want
    to keep those sentences together, but for segmentation jobs, it works as a fairly safe segmenter.
    we might want to use it.

    Output: list of sentences, each in the following format: (sentence-length, [word1, word2, ...])
    """
    # 1. find unambiguous sentence end markers: ending particles followed by shads
    previous_end = 0
    sentence_idx = extract_chunks(is_endpart_n_shad, tokens, 0, previous_end)

    # 2. find clause boundaries followed by shads
    a = 0
    while a < len(sentence_idx):
        length, start, end = sentence_idx[a]['len'], sentence_idx[a]['start'], sentence_idx[a]['end']
        previous_end = start
        new_sentences = extract_chunks(is_clause_boundary_n_shad, tokens[start:end + 1], start, previous_end)

        if new_sentences:
            sentence_idx[a:a+1] = new_sentences
            a += len(new_sentences)
        else:
            a += 1

    sentences = get_token_str(sentence_idx, tokens)
    return sentences


def format_sentences_for_lighttag(sentences):
    output = []
    for i, sent in enumerate(sentences):
        sent_str = ''.join([token.content for token in sent[1]])
        sentence = {'ex': sent_str, 'order': i}
        output.append(sentence)

    return jp.dumps(output)


if __name__ == '__main__':
    pipeline = BoPipeline('dummy',
                          'pybo',
                          ('pybo_sentences', sentencify),
                          ('lighttag_sentences', format_sentences_for_lighttag),
                          pybo_profile='GMD')

    in_str = "། མཛངས་བླུན་ཞེས་བྱ་བའི་མདོ། །བམ་པོ་དང་པོའོ། དཔེར་སྣ་ཚོགས་བསྟན་པའི་ལེའུ། འདི་སྐད་བདག་གིས་ཐོས་པའི་དུས་གཅིག་ན། " \
             "བཅོམ་ལྡན་འདས་ཡུལ་མ་ག་དྷཱའི་དཀྱིལ་འཁོར་རྣམ་པར་རྒྱལ་བ་ན་བཞུགས་ཏེ། མངོན་པར་རྫོགས་པར་སངས་རྒྱས་ནས། " \
             "རིང་པོར་མ་ལོན་པ་ཞིག་ན་འདི་སྙམ་དུ་དགོངས་པར་གྱུར་ཏོ། །སེམས་ཅན་འདི་དག་ནི་ཡུན་རིང་པོ་ནས་ཕྱིན་ཅི་ལོག་གིས་ཡོངས་སུ་བསླད་དེ། " \
             "བསྟན་ཅིང་བཅོས་སུ་ཡང་ཤིན་ཏུ་དཀའ་བས། ཇི་སྲིད་དུ་འཇིག་རྟེན་ན་བཞུགས་ཀྱང་ཕན་པའི་དོན་མེད་ཀྱིས། " \
             "དེས་ན་ལྷག་མ་མ་ལུས་པའི་མྱ་ངན་ལས་འདའ་བས་ཡོངས་སུ་མྱ་ངན་ལས་འདའོ་སྙམ་དུ་དགོངས་མ་ཐག་ཏུ། " \
             "དེའི་ཚེ་ན་ཚངས་རིས་ཀྱི་ལྷ་རྣམས་ཀྱིས་བཅོམ་ལྡན་འདས་ཀྱི་དགོངས་པ་ཤེས་ཤིང་རྟོགས་ནས། ནམ་མཁའ་ལས་བབས་ཏེ། བཅོམ་ལྡན་འདས་གང་ན་བ་དེར་ལྷགས་ནས། " \
             "དེར་ཕྱིན་པ་དང་། ཞབས་ལ་མགོ་བོས་ཕྱག་འཚལ་ནས་ཐལ་མོ་སྦྱར་ཏེ། བཅོམ་ལྡན་འདས་ལ་ཆོས་ཀྱི་འཁོར་ལོ་བསྐོར་བར་གསོལ་ཞིང་བསྐུལ་བ་དང་། " \
             "དེ་ལ་བཅོམ་ལྡན་འདས་ཀྱིས་འདི་སྐད་ཅེས་བཀའ་སྩལ་ཏེ། ཚངས་རིས་ཀྱི་ལྷ་དག་སེམས་ཅན་འགྱུརའདི་དག་ཉེས་པའི་དྲི་མས་ཡོངས་སུ་གླགས་ཏེ། " \
             "འཇིག་རྟེན་གྱི་བདེ་བ་ལ་ཆགས་ནས། ཤེས་རབ་དང་ལྡན་པའི་སེམས་མེད་པས། ཅི་སྲིད་དུ་འཇིག་རྟེན་ན་བཞུགས་ཀྱང་བྱ་བ་དོན་མེད་པར་འགྱུར་ཏེ། " \
             "མྱ་ངན་ལས་འདས་ན་བདེའོ་སྙམ་དུ་དགོངས་སོ། །དེ་ནས་ཚངས་རིས་ཀྱི་ལྷ་རྣམས་ཀྱིས། ཡང་བཅོམ་ལྡན་འདས་ལ་འདི་སྐད་ཅེས་གསོལ་ཏོ། །" \
             "བཅོམ་ལྡན་འདས་ཆོས་ཀྱི་རྒྱ་མཚོ་ཡོངས་སུ་གང་བ། ཆོས་ཀྱི་རྒྱལ་མཚན་བཙུགས་པ་བསྟན་ཅིང་འདུལ་བའི་དུས་ལ་ཡང་བབ། སེམས་ཅན་འདི་དག་ལས་གྲོལ་བར་འགྱུར་བ་ཡང་ཤིན་ཏུ་མང་ན། " \
             "ཅིའི་སླད་དུ་བཅོམ་ལྡན་འདས་མྱ་ངན་ལས་འདས་པར་དགོངས་ཏེ། ཤིན་ཏུ་མདོངས་པར་གྱུར་པ་འདི་དག་གི་མགོན་དང་སྐྱབས་མི་མཛད། " \
             "བཅོམ་ལྡན་འདས་ནི་སྔོན་བསྐལ་པ་གྲངས་མ་མཆིས་པ་འདས་པའི་ཕ་རོལ་ན། སེམས་ཅན་གྱི་དོན་དུ་ཐོས་པ་ཚོལ་ཞིང་ཚོལ་བ་ན། " \
             "ཆུང་ངུ་ན་ཚིགས་སུ་བཅད་པ་གཅིག་ཙམ་གྱི་སླད་དུ་ཡང་བདག་གི་ལུས་དང་། ཆུང་མ་དང་། བུ་དང་། བུ་མོ་དང་། ཅིའི་སླད་དུ་མགོན་མ་མཆིས་པ་འདི་དག་ཡོངས་སུ་བཏང་བར་དགོངས། " \
             "སྔོན་འདས་པའི་དུས་ཡུན་རིང་པོ་ན། འཛམ་བུའི་གླིང་འདིར་རྒྱལ་པོ་ཆེན་པོ་ཁ་དོག་དམ་པ་བགྱི་བ། འཇིག་རྟེན་འདི་ལ་དབང་སྒྱུར་བ་ཞིག་བྱུང་སྟེ། རྒྱལ་པོ་དེ་ལ་རྒྱལ་ཕྲན་ནི་བརྒྱད་ཁྲི་བཞི་སྟོང་མངའ། " \
             "ལྗོངས་ཆེན་པོ་སྟོང་ཕྲག་དྲུག་ཅུའི་ནང་ན༑ གྲོང་ཁྱེར་ཡང་ཁྲི་ཕྲག་བཅུ་ཅུ་མངའ་སྟེ། རྒྱལ་པོ་དེ་ལ་བཙུན་མོ་ནི་སྟོང་ཕྲག་ཉི་ཤུ། བློན་པོ་ཆེན་པོ་ནི་སྟོང་ཕྲག་བཅུ་སྙེད་མངའོ། །" \
             "རྒྱལ་པོ་ཁ་དོག་དམ་པ་དེའི་གཟི་བརྗིད་དང་། མཐུ་དཔེ་མ་མཆིས་པ་ཆེ་སྟེ། འབྱོར་པ་དང་། བདེ་བ་དང་། ལོ་ལེགས་པ་དང་། མི་ལ་སོགས་པ་སྐྱེ་བོ་མང་ཞིང་རབ་ཏུ་མང་བ་དང་ལྡན་པ་དེས་འདི་སྙམ་དུ་བསམས་ཏེ། " \
             "བདག་གིས་ནི་རིན་པོ་ཆེ་དང་། ལོངས་སྤྱོད་ཀྱིས་འགྲོ་བ་ཐམས་ཅད་ལ་ཕན་བཏགས་ཀྱིས་དམ་པའི་ཆོས་ཀྱི་ཕན་འདོགས་པར་མ་གྱུར་ཏེ། འདི་དག་ནི་བདག་གི་སྐྱོན་དུ་འགྱུར་གྱིས། " \
             "དམ་པའི་ཆོས་གང་ན་མཆིས་པ་བཙལ་ཏེ། ཐམས་ཅད་དགྲོལ་བར་བྱའོ་སྙམ་དུ་བསམས་ནས། འདི་སྐད་ཅེས་བཀར་བཏགས་སོ། འཛམ་བུའི་གླིང་འདི་ན་སུ་ལ་དམ་པའི་ཆོས་ཡོད་པ་དེ། " \
             "བདག་ལ་སྟོན་པར་གྱུར་ན། དེ་ཡིད་དང་མི་འགལ་བར་ཅི་དང་ཅི་འདོད་པར་སྦྱིན་ནོ་ཞེས་བསྒྲགས་ཀྱང་སྟོན་ནུས་པ་མ་བྱུང་ངོ་། དེའི་ཚེ་ན་རྒྱལ་པོ་དེ་མྱ་ངན་གྱིས་ཡིད་གདུངས་ཏེ། " \
             "མི་དགའ་བར་གྱུར་པ་ངལ་བསོ་པོས་ཐོས་ནས་སད་པའི་སླད་དུ། བདག་གིས་ལུས་གནོད་སྦྱིན་ཞིག་ཏུ་སྤྲུལ་ནས། དེའི་མདོག་ཤིན་ཏུ་སྔོ་བ། གནག་པ། མིག་ཁྲག་ལྟར་དམར་བ། " \
             "མཆེ་བ་གྱེན་དུ་བྱུང་བ། སྐྲ་གྱེན་དུ་བསྒྲེང་བ། ཁ་ནས་མེ་འབར་བ། ཕོ་བྲང་གི་སྒོར་མཆིས་ནས། སུ་ཞིག་ཆོས་ཐོས་པར་འདོད་པ་ང་ལས་ཉོན་ཅིག་ཅེས་སྨྲས་སོ། །རྒྱལ་པོས་དེ་སྐད་ཅེས་སྨྲས་པ་ཐོས་ནས། " \
             "ཤིན་ཏུ་དགའ་མགུ་སྟེ། གནོད་སྦྱིན་དེ་བསུ་ནས་མགོ་བོས་ཕྱག་བྱས་ཏེ། སྟན་མཐོན་པོ་ལ་བཞག་ནས། བློན་པོ་དང་། འཁོར་མང་པོ་དག་བསྡུས་ཏེ། ཆོས་ཉན་དུ་གཞུག་པའི་སླད་དུ་འཁོར་བར་བསྐོར་ཏོ། །" \
             "དེའི་ཚེ་ན་གནོད་སྦྱིན་གྱིས་རྒྱལ་པོ་ལ་འདི་སྐད་ཅེས་སྨྲས་སོ། །རྒྱལ་པོ་ཆོས་ཐོས་པར་བྱ་བ་ནི་ཤིན་ཏུ་དཀའ་བས། ཆོས་ཉན་པར་འདོད་ན། འདི་ཙམ་གྱིས་ཆོག་པ་མ་ཡིན་ནོ། །ཞེས་སྨྲས་པ་དང་། " \
             "རྒྱལ་པོས་དེ་ལ་ཐལ་མོ་སྦྱར་ཏེ། ཁྱོད་ཅི་དང་ཅི་འདོད་པ་དེ་མི་འགལ་བར་ཐམས་ཅད་སྦྱིན་ནོ་ཞེས་སྨྲས་སོ། །དེ་ནས་གནོད་སྦྱིན་དེས་རྒྱལ་པོ་ལ་སྨྲས་པ། རྒྱལ་པོ་ཁྱོད་ཀྱི་བཙུན་མོ་དང་སྲས་གང་ཐིངས་པ། " \
             "ཁོ་བོ་ཟར་བཅུག་ན། དམ་པའི་ཆོས་སྦྱིན་ནོ་ཞེས་སྨྲས་པ་དང་། དེའི་ཚེ་ན་རྒྱལ་པོ་ཆེན་པོ་དེས་བཙུན་མོའི་ནང་ན་གང་ཕངས་པ་དང་། སྲས་ཀྱི་མཆོག་གནོད་སྦྱིན་ལ་ཕུལ་ཏེ། " \
             "གནོད་སྦྱིན་གྱིས་འཁོར་མང་པོའི་ནང་དུ་ཀུན་གྱིས་མཐོང་བཞིན་དུ་ཟོས་སོ། །དེའི་ཚེ་ན་རྒྱལ་པོ་དེའི་བློན་པོ་རྣམས་དེ་ལྟར་གྱུར་པ་མཐོང་ནས། ཆོ་ངེས་བཏབ་སྟེ། " \
             "ས་ལ་འགྲེ་བཞིན་དུ་རྒྱལ་པོ་ཆེན་པོ་མི་རིགས་པའི་ལས་འདི་ལྟ་བུ་དག་ཐོང་ཤིག་ཅེས་གསོལ་བ་བཏབ་ཀྱང་། རྒྱལ་པོ་དེ་དམ་པའི་ཆོས་ཚོལ་བའི་ཕྱིར་ཤིན་ཏུ་བརྣན་པས་བཟློག་མ་ནུས་སོ། །" \
             "དེའི་ཚེ་ན་གནོད་སྦྱིན་དེས་རྒྱལ་པོའི་བཙུན་མོ་དང་སྲས་ཟོས་ནས། ཚིགས་སུ་བཅད་པ་འདི་སྐད་ཅེས་སྨྲས་སོ། །འདུ་བྱེད་ཐམས་ཅད་མི་རྟག་སྟེ། ཇི་ཙམ་སྐྱེ་བ་སྡུག་བསྔལ་བཅས། ལྔ་ཕུང་མཚན་མ་མེད་པས་སྟོང་། །" \
             "བདག་དང་བདག་གི་བ་ཡང་མེད། ཚིགས་སུ་བཅད་པ་འདི་སྨྲས་པ་དང་། རྒྱལ་པོ་དགའ་མགུ་རངས་ཏེ། བ་སྤུའི་ཉག་མ་ཙམ་གྱི་འགྱོད་པའི་སེམས་མ་སྐྱེས་སོ། །དེ་ནས་ཡི་གེར་བྲིས་ནས། འཛམ་བུའི་གླིང་ཀུན་ཏུ་བསྒྲགས་ཏེ། " \
             "ཐམས་ཅད་སློབ་ཏུ་བཅུག་གོ། །དེ་ནས་ངལ་བསོ་པོས་བདག་ཉིད་ཀྱི་ལུས་སུ་སླར་བསྒྱུར་ནས་ཤིན་ཏུ་ལེགས་སོ་ངོ་མཚར་རྨད་དོ་ཞེས་བསྟོད་ཅིང་བསྔགས་ཏེ། རྒྱལ་པོའི་བཙུན་མོ་དང་། སྲས་ཀྱང་སྔོན་བཞིན་དུ་ཅང་མ་ནོངས་སོ། །"

    tokens = pipeline.pipe_str(in_str)
    Path('lighttag/test.json').write_text(tokens)
