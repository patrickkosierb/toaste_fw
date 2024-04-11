import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from PIL import Image
import os
import random
import time

# Define the neural network architecture
class CrispClassifier(nn.Module):
    def __init__(self):
        super(CrispClassifier, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(32 * 56 * 56, 256)
        self.fc2 = nn.Linear(256, 1)
        self.sigmoid = nn.Sigmoid()
        self.transform =  transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Using ImageNet normalization
        ])

    def forward(self, x):
        x = self.pool(nn.functional.relu(self.conv1(x)))
        x = self.pool(nn.functional.relu(self.conv2(x)))
        x = x.view(-1, 32 * 56 * 56)
        x = nn.functional.relu(self.fc1(x))
        x = self.sigmoid(self.fc2(x))
        return x

    def load(self):
        load_model = torch.load(os.getcwd()+'/crisp_classifier.pth')
        self.load_state_dict(load_model['model_state_dict'])
        self.eval() #set to evaluate mode

    def predictCrispiness(self, frame):
        capture = self.transform(frame).unsqueeze(0)  # Add batch dimension
        with torch.no_grad():
            output = self(capture)
        return output.item()

# Define dataset class for learning
class CrispDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.runs = os.listdir(self.data_dir)
        self.transform = transform

    def __len__(self):
        # Assuming all images are in the same directory
        minSize = 1000
        for run in self.runs:
            curSize = len(os.listdir(self.data_dir+run))
            if(minSize>curSize):
                minSize=curSize
        return minSize

    def __getitem__(self, idx):

        # pic random dir to chose image from 
        rand_path = self.data_dir+self.runs[random.randint(0, len(self.runs)-1)]

        img_name = os.listdir(rand_path)[idx] 
        img_path = os.path.join(rand_path, img_name)
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)

        # Label decoding
        start_i = img_path.index(':')
        end_i = img_path.index('.')
        temp=""

        for i in range(1,end_i-start_i):
            temp=temp+img_path[start_i+i]

        label = int(temp)/100 # convert labels to cripsiness values
        # print(label)
        return image, torch.tensor(label, dtype=torch.float32)

if __name__ == "__main__":

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Define transforms for data preprocessing
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Using ImageNet normalization
    ])

    # Define hyperparameters
    batch_size = 20
    learning_rate = 0.001
    num_epochs = 50

    # Load data
    dataPath = os.getcwd()+"/learning/data_label/" #change depending on set you want to train on (can automate this)
    train_dataset = CrispDataset(data_dir=dataPath, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Model + optimizer
    model = CrispClassifier().to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Load model if already exists
    try: 
        checkpoint = torch.load(os.getcwd()+'/crisp_classifier.pth')
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print("Loaded model")   
    except:
        pass

    # training
    start = time.time()
    for epoch in range(num_epochs):
        running_loss = 0.0
        for data in train_loader:
            try:
                inputs, labels = data[0].to(device), data[1].to(device)
                optimizer.zero_grad()

                outputs = model(inputs)
                # print(labels)
                loss = criterion(outputs, labels.view(batch_size,1))

                # Backward pass and optimization
                loss.backward()
                optimizer.step()

                running_loss += loss.item()
            except:
                print("error: ", len(data))
                pass
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss / len(train_loader)}")
    dt = time.time() - start
    print('Finished Training time taken: ', dt)
    
    # save model
    cp = {
        'model_state_dict' : model.state_dict(),
        'optimizer_state_dict' : optimizer.state_dict()
    }
    torch.save(cp, 'crisp_classifier.pth')
