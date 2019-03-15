from pybo import BoPipeline, BoTokenizer

tok = BoTokenizer('GMD')


def bo_tok(text):
    return tok.tokenize(text)


def pos_suggestions(tokens):
    output = []
    idx = 0
    for t in tokens:
        start = idx

        if t.type == 'syl':
            end = start + t.syls[-1][-1] + 1
            if t.affixed:
                pos = t.pos
            else:
                pos = t.pos
            output.append([pos, start, end])

        idx = start + len(t.content)
    return output


pipeline = BoPipeline('dummy',  # preprocessor
                      bo_tok,   # tokenizer
                      pos_suggestions,  # processor
                      'dummy',  # formatter
                      pybo_profile='GMD')


def segment(string, tagset):
    suggestions = pipeline.pipe_str(string)
    for s in suggestions:
        try:
            s[0] = tagset[s[0]]
        except KeyError:
            s[0] = tagset['X']
    return suggestions


def generate_suggestions(examples, tagset):
    """
    Duplicate of the function in submit_suggestions.py
    Only use when generating a json file with the wanted suggestions.
    """
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


if __name__ == '__main__':
    from pathlib import Path
    import json

    content = "འདོད་པ་རྣམས་ལ་མི་ཆགས་ཤིང་། ཞེ་སྡང་སེམས་ཀྱང་མེད་པར་བྱ། ངན་པར་བལྟ་བ་ཀུན་སྤངས་ན། །བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པའོ། །ཞེས་ཚིགས་སུ་བཅད་པ་འདི་དག་སྨྲས་མ་ཐག་ཏུ། " \
              "ཡི་གེར་བྲིས་ནས་འཛམ་བུའི་གླིང་ཀུན་ཏུ་བསྒྲགས་ཏེ། མི་མང་པོ་ཐམས་ཅད་ཀྱིས་དེ་ལ་སློབ་ཅིང་ཅི་ལྟར་བསྟན་པ་བཞིན་དུ་ནན་ཏན་བྱེད་དུ་བཅུག་གོ། །བཅོམ་ལྡན་འདས་དེའི་ཚེ་དེའི་དུས་ན་ཡང་། " \
              "སེམས་ཅན་མང་པོའི་སླད་དུ་ཆོས་ཚོལ་བ་ལ་འགྱོད་པའི་ཐུགས་མི་མངའ་ན། ད་ཅིའི་སླད་དུ་ཆོས་ཀྱང་མ་བསྟན་པ་ཐམས་ཅད་ཡོངས་སུ་བཏང་སྟེ། མྱ་ངན་ལས་འདའ་བར་དགོངས། " \
              "བཅོམ་ལྡན་འདས་གཞན་ཡང་སྔོན་འདས་པའི་བསྐལ་པ་གྲངས་མ་མཆིས་ཚད་མ་མཆིས་པའི་ཕ་རོལ་ན། འཛམ་བུའི་གླིང་འདིར་རྒྱལ་པོ་ཤི་བི་ཞེས་བགྱི་བ་ཞིག་བྱུང་བ་དང་། " \
              "རྒྱལ་པོ་དེ་བཞུགས་པའི་ཕོ་བྲང་ནི་དེ་བ་བརྟ་ཞེས་བགྱི་སྟེ། འབྱོར་བ། བདེ་བ། ལོ་ལེགས་པ། ལོངས་སྤྱོད་དཔག་ཏུ་མེད་པ་དང་ལྡན་ནོ། །དེའི་ཚེ་ན་རྒྱལ་པོ་དེ་འཛམ་བུའི་གླིང་འདི་ལ་དབང་མཛད་དེ། " \
              "རྒྱལ་ཕྲན་ནི་བརྒྱད་ཁྲི་བཞི་སྟོང་། ལྗོངས་ནི་སྟོང་ཕྲག་དྲུག་ཅུའི་ནང་ན། གྲོང་ཁྱེར་ཁྲི་ཕྲག་བརྒྱད་ཅུ་དང་། བཙུན་མོ་དང་ཕོ་བྲང་གི་སླས་སྟོང་ཕྲག་ཉི་ཤུ་དང་། རྒྱལ་བུ་ལྔ་བརྒྱ་ཙམ་དང་། " \
              "བློན་པོ་ཆེན་པོ་སྟོང་ཕྲག་བཅུ་མངའ་བ་ལ་དབང་མཛད་དེ། ཐམས་ཅད་ལ་བྱམས་པ་དང་། སྙིང་རྗེས་མ་ཁྱབ་པ་མེད་དོ། །དེའི་ཚེ་ན་བརྒྱ་བྱིན་ལྷའི་དབང་པོ་ལུས་ཀྱི་ཡོན་ཏན་ལྔ་དང་བྲལ་ཏེ། " \
              "ཚེའི་དུས་བྱེད་དུ་ཉེ་བས་ཤིན་ཏུ་མི་དགའ་སྟེ། མྱ་ངན་བྱེད་པབི་ཤྭ་ཀརྨས་མཐོང་ནས། བརྒྱ་བྱིན་ལ་ཅིའི་སླད་དུ་མྱ་ངན་མཛད་ཅིང་མི་དགྱེས་ཅེས་གསོལ་པ་དང་། བརྒྱ་བྱིན་གྱིས་སྨྲས་པ། " \
              "ང་ནི་ཚེའི་དུས་བྱེད་དུ་ཉེ་བས་ཚེ་འཕོས་བའི་ལྟས་མངོན་དུ་བྱུང་ན། འཇིག་རྟེན་འདིར་སངས་རྒྱས་ཀྱི་ཆོས་ནི་ནུབ་བར་གྱུར་ཏེ། བྱང་ཆུབ་སེམས་དཔའ་ཡང་འཇིག་རྟེན་ན་མི་བཞུགས་ན། " \
              "ཁོ་བོ་གང་ལ་སྐྱབས་སུ་འགྲོ་བ་མི་ཤེས་པས་མྱ་ངན་བྱེད་དོ། །བི་ཤྭ་ཀརྨས་སྨྲས་པ། ལྷའི་དབང་པོ་འཛམ་བུའི་གླིང་ན་རྒྱལ་པོ་ཆེན་པོ་བྱང་ཆུབ་སེམས་དཔའི་སྤྱད་པ་སྤྱོད་པ་ཤི་བི་ཞེས་བྱ་བ་ཞིག་བཞུགས་ཏེ། " \
              "ཤིན་ཏུ་ཡི་དམ་ལ་བརྟན་ཞིང་བརྩོན་འགྲུས་བརྩམས་པས་གདོན་མི་ཟ་བར་མངོན་པར་འཚང་རྒྱ་སྟེ། དེ་ལ་སྐྱབས་སུ་སོང་ན་གདོན་མི་ཟ་བར་དཔུང་གཉེན་དུ་འགྱུར་ཏེ། བགེགས་ལས་རྣམ་པར་ཐར་བར་འགྱུར་རོ། །"
    tagset = {'ཕྲད་ཡོད།': 'a', 'མིང་ཚིག': 'b'}
    task_name = 'test15'

    examples = [{'content': content, 'id': 'dunno'}]
    suggestions = pipeline.pipe_str(content)
    Path(task_name + '_suggestions.json').write_text(json.dumps(suggestions, sort_keys=True, indent=4))
