import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionBlock(nn.Module):
    def __init__(self, F_g, F_l, F_int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, 1, bias=False),
            nn.BatchNorm2d(F_int)
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, 1, bias=False),
            nn.BatchNorm2d(F_int)
        )
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, 1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)

class UpConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_ch, out_ch, 2, stride=2)

    def forward(self, x):
        return self.up(x)

class AttentionUNet(nn.Module):
    def __init__(self, in_ch=1, out_ch=1):
        super().__init__()
        # Encoder
        self.enc1 = ConvBlock(in_ch, 64)
        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = ConvBlock(64, 128)
        self.pool2 = nn.MaxPool2d(2)
        self.enc3 = ConvBlock(128, 256)
        self.pool3 = nn.MaxPool2d(2)
        self.enc4 = ConvBlock(256, 512)
        self.pool4 = nn.MaxPool2d(2)

        # Bottleneck
        self.bottleneck = ConvBlock(512, 1024)

        # Decoder + Attention
        self.up4 = UpConv(1024, 512)
        self.att4 = AttentionBlock(512, 512, 256)
        self.dec4 = ConvBlock(1024, 512)

        self.up3 = UpConv(512, 256)
        self.att3 = AttentionBlock(256, 256, 128)
        self.dec3 = ConvBlock(512, 256)

        self.up2 = UpConv(256, 128)
        self.att2 = AttentionBlock(128, 128, 64)
        self.dec2 = ConvBlock(256, 128)

        self.up1 = UpConv(128, 64)
        self.att1 = AttentionBlock(64, 64, 32)
        self.dec1 = ConvBlock(128, 64)

        self.final = nn.Conv2d(64, out_ch, 1)

    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))

        b = self.bottleneck(self.pool4(e4))

        # Decoder + Attention
        d4 = self.up4(b)
        a4 = self.att4(d4, e4)
        d4 = self.dec4(torch.cat((a4, d4), dim=1))

        d3 = self.up3(d4)
        a3 = self.att3(d3, e3)
        d3 = self.dec3(torch.cat((a3, d3), dim=1))

        d2 = self.up2(d3)
        a2 = self.att2(d2, e2)
        d2 = self.dec2(torch.cat((a2, d2), dim=1))

        d1 = self.up1(d2)
        a1 = self.att1(d1, e1)
        d1 = self.dec1(torch.cat((a1, d1), dim=1))

        return self.final(d1)

if __name__ == "__main__":
    model = AttentionUNet(in_ch=3, out_ch=1)
    x = torch.randn(4, 3, 256, 256)
    y = model(x)
    print(y.shape)  # should be (1, 1, 256, 256)

