from pybo import BoPipeline
import re
from pathlib import Path


def basic_cleanup(text: str) -> str:
    # used by base_pipeline
    text = text.strip()
    text = re.sub(r'\n\n', '_', text)
    text = re.sub(r'\n', '', text)
    return text


def keep_returns(text: str) -> str:
    # used by suggestion_pipeline
    text = text.strip()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', '_', text)
    return text


def process(tokens):
    # used by suggestion_pipeline
    content = ''
    annotations = []

    idx = 0
    start = 0
    end = 0
    annot = {}
    for token in tokens:
        idx += len(token)
        if '།' in token or '_' in token:
            content += token
            print('ok')
    return tokens


def merge_spaces(tokens):
    out = []
    for t in tokens:
        if t == '_':
            if not out:
                out.append(t)
            else:
                out[-1] = out[-1] + t
        else:
            out.append(t)
    return out


def lighttag_raw(tokens):
    return ''.join(tokens).replace('_', ' ')


def json_maker(tokens):
    # used by suggestion_pipeline
    out = ''

    return out


def lighttag_base_pipeline():
    # pre: remove all \n
    # tok: reuse bo_syl_tok
    # proc: spaces_plain_fulltext
    # frm: plaintext
    return BoPipeline(basic_cleanup,
                      'syls',
                      merge_spaces,
                      lighttag_raw)


def lighttag_suggestion_pipeline():
    # pre: remove all \n and add space instead (keep_returns)
    # tok: syls
    # proc: ??? (process)
    # frm: json_maker
    return BoPipeline(keep_returns,
                      'syls',
                      process,
                      json_maker)


pipeline1 = lighttag_base_pipeline()
pipeline2 = lighttag_suggestion_pipeline()


for f in Path('soas-segmentation/').glob('*.txt'):
    pipeline1.pipe_file(f, 'lighttag/totag/')
# pipeline2.pipe_file('soas-segmentation/mdzangs_blun.txt', 'lighttag/totag/')