# from PIL import Image, ImageOps
# import io

# def process_image(image_bytes):
#     img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     processed_img = ImageOps.invert(img)
#     output_buffer = io.BytesIO()
#     processed_img.save(output_buffer, format="PNG")
#     return output_buffer.getvalue()



# from PIL import Image, ImageOps
# import io
# import routers.stages.combined as model

# def process_image(image_bytes):
#     img = Image.open(io.BytesIO(image_bytes)).convert("RGB")


#     processed_img = model.process(img)
    

#     output_buffer = io.BytesIO()
#     processed_img.save(output_buffer, format="PNG")
#     return output_buffer.getvalue()

from PIL import Image, ImageOps
import io
import stages.combined as model
import os
import cv2
import numpy as np


from PIL import Image, ImageEnhance
import numpy as np
import cv2
import io

import random

def process_image(image_bytes):
    # Load original image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    name = str(random.randint(0,10000000000))
    img.save(f"processing_img/{name}.png")

    # Run your model on the image
    processed_img, _ ,diseases = model.process_disease(f"processing_img/{name}.png")  

    # Convert mask to binary and scale to 255
    processed_img = (processed_img > 0).astype(np.uint8) * 255

    # # Create a red-colored overlay from the mask
    # mask_rgba = np.zeros((*processed_img.shape, 4), dtype=np.uint8)
    # mask_rgba[..., 1] = 255  # Red channel
    # mask_rgba[..., 3] = (processed_img * 0.4).astype(np.uint8)  # Alpha channel (40% opacity where mask is 255)

    # # Convert to PIL Image
    # mask_image = Image.fromarray(mask_rgba, mode="RGBA")
    # base_image = img.convert("RGBA")

    # # Composite the overlay on the original image
    # blended = Image.alpha_composite(base_image, mask_image)

    base_image = img.convert("RGBA")
    darkened_image = ImageEnhance.Brightness(base_image).enhance(0.6)  # 60% brightness

    # Step 2: Create a red overlay from the mask
    mask_rgba = np.zeros((*processed_img.shape, 4), dtype=np.uint8)
    mask_rgba[..., 1] = 255  # Red channel
    mask_rgba[..., 3] = (processed_img * 0.7).astype(np.uint8)  # Alpha channel for 70% opacity

    # Step 3: Convert to PIL image
    mask_image = Image.fromarray(mask_rgba, mode="RGBA")

    mask_processed = Image.fromarray(processed_img)

    # Step 4: Composite the mask on the darkened image
    blended = Image.alpha_composite(darkened_image, mask_image)

    blended.save(f"processing_img/{name}_processed.png")

    output_buffer = io.BytesIO()
    mask_processed.save(output_buffer, format="PNG")


    # Save to buffer
    output_buffer_blended = io.BytesIO()
    blended.save(output_buffer_blended, format="PNG")


    return [output_buffer.getvalue(),output_buffer_blended.getvalue(), diseases]
