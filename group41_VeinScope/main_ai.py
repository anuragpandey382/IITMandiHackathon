import torch
from ultralytics import YOLO
import os
import cv2
from unet_plus_attn import Vessels
import numpy as np
import tqdm

class AI_app():

    def __init__(self,fore_model_path,vein_model_path,if_cropped=False):
        print('++Building the pipeline++')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print('Running on:',self.device)
        cwd=os.getcwd()
        self.fore_model_path = os.path.join(cwd,fore_model_path)
        self.if_cropped = if_cropped
        self.original_size=(3000, 1800)

        self.vein_segmentation(os.path.join(cwd, vein_model_path))
        self.foreground_segmentation()

    def foreground_segmentation(self):
        self.fg_model = YOLO(self.fore_model_path)

    def load_image(self,image_path, target_size=(512, 512), original_size=(3000, 1800)):
        org_img = cv2.imread(image_path)
        img = cv2.cvtColor(org_img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, target_size)
        org_img = cv2.resize(org_img, original_size)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        img = cv2.GaussianBlur(enhanced, (5,5), 0)
        #img = img.astype(np.float32) / 255.0
        return img,org_img
        

    def vein_segmentation(self,model_path):
        self.vessel_model = Vessels(model_path,device=self.device)

    def clip_masks(self,mask_sc,mask_vi):
        mask_sc = cv2.resize(mask_sc,(mask_vi.shape[1],mask_vi.shape[0]),interpolation=cv2.INTER_NEAREST)
        # print(mask_vi.shape,mask_sc.shape)
        mask_sc=(mask_sc>0).astype(np.uint8)*225
        mask_vi=(mask_vi>0).astype(np.uint8)*225
        
        confined_masks = cv2.bitwise_and(mask_vi,mask_sc)
        
        return confined_masks
        

    def execute(self,in_images):
        print('++Executing on images++')

        for im_path in tqdm.tqdm(in_images):
            img = cv2.imread(im_path)
            im_name = os.path.basename(im_path)
            base_name, ext = os.path.splitext(im_name)
            # save_path = f'/results_ai/{base_name}/'
            save_path = os.path.join('results_ai', base_name)

            os.makedirs(save_path, exist_ok=True)
            # im_name= os.path.basename(im_path).replace('.jpg', '')
            # save_path=f'app/results_ai/{im_name}/'
            # os.makedirs(save_path,exist_ok=True)
            
            # sclera segmentation model
            result = self.fg_model.predict(source=im_path,
            imgsz=640,
            save=True,
            project='results',
            conf=0.25,  # Confidence threshold
            iou=0.45,   # IoU threshold for NMS
            show_labels=True,  # Show class labels on masks
            show_conf=True     # Show confidence scores
            )
            mask_sc=result[0].masks
            if mask_sc is not None:
                mask_sc = mask_sc.data.cpu().numpy().astype('uint8')[0] *255
                # mask_name =im_name.replace('.','_sclera_mask.')
                # output_path = os.path.join(save_path,mask_name)
                mask_name = f"{base_name}_sclera_mask{ext}"
                output_path = os.path.join(save_path, mask_name)
                cv2.imwrite(output_path, mask_sc)
            else:
                print('no sclera mask')
                
            # vein segmentation model
            mask_vi,original_img = self.vessel_model.predict(img)
            if mask_sc is not None:
                confined_mask = self.clip_masks(mask_sc=mask_sc,mask_vi=mask_vi)
                overlay_img_con = self.vessel_model.overlay_mask_on_image(original_img, confined_mask)
                # mask_name =im_name.replace('.','_con_mask.')
                # output_path_confined = os.path.join(save_path,mask_name)# Define your output path
                mask_name = f"{base_name}_con_mask{ext}"
                output_path_confined = os.path.join(save_path, mask_name)
                cv2.imwrite(output_path_confined, overlay_img_con)
            else:
                overlay_img = self.vessel_model.overlay_mask_on_image(original_img, mask_vi)
                # overlay_name = im_name.replace('.','_overaly.jpg')
                # output_path_confined = os.path.join(save_path,overlay_name)
                overlay_name = f"{base_name}_overlay{ext}"
                output_path_confined = os.path.join(save_path, overlay_name)
                cv2.imwrite(output_path_confined, overlay_img)
            
            # mask_name =im_name.replace('.','_mask.')
            # output_path = os.path.join(save_path,mask_name)
            # cv2.imwrite(output_path, mask_vi)
            
            
            
            
            # relative_url = output_path_confined.replace('\\', '/').replace(BASE_DIR + '/', '')

            print(output_path_confined, )
            
            return output_path_confined
            
            


if __name__ == '__main__':
    fore_ckpt_path='ckpts/yolo_sclera.pt'
    vein_ckpt_path ='ckpts/vein_ckpt.pt'
    images=['test1.jpeg']
    pipe = app(fore_ckpt_path,vein_ckpt_path,if_cropped=True)
    pipe.execute(images)
