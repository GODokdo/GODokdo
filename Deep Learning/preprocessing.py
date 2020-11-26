from nltk import tokenize
from value import *
from preprocessing import *
from config import *

def split_document(contents, errors):
    result = []
    sentences = []
    # text = i['contents'].replace("\r","").replace("\n","")
    #sentences = [i.strip() for i in tokenize.sent_tokenize(text)] #문장 단위로 분리 및 문장 앞뒤 공백 제거
    sentences = [i.strip() for i in contents.split('\n')]
    
    # 두줄 이상 공백이 있는 경우 제거
    last = ""
    remove_indexes = []
    for j in range(0, len(sentences)):
        if last == "" and sentences[j] == "":
            remove_indexes.append(j)
        last = sentences[j]
        
    for index in sorted(remove_indexes, reverse=True):
        del sentences[index]
    
    # 문장별로 표기 오류 키워드 검색 && 2 + 1 + 2 문장 단위로 자동 구성
    # padding
    sentences = ['', ''] + sentences + ['', '']
    for index in range(2, len(sentences)):
        sentence = sentences[index]
        # 빈 문장 제거
        if (len(sentence.strip()) == 0): continue
            
        y_class = 0
        y_keyword = ""
        # 현재 문장에 표기 오류가 있는지 확인
        sorted(errors, key = lambda item: item['position'])

        error_index = 0
        for error in errors:
            if (error['sentence_no'] != index - 2):
                continue
            predict_keyword = sentence[error['position']:(error['position']+error['length'])]
            if (predict_keyword != error['keyword']):
                print("에러")
                print(error)
            
            y_class = class_list_from_code[error['code']]
            y_keyword = error['keyword']
            sequence = "sequence " + str(error_index) + ": "
            sequence = ""
            position = len(sequence) + error['position']
            result.append([[(sequence + sentence if j == index else sentences[j]) for j in range(index-2, index+2 + 1)], y_class, y_keyword, position, error['length'], error_index, index])
            error_index += 1
            sentence = sentence[:error['position']] + (' ' * error['length']) + sentence[error['position']+error['length']:]
        sequence = ""
        
        if (len(sentence.strip()) == 0): continue
        result.append([[(sequence+ sentence if j == index else sentences[j]) for j in range(index-2, index+2 + 1)],0, "", 0, 0, error_index, index])
    return result
        
def getInformationFromSentence(i):
    return {
        'text': i[0],
        'y_class': i[1],
        'y_keyword': i[2],
        'position': i[3],
        'length': i[4],
        'error_index': i[5],
        'sentence_no': i[6]
    }

def preprocessing(text, y_class, y_keyword, position, length, error_index):
    if (len(text[1]) > 50):
        before = text[1]
    else:
        before = text[0] + " " + text[1]
        
    main = text[2]
    
    if (len(text[3]) > 50):
        after = text[3]
    else:
        after = text[3] + " " + text[4]
    # before = ""
    # after = ""
    before = config.TOKENIZER.encode(before)
    main = config.TOKENIZER.encode(main)
    after = config.TOKENIZER.encode(after)


    # 토큰 기준으로 키워드가 어디있는지 확인
    keyword_position_in_token = -1
    keyword_end_in_token = -1
    if y_class != 0:
        keyword_position_in_string = position
        keyword_length_in_string = length
        for j in range(len(main.offsets)):
            if keyword_position_in_token == -1 and main.offsets[j][0] >= keyword_position_in_string:
                keyword_position_in_token = j
            if main.offsets[j][1] == 0: continue
            if main.offsets[j][1] <= (keyword_position_in_string + keyword_length_in_string):
                keyword_end_in_token = j
    else:        
        keyword_position_in_token = 0
        keyword_end_in_token = 0
        
    # ids = cls, classification number, sep, token, sep
    ids = [101, 9999, 102] + main.ids[1:] + before.ids[1:] + after.ids[1:]
    # mask = len(cls, classification number, sep, token, sep) = 1, else 0
    mask = [1] * len(ids)
    # token_type_ids len(token, sep) = 1, else 0
    token_type_ids = [0,0,0] +  [1] * (len(main) - 1) + [0] * (len(before) - 1) + [0] * (len(after) - 1)

    targets_start = keyword_position_in_token
    targets_end = keyword_end_in_token

    # offsets based on ids, token offsets (0,0)(0,0)(0,0)(0,a)...(0,0)
    offsets = main.offsets
    
    # Pad sequence if its length < `max_len`
    padding_length = 380 - len(ids)
    if padding_length > 0:
        ids = ids + ([0] * padding_length)
        mask = mask + ([0] * padding_length)
        token_type_ids = token_type_ids + ([0] * padding_length)
        padding_length = 380 - len(offsets)
        offsets = offsets + ([(0, 0)] * padding_length)
        
    temp = []
    temp = [0] * len(class_list)
    try:
        temp[y_class] = 1
    except:
        print(y_class)    
    return {
            'ids': ids,
            'mask': mask, 
            'token_type_ids': token_type_ids,
            'targets_start': targets_start, 
            'targets_end': targets_end, 
            'orig_text': text,
            'orig_keyword': y_keyword,
            'class': y_class,
            'offsets': offsets ,
            'targets_class': temp,
            'error_index':[error_index] * 380
    }