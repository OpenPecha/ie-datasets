import requests
from pybo import BoTokenizer
import json
import pandas as pd
from pprint import pprint
from requests.auth import HTTPBasicAuth


def prepare_to_suggest(config):
    # CONFIG
    # server
    LIGHTTAG_DOMAIN = config['domain']  # should be your lighttag domain
    LT_USERNAME = config['user']  # Username of manager user
    LT_PASSWORD = config['pwd']  # password of manager user
    # dataset
    DATASET_NAME = config['dataset']
    # schema
    SCHEMA_NAME = config['schema']

    # connect to the server
    SERVER = f'https://api-{LIGHTTAG_DOMAIN}.lighttag.io/'
    API_BASE = SERVER + 'api/v1/'

    response = requests.post(f"{SERVER}/auth/token/create/",
                             json={"username": LT_USERNAME,
                                   "password": LT_PASSWORD})
    token = response.json()['key']
    headers = {'Authorization': f'Token {token}'}
    session = requests.session()
    session.headers = headers

    # Step 1 Getting the examples to annotate
    datasets = session.get(API_BASE+'projects/default/datasets/').json()

    dataset = next(filter(lambda x: x['slug'] == DATASET_NAME, datasets))
    examples =session.get(dataset['url']+'examples/').json()

    # Step 2 Get the tagset
    schemas = session.get(f'{API_BASE}projects/default/schemas/').json()
    schema = None
    for s in schemas:
        if s['slug'] == SCHEMA_NAME:
            schema = s
    assert schema, 'schema not found.'

    tags = session.get(schema['url']+'tags/').json()
    tagset = {tag["name"]: tag["id"] for tag in tags}

    return {'session': session, 'schema': schema, 'api_base': API_BASE}, examples, tagset


def generate_suggestions(examples, tagset):
    tok = BoTokenizer('GMD')
    suggestions = []
    for example in examples:
        segmented = segment(tok, example['content'], tagset)
        print('ok')
        for tag_id, start, end in segmented:
            suggestion = {  # Create a suggestion
                "example_id": example['id'],  # That refers to a particular example
                "tag_id": tag_id,  # and applies a particular tag
                "start": start,  # Which starts somewhere in the example
                "end": end  # And ends somewhere in the example
            }
            suggestions.append(suggestion)

    model_metadata = {  # Define any metadata you'd like to store about the model
        "defined_by": "BoTokenizer",
        "comments": "Text segmented using pybo"
    }
    data = {
        "model": {
            "name": "pybo",  # Give the model a name
            "metadata": model_metadata  # Provide metadata (optional)
        },
        "suggestions": suggestions  # Attach the suggestions you made before
    }
    return data


def upload_suggestions(server, suggestions):
    server['session'].post(f"{server['schema']['url']}models/bulk/", json=suggestions)
    models = server['session'].get(server['schema']['url'] + 'models/').json()
    modelIds = {"models": [x['id'] for x in models]}

    resp = server['session'].put(f"{server['api_base']}projects/default/task_definitions/explore-tags-only/",
                                 json=modelIds).json()
    return resp


def get_last_letter_idx(token):
    if token.syls:
        return token[-1][-1]
    return 0


def segment(tok, string, tagset):
    tokens = tok.tokenize(string, split_affixes=False, lemmatize=False)
    print('ok')
    output = []
    idx = 0
    for t in tokens:
        start = idx
        end = start + get_last_letter_idx(t)
        if t.type == 'syl':
            if t.affixed:
                type = tagset['ཕྲད་ཡོད།']
            else:
                type = tagset['མིང་ཚིག']
            output.append((type, start, end))

        idx = start + len(t.content)
    return output


def main(dataset, schema):
    config = {'domain': 'tiblex',
              'user': 'dfg9w',
              'pwd': 'Boddgu99',
              'dataset': dataset,
              'schema': schema}
    server, examples, tagset = prepare_to_suggest(config)
    suggestions = generate_suggestions(examples, tagset)
    resp = upload_suggestions(server, suggestions)
    print(resp)


dataset = 'test1'
schema = 'segment'
main(dataset, schema)
