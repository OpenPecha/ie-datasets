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
    pipes1 = {'pre': {'remove_returns': basic_cleanup},
              'proc': {'merge_spaces': merge_spaces},
              'frm': {'lighttag_raw': lighttag_raw}}

    profile1 = {'lighttag_base':
                    {'pre': 'remove_returns',
                     'tok': 'syls',
                     'proc': 'merge_spaces',
                     'frm': 'lighttag_raw'}}

    return BoPipeline(profile=profile1, new_pipes=pipes1)


def lighttag_suggestion_pipeline():
    # pre: remove all \n and add space instead (keep_returns)
    # tok: syls
    # proc: ??? (process)
    # frm: json_maker
    pipes2 = {'pre': {'keep_returns': keep_returns},
              'proc': {'lighttag_suggestions': process},
              'frm': {'json_maker': json_maker}}

    profile2 = {'lighttag_suggestions':
                    {'pre': 'keep_returns',
                     'tok': 'syls',
                     'proc': 'lighttag_suggestions',
                     'frm': 'json_maker'}}

    return BoPipeline(profile=profile2, new_pipes=pipes2)


pipeline1 = lighttag_base_pipeline()
pipeline2 = lighttag_suggestion_pipeline()


pipeline1.pipe_file('soas-segmentation/mdzangs_blun.txt', 'lighttag/totag/')
# pipeline2.pipe_file('soas-segmentation/mdzangs_blun.txt', 'lighttag/totag/')