class sizing_node:
    ''' This node takes native resolution, aspect ratio, and original resolution. It uses these to 
        calculate and output the latent dimensions in an appropriate bucketed resolution with 64-multiples 
        for each side (which double as the target_height/_width), the resolution for the width and height
        conditioning inputs (representing a hypothetic "original" image in the training data), and the
        crop_w and crop_h conditioning inputs, which are determined by the difference between the model
        resolution and the upscaled/downscaled training image along that dimension (and divided by two).
        The downscale output can optionally be connected to an "upscale by" node to automatically downscale
        gens to match the "original size" set in this node. (Most don't like downscaling, this was for my 
        own use.) Set to 0.0 or just don't connect the output to anything if you don't want downscaling.

        crop_extra just adds a fraction of the image size to the crop inputs. Leave at 0.0 unless you want 
        to experiment with SDXL's ability to reproduce cropped images.

        The input fields accept different kinds of string inputs to produce different results. Here's a list:
        "native_res"
            - "1000x10" - returns 100, the square root of 10 * 1000 (as an int).
            - "100" - returns 100
            - "100.0" - returns 100
            (this should generally be left at 1024 for SDXL.)
        "aspect"
            these are all correct ways of getting a 1:2 aspect ratio:
            - "2:4"
            - "1x2"
            - "0.5"
            - "1 by 2"
        "original_res"
            - "600" - returns 600 on the long side, and the short side is calculated to match the aspect ratio.
            - "600x600" - returns 600 by 600, and crop_w and crop_h are calculated accordingly if this doesn't
                match the aspect ratio of the image resolution.
            - "2.0" - returns dimensions double those of the generation. So if you're generating at 1024x1024,
                this will return 2048x2048.
    '''

    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "native_res": ("STRING", {
                    "multiline": False,
                    "default": "1024"
                }),
                "aspect": ("STRING", {
                    "multiline": False,
                    "default": "1:1"
                }),
                "original_res": ("STRING", {
                    "multiline": False,
                    "default": "800x1200"
                }),
                "crop_extra": ("FLOAT", {
                    "default": 0.0,
                    "max": 1.0,
                    "min": 0.0,
                    "step": 0.001
                }),
                "downscale_effect": ("FLOAT", {
                    "default": 0.0,
                    "max": 1.0,
                    "min": 0.0,
                    "step": 0.001
                })
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "FLOAT")   
    RETURN_NAMES = ("width", "height", "latent_width", "latent_height", "crop_w", "crop_h", "downscale")

    FUNCTION = "get_sizes"

    CATEGORY = "sizing"

    def parse_res(self, input_text):


        if "." in input_text:
            return float(input_text)

        


        striptext = "".join(i for i in input_text if i in set("1234567890xby*:-"))

        replace_list = ["by", "*", ":"]
        for i in replace_list:
            striptext = striptext.replace(i, "x")

        if "x" in striptext:
            w, h = striptext.split("x", 1)
            return (int(w), int(h))
        else:
            return int(striptext)

    def make_64(self, num):
        num = int(num)
        return num // 64 * 64 if num % 64 < 32 else (num + 1) // 64 * 64

    def get_sizes(self, native_res, aspect, original_res, crop_extra, downscale_effect):

        native_res = self.parse_res(native_res)

        aspect = self.parse_res(aspect)

        original_res = self.parse_res(original_res)

        width, height, latent_width, latent_height, crop_w, crop_h, downscale = None, None, None, None, None, None, None

        if isinstance(native_res, tuple):
            native_res = int((native_res[0] * native_res[1])**(1/2))
        elif isinstance(native_res, float):
            native_res = int(native_res * 1024)

        if isinstance(aspect, tuple):
            aspect = aspect[0]/aspect[1]

        c = (native_res**2 / aspect)**(1/2)
        latent_width = self.make_64(c * aspect)
        latent_height = self.make_64(c)

        aspect = latent_width/latent_height   # adjust aspect to match these multiples of 64

        if isinstance(original_res, float):
            width, height = int(original_res * latent_width), int(original_res * latent_height)
        elif isinstance(original_res, tuple):
            width, height = original_res
        else:
            if latent_width > latent_height:
                width = original_res
                height = int(original_res / aspect)
            else:
                width = int(original_res * aspect)
                height = original_res


        if width/height == latent_width/latent_height:
            crop_w = int(latent_width*crop_extra)//2
            crop_h = int(latent_height*crop_extra)//2
            downscale = width / latent_width
        elif width/height > latent_width/latent_height:
            crop_w = int(width * latent_height/height - latent_width + latent_width * crop_extra)//2
            crop_h = int(latent_height*crop_extra)//2
            downscale = height / latent_height
        else:
            crop_w = int(latent_width*crop_extra)//2
            crop_h = int(height * latent_width/width - latent_height + latent_height * crop_extra)//2
            downscale = width/latent_width

        downscale = 1 - ((1 - downscale) * downscale_effect)

        return (width, height, latent_width, latent_height, crop_w, crop_h, downscale)



NODE_CLASS_MAPPINGS = {
    "sizing_node": sizing_node

}

NODE_DISPLAY_NAME_MAPPINGS = {
    "sizing_node": "get resolutions for generation"
}
