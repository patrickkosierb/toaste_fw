import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os 

# Define the neural network architecture (make sure this matches the architecture you used during training)
class CrispClassifier(nn.Module):
    def __init__(self):
        super(CrispClassifier, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(32 * 56 * 56, 256)
        self.fc2 = nn.Linear(256, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.pool(nn.functional.relu(self.conv1(x)))
        x = self.pool(nn.functional.relu(self.conv2(x)))
        x = x.view(-1, 32 * 56 * 56)
        x = nn.functional.relu(self.fc1(x))
        x = self.sigmoid(self.fc2(x))
        return x

if __name__ == "__main__":

    model = CrispClassifier()
    # Load the trained model state dict
    model.load_state_dict(torch.load('crisp_classifier.pth'))

    # Set the model to evaluation mode
    model.eval()

    # Define transforms for data preprocessing (make sure these match the transforms used during training)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Using ImageNet normalization
    ])

    # Load image for prediction
    image = Image.open(os.getcwd()+'/data_label/crisp-82.jpg').convert('RGB')
    image = transform(image).unsqueeze(0)  # Add batch dimension

    # Make prediction
    with torch.no_grad():
        output = model(image)

    # Convert the output to a probability score
    crispiness = output.item()

    # You can then use the probability score for further analysis or decision making
    print("Predicted Crispiness:", crispiness)
