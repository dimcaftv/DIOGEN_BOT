from urllib.parse import parse_qs, urlencode


def extract_query_data(query: str):
    res = {}
    for k, v in parse_qs(query).items():
        if len(v) == 1:
            v = v[0]
            if v.isdecimal():
                v = int(v)
        res[k] = v
    return res


def encode_url(base: str, query: dict):
    return base + '?' + urlencode(query)
