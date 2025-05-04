import torch
from torch.utils.data import Dataset, DataLoader
import h5py
import numpy as np

class AudioDataset(Dataset):
    def __init__(self, h5_file, transform=None):
        self.h5_file = h5py.File(h5_file, 'r', libver='latest')
        self.transform = transform
        
    def __len__(self):
        return len(self.h5_file['waveforms'])
    
    def __getitem__(self, idx):
        audio_sample = self.h5_file['waveforms'][idx]  # Lazy load the waveform
        audio_waveform = np.array(audio_sample)
        
        if self.transform:
            audio_waveform = self.transform(audio_waveform)
        
        label = self.h5_file['labels'][idx]
        
        return torch.tensor(audio_waveform, dtype=torch.float32), torch.tensor(label, dtype=torch.long)

    def close(self):
        self.h5_file.close()

if __name__ == '__main__':
    h5_file_path = 'trainingdataset_reverb.h5'
    dataset = AudioDataset(h5_file=h5_file_path)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    for audio_data, labels in dataloader:
        print(f'Audio Data Shape: {audio_data.shape}, Labels: {labels}')
    
    dataset.close()
