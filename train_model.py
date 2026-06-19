import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

data = {
    'length': [20,150,30,180,50,220,45,170,60,200],
    'https': [1,0,1,0,1,0,1,0,1,0],
    'dots': [2,5,2,6,3,7,2,5,3,6],
    'domain_len': [10,25,12,30,15,35,11,28,14,32],
    'ip': [0, 0, 0, 0, 0, 0, 1],
    'at': [0,1,0,1,0,1,0,1,0,1],
    'hyphen': [0,1,0,1,0,1,0,1,0,1],
    'keywords': [0,1,0,1,0,1,0,1,0,1],
    'label': [0,1,0,1,0,1,0,1,0,1]
}

df = pd.DataFrame(data)

X = df.drop('label', axis=1)
y = df['label']

model = RandomForestClassifier(n_estimators=300)
model.fit(X, y)

pickle.dump(model, open('model.pkl', 'wb'))

print("Model Trained Successfully")