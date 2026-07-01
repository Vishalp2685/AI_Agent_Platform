from sentence_transformers import SentenceTransformer

_model = None

def load_model():
    global _model

    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')

    return _model

def embed(texts: list[str]):
    '''
    Takes a list of chunks and return a list of vectors for the chunks
    '''
    model = load_model()
    return model.encode(texts)


