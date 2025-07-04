# Functions for decoding agilent intelliquant
def extract_strings(filepath, min_length=4):
    with open(filepath, 'rb') as f:
        data = f.read()
    pattern = rb'[\x20-\x7E]{%d,}' % min_length
    strings = [s.decode('utf-8', errors='ignore') for s in re.findall(pattern, data)]
    return strings

def extract_json_like(strings):
    json_like = []
    for s in strings:
        if s.strip().startswith('{') and s.strip().endswith('}'):
            try:
                parsed = json.loads(s)
                json_like.append(parsed)
            except json.JSONDecodeError:
                pass
    return json_like

#filename=
#readable = extract_strings(filename)
#t.write('\n'.join(readable))
#t.close()
#json_blocks = extract_json_like(readable)
