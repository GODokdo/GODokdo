import torch
import transformers
from config import *
from preprocessing import *

class TextDataset:
    """
    Dataset which stores the tweets and returns them as processed features
    """
    def __init__(self, dataset):
        self.dataset = dataset
    
    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, item):
        data = preprocessing(
            self.dataset[item][0], 
            self.dataset[item][1], 
            self.dataset[item][2], 
            self.dataset[item][3], 
            self.dataset[item][4], 
            self.dataset[item][5]
        )
        temp = []
        for i in data["targets_class"]:
            temp.append(torch.tensor(i, dtype=torch.long))
            
        # Return the processed data where the lists are converted to `torch.tensor`s
        return {
            'ids': torch.tensor(data["ids"], dtype=torch.long),
            'mask': torch.tensor(data["mask"], dtype=torch.long),
            'token_type_ids': torch.tensor(data["token_type_ids"], dtype=torch.long),
            'targets_start': torch.tensor(data["targets_start"], dtype=torch.long),
            'targets_end': torch.tensor(data["targets_end"], dtype=torch.long),
            'targets_class': torch.tensor(data["targets_class"], dtype=torch.long),
            'orig_tweet': data["orig_text"],
            'orig_selected': data["orig_keyword"],
            'sentiment': data["class"],
            'offsets': torch.tensor(data["offsets"], dtype=torch.long),
            'error_index': torch.tensor(data["error_index"], dtype=torch.long)
        }
