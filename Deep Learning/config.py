import tokenizers
class config:
    MAX_LEN = 128
    TRAIN_BATCH_SIZE = 8
    VALID_BATCH_SIZE = 4
    EPOCHS = 5
    BERT_PATH = "./bert-base-uncased/"
    MODEL_PATH = "model.bin"
    TOKENIZER = tokenizers.BertWordPieceTokenizer(
        f"{BERT_PATH}/vocab.txt", 
        lowercase=True
    )
    API_KEY = "godapikey12"