# GODokdo

Python-based AI solution for fixing from the error about the korea's information to correct one.

![image](https://user-images.githubusercontent.com/17453822/100536654-525f6000-3265-11eb-82fc-d4631dbcc4bf.png)
![image](https://user-images.githubusercontent.com/17453822/100536614-29d76600-3265-11eb-8d12-a8ca57bcfefa.png)


## Main Process 

1. Users and web crawlers register various types of documents such as text, URL, and images.

1. Server automatically collects document information
    - Text: Sentence separation
    - URL: Web page information collection + conversion data into text.
    - Image: Using tesseract, conversion img into text.
    
1. AI reads text and detects errors.

1. Users can check the detected errors.
      - Is this all right?
      - Isn't it misclassified?
      - This part was not detected.
      - Everything is successful. Click the Done button.
      
1. The server stores that data. AI also reflects those documents in the deep learning process that runs periodically.

## Subproject Overview

### API Server

  All activities go through this server. We tried to satisfy the REST API as much as possible. [API Document](https://api.easylab.kr/)

### Deep Learning Server

  It learns by receiving data from the API server. BERT was used as the word embedding model. We use the output of the two hidden layers of the BERT model as the embedding result. 
  
  And Our model is to predict [error categories (one-hot encoding), error keyword position, error keyword length(end_position)] through two additional layers.
  
  In addition, surrounding sentences are used together to predict. So our model can be expected to take the context into account.

### Web Server

  The Angular framework was used to create the web server. Register new file, bring the registered new file and fill the sentence. This is a front-end system that allows users to communicate with the server.

### Web Crawling Server

  To collect data from web page, we used python. There is a root keyword here. It collects new documents by stacking new urls(hyperlinks) to tree structure base on root keyword.
  

## Usage

 1. Search from our web site via url.
 1. Confirm the result from web site whether that web site is clear or not.
 1. also, we can confirm with image.



## Future Work
We are trying a new image object detection model called yolov4 and expect this to be able to detect errors that are not detected by text alone.
![image](https://user-images.githubusercontent.com/17453822/100537383-76be3b00-326b-11eb-8c69-09c7bd29b336.png)
However, the model's performance did not come out as expected bacause of lack of data

**So, it was temporarily excluded from the service. But, if the opportunity arises, we will incorporate this into our solution!**


- CNN (github : https://github.com/deepseasw/caltech101-image-cnn-classification/blob/master/Image%20CNN%20Classification.ipynb)

- pytorch-YOLOv4 (github : https://github.com/Tianxiaomo/pytorch-YOLOv4)




## Reference
- [Angular](https://github.com/angular/angular)
- [Core free angular admin template](https://github.com/coreui/coreui-free-angular-admin-template)
- [BERT - pytorch](https://github.com/codertimo/BERT-pytorch)
- [BERT - span extraction example](https://www.kaggle.com/abhishek/bert-base-uncased-using-pytorch)
- [pytesseract](https://pypi.org/project/pytesseract/)


## Member
* **Seunghwa, Lee** 
* **Kyoyeon, Hong** 
* **JiHyeon, Kim** 
