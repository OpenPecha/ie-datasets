import jsonpickle as jp
from pathlib import Path

from pybo import BoPipeline
jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False)


# TODO: Once sentencify and paragraphy are released in pybo, remove this code here and call it directly from pybo
ending_particles = ['གོ་', 'ངོ་', 'དོ་', 'ནོ་', 'བོ་', 'མོ་', 'འོ་', 'རོ་', 'ལོ་', 'སོ་', 'ཏོ་']
ending_words = ['ཅིག་', 'ཤོག་']
ending_verbs = ['ཡིན་', 'ཡོད་', 'མིན་', 'མེད་', 'འགྱུར་', 'ལྡན་', 'བགྱི་', 'བྱ་']
clause_boundaries = ['སྟེ་', 'ཏེ་', 'དེ་', 'ནས་', 'ན་']
dagdra = ['པ་', 'བ་', 'པོ་', 'བོ་']


def is_word(token):
    return token and token.type == 'syl'


def has_last_syl(token, l):
    if token.syls:
        last_syl = ''.join([token.content[c] for c in token.syls[-1]]) + '་'
        return last_syl in l
    else:
        return False


def is_ending_part(token):
    return token and token.pos == 'PART' \
           and has_last_syl(token, ending_particles)


def is_endpart_n_punct(token1, token2):
    return is_ending_part(token1) and token2.pos == 'punct'


def is_clause_boundary_n_punct(token1, token2):
    return (has_last_syl(token1, clause_boundaries)
            or has_last_syl(token1, ending_words))\
           and token2.pos == 'punct'


def is_verb_n_punct(token1, token2):
    return ((token1.pos == 'VERB' and not has_last_syl(token1, dagdra))
            or has_last_syl(token1, ending_verbs)) \
           and token2.pos == 'punct'


def is_verb_n_clause_boundary(token1, token2):
    return ((token1.pos == 'VERB' and not has_last_syl(token1, dagdra))
            or has_last_syl(token1, ending_verbs)) \
           and has_last_syl(token2, clause_boundaries)


def extract_chunks(test, subtokens, start, previous_end):
    chunks = []
    n = 0
    for n, token in enumerate(subtokens):
        if test(subtokens[n - 1], token):
            chunks.append({'start': previous_end, 'end': start + n, 'len': start + n + 1 - previous_end})
            previous_end = start + n + 1
    if chunks and previous_end < start + n:
        chunks.append({'start': previous_end, 'end': start + n, 'len': start + n + 1 - previous_end})

    return chunks


def piped_sentencify(sentences, tokens, test, threshold=None):
    a = 0
    while a < len(sentences):
        length, start, end = sentences[a]['len'], sentences[a]['start'], sentences[a]['end']
        previous_end = start
        new_sentences = []
        if threshold:
            if end - start > threshold:
                new_sentences = extract_chunks(test, tokens[start:end + 1], start, previous_end)
        else:
            new_sentences = extract_chunks(test, tokens[start:end + 1], start, previous_end)

        if new_sentences:
            sentences[a:a + 1] = new_sentences
            a += len(new_sentences)
        else:
            a += 1
    return sentences


def join_no_verb_sentences(sentences, tokens, threshold=4):
    i = 0
    while i < len(sentences):
        start, end, length = sentences[i]['start'], sentences[i]['end'], sentences[i]['len']
        if length > threshold:
            i += 1
            continue

        no_verb = True
        for token in tokens[start:end + 1]:
            if token.pos == 'VERB' and not has_last_syl(token, dagdra):
                no_verb = False

        if no_verb:
            last_word = tokens[end] if tokens[end].type == 'syl' else tokens[end - 1]
            if i + 1 < len(sentences) and has_last_syl(last_word, clause_boundaries):
                # join to the left
                sentences[i + 1]['start'] = sentences[i]['start']
                sentences[i + 1]['len'] += sentences[i]['len']
                del sentences[i]
                i -= 1
            elif i - 1 >= 0:
                # join to the right
                last_word_of_previous = tokens[sentences[i-1]['end']] if tokens[sentences[i-1]['end']].type == 'syl' else tokens[sentences[i-1]['end'] - 1]
                if not has_last_syl(last_word_of_previous, ending_particles):
                    sentences[i - 1]['end'] = sentences[i]['end']
                    sentences[i - 1]['len'] += sentences[i]['len']
                    del sentences[i]
                    i -= 1

        i += 1

    return sentences


