import requests
from generate_suggestions import segment
from pathlib import Path


def prepare_to_suggest(config):
    DATASET_NAME = config['dataset']
    SCHEMA_NAME = config['schema']

    # Step 0 - Basic Setup
    LIGHTTAG_DOMAIN = config['domain']
    SERVER = f'https://{LIGHTTAG_DOMAIN}.lighttag.io/'
    API_BASE = SERVER + 'api/v1/'
    LT_USERNAME = config['user']
    LT_PASSWORD = config['pwd']
    response = requests.post(f"{SERVER}api/auth/token/create/",
                             json={"username": LT_USERNAME,
                                   "password": LT_PASSWORD})

    token = response.json()['key']
    headers = {'Authorization': f'Token {token}'}
    session = requests.session()
    session.headers = headers

    # Step 1 Getting the examples to annotate
    examples = session.get(f'{API_BASE}projects/default/datasets/{DATASET_NAME}/examples/').json()

    # Step 2 Get schema and tags
    schema = session.get(f'{API_BASE}projects/default/schemas/{SCHEMA_NAME}').json()

    tags = session.get(schema['url']+'tags/').json()
    tagset = {tag["name"]: tag["id"] for tag in tags}

    return {'session': session, 'schema': schema, 'api_base': API_BASE}, examples, tagset


def generate_suggestions(examples, tagset, schema_name):
    # Step 3 - Create your suggestions

    # 3.1 - make a list of suggestions
    suggestions = []
    for example in examples:
        segmented = segment(example['content'], tagset)
        for tag_id, start, end in segmented:
            suggestion = {  # Create a suggestion
                "example_id": example['id'],  # That refers to a particular example
                "tag_id": tag_id,  # and applies a particular tag
                "start": start,  # Which starts somewhere in the example
                "end": end  # And ends somewhere in the example
            }
            suggestions.append(suggestion)

    # 3.2 - define a model
    model_metadata = {  # Define any metadata you'd like to store about the model
        "defined_by": "BoTokenizer",
        "comments": "Text segmented using pybo"
    }
    data = {
        "model": {
            "name": schema_name,  # Give the model a name
            "metadata": model_metadata  # Provide metadata (optional)
        },
        "suggestions": suggestions  # Attach the suggestions you made before
    }
    return data


def upload_suggestions(session_parts, data):
    # Step 4 - Upload your model and data
    resp = session_parts['session'].post(f"{session_parts['schema']['url']}models/bulk/", json=data)

    if resp.status_code == 201:
        print(resp.json())
    else:
        print('no json in response of uploading suggestions.', resp)


def assign_suggestions_to_task(session_parts, model, task):
    # Step 5 - Assign suggestion model to a task
    models = session_parts['session'].get(session_parts['schema']['url'] + 'models/').json()
    modelIds = {'models': [m['id'] for m in models if m['name'] == model]}

    resp = session_parts['session'].put(f'{session_parts["api_base"]}projects/default/task_definitions/{task}/',
                                 json=modelIds)

    if resp.status_code == 201:
        print(resp.json())
    else:
        print('no json in response of assigning suggestion to task.', resp)


def main(dataset, schema, model, task):
    user, pwd = Path('config').read_text().strip().split('\n')
    config = {'domain': 'tiblex',
              'user': user,
              'pwd': pwd,
              'dataset': dataset,
              'schema': schema}

    # Steps 0, 1 and 2
    session_parts, examples, tagset = prepare_to_suggest(config)

    # Step 3
    data = generate_suggestions(examples, tagset, model)
    # Step 4
    upload_suggestions(session_parts, data)
    # Step 5
    assign_suggestions_to_task(session_parts, model, task)


dataset = 'test1'
schema = 'pos-beta1'
model = "pybo-pos"
task = 'tset1'
main(dataset, schema, model, task)