def get_sentence_indices(tokens):
    """
    from 1 to 3, we want to use the shad since it reflects the writer's own idea of where parts of the
    sentence end and start.
    1. ending particle + shad to not take all the quotations that potentially contain ending particles

    2. clause boundary particles + shad: ན་ is often found within a sentence, but cuts it in a way that doesn't prevent
    the correct understanding, so for translation, we might want to remove it as translation units will want
    to keep those sentences together, but for segmentation jobs, it works as a fairly safe segmenter.
    we might want to use it.

    Output: list of sentences, each in the following format: (sentence-length, [word1, word2, ...])
    """
    # 1. find unambiguous sentence end markers: ending particles followed by punctuation
    previous_end = 0
    sentence_idx = extract_chunks(is_endpart_n_punct, tokens, 0, previous_end)

    # 2. find clause boundaries followed by punctuation
    sentence_idx = piped_sentencify(sentence_idx, tokens, is_clause_boundary_n_punct)

    # 3. find verbs followed by punctuation
    sentence_idx = piped_sentencify(sentence_idx, tokens, is_verb_n_punct)

    # 4. find verbs followed by clause boundaries
    sentence_idx = piped_sentencify(sentence_idx, tokens, is_verb_n_clause_boundary, threshold=30)  # max size to check

    # joining the sentences without verbs to either the one preceding them or following them
    sentence_idx = join_no_verb_sentences(sentence_idx, tokens)

    return sentence_idx


def sentencify(tokens):
    sent_indices = get_sentence_indices(tokens)
    # get tokens for each sentence
    sentences = []
    for sentence in sent_indices:
        start, end, l = sentence['start'], sentence['end'], sentence['len']
        sentences.append((l, tokens[start:end + 1]))

    return sentences


def paragraphify(tokens):
    threshold = 70
    paragraph_max = 150
    sent_indices = get_sentence_indices(tokens)

    # join small sentences to form paragraphs
    i = 0
    while i < len(sent_indices):
        start, end, l = sent_indices[i]['start'], sent_indices[i]['end'], sent_indices[i]['len']
        if i > 0 and l < threshold:
            previous_len = sent_indices[i - 1]['len']
            if l + previous_len < paragraph_max:
                sent_indices[i - 1]['end'] = sent_indices[i]['end']
                sent_indices[i - 1]['len'] += sent_indices[i]['len']
                del sent_indices[i]
                i -= 1
        i += 1

    # get tokens for each sentence
    sentences = []
    for sentence in sent_indices:
        start, end, l = sentence['start'], sentence['end'], sentence['len']
        sentences.append((l, tokens[start:end + 1]))

    return sentences


def format_sentences_for_lighttag(sentences):
    output = []
    for i, sent in enumerate(sentences):
        sent_str = ''.join([token.content for token in sent[1]])
        sentence = {'ex': sent_str, 'order': i}
        output.append(sentence)

    return jp.dumps(output)


def format_to_csv(sentences):
    output = []
    for sent in sentences:
        sent_str = ''.join([token.content for token in sent[1]])
        output.append((sent[0],sent_str))

    output = sorted(output, key=lambda x: x[0], reverse=True)

    return '\n'.join([f'{a[0]},{a[1]}' for a in output])


if __name__ == '__main__':
    pipeline = BoPipeline('dummy',
                          'pybo',
                          ('pybo_sentences', paragraphify),
                          format_to_csv,
                          pybo_profile='GMD')

    tokens = pipeline.pipe_file('verses.txt', 'lighttag')
    in_str = 'འདི་ལ་ཡང་གཟུང་བའི་ཆ་ཡོད་ན་ཤེས་པ་ཡོད་ལ་མེད་ན་མེད་དེ། དེ་ལྟ་བས་ན་ལྷན་ཅིག་འབྱུང་བ་དེ་གཉིས་ཀྱང་རྒྱུ་དང་རྒྱུ་དང་ལྡན་པ་ཉིད་དུ་འགྲུབ་པོ། །གཏན་ཚིགས་པ་དག་ཅེས་བྱ་བ་ནི་གང་དག་གཏན་ཚིགས་ཀྱི་ཐ་སྙད་འདོགས་པ་དེ་དག་ནི་གཏན་ཚིགས་པ་དག་སྟེ། རྟོག་གེ་བ་ཞེས་བྱ་བའི་ཐ་ཚིག་གོ། །དེ་དང་ལྡན་པ་ཉིད་ཅེས་བྱ་བ་ནི་ཡོད་པ་དང་མེད་པ་དང་ལྡན་པ་ཉིད་དོ། །རྒྱུ་དང་རྒྱུ་དང་ལྡན་པ་ཞེས་བྱ་བ་ནི་རྒྱུ་དང་འབྲས་བུ་དག་ཅེས་བྱ་བའི་དོན་ཏོ། །'
    print(pipeline.pipe_str(in_str))
    print('ok')
