class sizing_node:
    ''' This node takes native resolution, aspect ratio, and original resolution. It uses these to 
        calculate and output the latent generator dimensions in an appropriate bucketed resolution with 64-multiples 
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
    w_to_h = {1600: [640], 896: [1088, 1152], 1536: [640], 832: [1152, 1216], 1472: [704], 1408: [704], 768: [1280, 1344], 704: [1344, 1408, 1472], 1344: [768], 1280: [768], 640: [1536, 1600], 1216: [832], 2048: [512], 1984: [512], 1152: [832, 896], 1920: [512], 1856: [512], 576: [1664, 1728, 1792], 1088: [896, 960], 1024: [960, 1024], 512: [1856, 1920, 1984, 2048], 1792: [576], 960: [1024, 1088], 1728: [576], 1664: [576]}
    h_to_w = {640: [1600, 1536], 1088: [896, 960], 1152: [896, 832], 1216: [832], 704: [1472, 1408], 1280: [768], 1344: [768, 704], 1408: [704], 1472: [704], 768: [1344, 1280], 1536: [640], 1600: [640], 832: [1216, 1152], 512: [2048, 1984, 1920, 1856], 896: [1152, 1088], 1664: [576], 1728: [576], 1792: [576], 960: [1088, 1024], 1024: [1024, 960], 1856: [512], 1920: [512], 1984: [512], 2048: [512], 576: [1792, 1728, 1664]}
    # exact buckets from the SDXL training report as quickly searchable dictionaries.

    reportResBase = [(1600, 640), (896, 1088), (896, 1152), (1536, 640), (832, 1152), (832, 1216), (1472, 704), (1408, 704), (768, 1280), (768, 1344), (704, 1344), (704, 1408), (704, 1472), (1344, 768), (1280, 768), (640, 1536), (640, 1600), (1216, 832), (2048, 512), (1984, 512), (1152, 832), (1152, 896), (1920, 512), (1856, 512), (576, 1664), (576, 1728), (576, 1792), (1088, 896), (1088, 960), (1024, 960), (1024, 1024), (512, 1856), (512, 1920), (512, 1984), (512, 2048), (1792, 576), (960, 1024), (960, 1088), (1728, 576), (1664, 576)]
    reportResDict = {i[0]/i[1]: i for i in reportResBase}
    getReportResIndex = sorted([i for i in reportResDict])

    comfyResBase = [(1024, 1024), (1152, 896), (896, 1152), (1216, 832), (832, 1216), (1344, 768), (768, 1344), (1536, 640), (640, 1536)]
    comfyResDict = {i[0]/i[1]: i for i in comfyResBase}
    getComfyResIndex = sorted([i for i in comfyResDict])
    # exact buckets recommended by Comfy—not as many of these! Must be that these had the most training data and produce the best results.



    
    
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
                
            },
            "optional":{
                "verbose": (["disabled", "basic", "full"],),
                "fit_aspect_to_bucket": (["disabled", "enabled"],),
                "strict_bucketing": (["SDXL Report", "Comfy", "disabled"],),
                "extra_args": ("STRING", {
                    "multiline": True,
                    "default": ""
                    })

            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "FLOAT")   
    RETURN_NAMES = ("width", "height", "crop_w", "crop_h", "target_width", "target_height", "downscale")

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

    def getRecommendedRes(self, aspect, mode = "Report"):
        getIndex = None
        resDict = None
        if mode == "Comfy":
            getIndex = self.getComfyResIndex
            resDict = self.comfyResDict
        elif mode == "Report":
            getIndex = self.getReportResIndex
            resDict = self.reportResDict


        # This will return the closest valid resolution.
        c = 0
        for i in getIndex:
            if i > aspect:
                if abs(i-aspect) < abs(c-aspect):
                    return resDict[i]
                else:
                    if c != 0:
                        return resDict[c]
                    else:
                        return resDict[c]
            c = i

        # if none were < aspect, return the last one
        return resDict[getIndex[-1]]

    def make_64(self, num):
        num = int(num)
        return num // 64 * 64 if num % 64 < 32 else (num + 1) // 64 * 64

    def find_fraction(self, decimal):
        ''' A bit silly/wasteful, but this is for describing aspect ratio to anons who put in a float value and
            want verbose reporting. It just iterates over all ints, starting at 1, until it finds one where 
            n / round(n/aspect) is close enough to the given decimal, and 'close enough' is defined according to
            how many decimal points you give it, to a maximum of 5. (Without a maximum this could get very slow.)

            Maybe this is adding some bloat but I think it's fun. It shouldn't get called if you don't choose to 
            turn on "verbose".
        '''
        decimal = round(decimal, 5)

        x = str(decimal)
        xf =len(x) - (x.find(".") + 1)
        tolerance = 10**(-xf-1)*5
        bounds = (decimal - tolerance, decimal + tolerance)

        i = 0
        past0 = False
        while past0 == False:
            i += 1
            if round(i/decimal) == 0.0:
                continue
            else:
                past0 = True
                t = i / round(i/decimal)
                if bounds[0] <= t < bounds[1]:
                    return (i, int(round(i/decimal)))

        while True:
            i+= 1
            t = i / round(i/decimal)
            if bounds[0] <= t < bounds[1]:
                return (i, int(round(i/decimal)))


    def get_sizes(self, native_res, aspect, original_res, crop_extra = 0.0, downscale_effect = 1.0, verbose = "disabled", fit_aspect_to_bucket = "disabled", strict_bucketing = "SDXL Report", extra_args = ""):
        
        sharp = False
        nudge = ("w", 0.0)
        nocrop = False
        override_aspect = False
        bucketMode = "Comfy" if strict_bucketing == "Comfy" else "Report"
        side = False

        if extra_args != "":

            try:
                splitargs = extra_args.split(" ")
                args = []
                for i in splitargs:
                    if i[:2] == "--":
                        args.append((i[2:],))
                    elif i != "":
                        args[-1] += (i, )

                # make it into a quickly searchable dictionary (in case I add lots of optional arguments... lol)
                args = {i[0]: i[1:] if len(i) > 1 else None for i in args}

                # check each argument individually. could do a dict of functions for speed but there aren't many arguments.
                if "nocrop" in args: nocrop = True
                if "nudge" in args:
                    nudge = (args["nudge"][0], float(args["nudge"][1]))
                if "sharp" in args:
                    sharp = 1.33
                if "extrasharp" in args:
                    sharp = 1.67
                if "supersharp" in args:
                    sharp = 2.0
                if "shortside" in args:
                    side = 1
                elif "equivalent" in args:
                    side = 2

                if "randomaspect" in args:
                    from random import random
                    aspect_limits = [0.25, 4.0]

                    # if additonal arguments are given, use them as limits
                    try:
                        aspect_limits = list(args["randomaspect"])
                    except:
                        pass

                    r = ()

                    #parse the inputs to floats
                    for i in aspect_limits:
                        corrected = ""
                        split = False
                        for c in i:
                            if c in {":", "x", "*", "/"}:
                                corrected += "*"
                                split = True
                            else:
                                corrected += c
                        if split:
                            x, y = corrected.split("*")
                            r += (float(x)/float(y),)
                        else:
                            r += (float(corrected), )
                    override_aspect = random()*(r[1]-r[0])+r[0]

            except:
                print("sizing_node: Invalid extra arguments, skipping.")

        # initialize the verbose variables for reporting
        v_aspect = None
        v_crops = None
        v_crops_extra = None
        v_postscale = None
        v_downscale = None
        v = verbose == "full"
        bucket = False if strict_bucketing == "disabled" else True


        # turn these string inputs into tuples, ints, or floats
        native_res = self.parse_res(native_res)
        aspect = self.parse_res(aspect)
        original_res = self.parse_res(original_res)

        #initialize some vars
        width, height, target_width, target_height, crop_w, crop_h, downscale = None, None, None, None, None, None, None


        # parse the native_res input -> int
        if isinstance(native_res, tuple):
            native_res = int((native_res[0] * native_res[1])**(1/2))
        elif isinstance(native_res, float):
            native_res = int(native_res * 1024)


        # if aspect is specified as random, then override it.
        if override_aspect:
            aspect = override_aspect

        # parse the aspect input -> float
        else:
            if isinstance(aspect, tuple):
                if v: v_aspect = aspect
                aspect = aspect[0]/aspect[1]
            elif aspect == -1 and isinstance(aspect, int):
                if isinstance(original_res, tuple):
                    aspect = original_res[0]/original_res[1]
                else:
                    aspect = 1.0
            elif aspect <= 0:
                aspect = 1.0

        if not 4.0 >= aspect >= 0.25:
            bucket = False
            if v: print("\nsizing_node: No actual training bucket for this aspect ratio. Exact bucketing disabled.")
        elif native_res != 1024:
            bucket = False
            if v: print("\nsizing_node: strict_bucketing disabled (native_res != 1024)")
        

        # match the buckets
        target_width, target_height = None, None
        if not bucket:
            c = (native_res**2 / aspect)**(1/2)
            target_width = self.make_64(c * aspect)
            target_height = self.make_64(c)
        else:
            # fit exactly to the actual training buckets, not to a theoretical training bucket
            target_width, target_height = self.getRecommendedRes(aspect, mode = bucketMode)

        if fit_aspect_to_bucket == "enabled":
            aspect = target_width/target_height   # adjust aspect to match the generation size


        if v:
            v_aspect = self.find_fraction(aspect)

        # parse the original resolution input -> width, height
        if isinstance(original_res, float):
            width, height = int(original_res * target_width), int(original_res * target_height)
        elif isinstance(original_res, tuple):
            width, height = original_res
        else:
            if side == 1:
                if target_width > target_height:
                    width = int(original_res * aspect)
                    height = original_res
                else:
                    width = original_res
                    height = int(original_res / aspect)
            elif side == 2:
                height = (original_res**2/aspect)**(1/2)
                width = height*aspect
                width, height = int(width), int(height)
            else:
                if target_width > target_height:
                    width = original_res
                    height = int(original_res / aspect)
                else:
                    width = int(original_res * aspect)
                    height = original_res

        # optional "nudge" argument overrides width or height to give a desired amount of 'plausible' cropping.
        if nudge[1] != 0.0:
            if nudge[0] == "w":
                width = int(round((height/target_height) * (target_width + nudge[1]*32)))
            else:
                height = int(round((width/target_width) * (target_height + nudge[1]*32)))


        # calculate cropping. This also calculates and stores values for verbose reporting on how the cropping was done after scaling in the 'hypothetical' training image.
        if nocrop:
            # optional extra argument to force crop sizes to 0, if this is preferred. This may be useful for A/B testing.
            if v: v_crops, v_postscale = (0, 0), (target_width, target_height, target_width/width, True)
            crop_w = 0
            crop_h = 0
            downscale = min(width/target_width, height/target_height)
        else:
            if width/height == target_width/target_height:
                if v: v_crops, v_postscale = (0, 0), (target_width, target_height, target_width/width, True)
                crop_w = int(target_width*crop_extra)//2
                crop_h = int(target_height*crop_extra)//2
                downscale = (1-crop_extra) * width / target_width
            elif width/height > target_width/target_height:
                x0 = int(width * target_height/height)
                x1 = x0 - target_width
                if v: v_crops, v_postscale = (x1, 0), (x0, target_height, target_height/height, False)
                crop_w = int(x1 + target_width * crop_extra)//2
                crop_h = int(target_height*crop_extra)//2
                downscale = (1-crop_extra) * height / target_height
            else:
                x0 = int(height * target_width/width)
                x1 = x0 - target_height
                if v: v_crops, v_postscale = (0, x1), (target_width, x0, target_width/width, False)
                crop_w = int(target_width*crop_extra)//2
                crop_h = int(x1 + target_height * crop_extra)//2
                downscale = (1-crop_extra) * width/target_width

        if sharp:
            width, height = int(width*sharp), int(height*sharp)

        if v: v_crops_extra = (int(target_width*(crop_extra))//2, int(target_height*(crop_extra))//2)

        if v: v_downscale = (downscale,)
        downscale = min(1 - ((1 - downscale) * downscale_effect), 1.0) # don't output for upscaling, since that should be handled in a different way.
        if v: 
            v_downscale += (downscale,)

        if verbose == "basic":
            print(f'''width: {width}
height: {height}
crop_w: {crop_w}
crop_h: {crop_h}
target_width: {target_width}
target_height: {target_height}
downscale: {downscale}''')

        elif verbose == "full":

            # scaling to fit bucketing
            scaling_line = f"Original dimensions: {width}x{height}\n - scaled by factor of {v_postscale[2]} to {v_postscale[0]}x{v_postscale[1]}."




            # cropping data
            crop_line = ""
            if v_crops == (0, 0):
                crop_line = "No cropping required."
            else:
                crop_line = f'{max(*v_crops)//2} pixels cropped from {"left and right sides" if v_crops[0] > v_crops[1] else "top and bottom"} to fit.'
            if crop_extra > 0:
                crop_line += f'\n - additional {v_crops_extra[0]}, {v_crops_extra[1]} pixels removed from width, height.'

            downscale_line = ""
            #downscale
            if downscale_effect > 0:
                if downscale_effect == 1.0:
                    downscale_line = f"Scale resulting image by {v_downscale[1]}"
                else:
                    downscale_line = f"Scale resulting image by {v_downscale[1]} ({v_downscale[0]}, effect strength {int(100*round(downscale_effect, 2))}%)"
                downscale_line += f"\n Final image size: {int(downscale*target_width)}x{int(downscale*target_height)}"

            #print
            print(
f'''
---- Sizing Data (debug) 
 native resolution: {int(native_res)}
 aspect ratio: {v_aspect[0]}:{v_aspect[1]}
 Generation size of {target_width}x{target_height}
 {scaling_line}
 {crop_line}
 {downscale_line}

---- Output Values
 width: {width}
 height: {height}
 target_width: {target_width}
 target_height: {target_height}
 crop_w: {crop_w}
 crop_h: {crop_h}
 downscale: {downscale}

* disable verbose on the sizing node to hide this information.
'''
                )


        #fin
        return (width, height, crop_w, crop_h, target_width, target_height, downscale)


class sizing_node_basic(sizing_node):

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
                    "default": "1024x1024"
                }),
                "crop_extra": ("FLOAT", {
                    "default": 0.0,
                    "max": 1.0,
                    "min": 0.0,
                    "step": 0.001
                })
                
            }
        }

class sizing_node_unparsed(sizing_node):

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "gen_size_w": ("INT", {
                    "min": -1,
                    "max": 100000,
                    "default": -1,
                    "step": 1
                }),
                "gen_size_h": ("INT", {
                    "min": -1,
                    "max": 100000,
                    "default": -1,
                    "step": 1
                }),
                "native_res": ("INT", {
                    "min": 0,
                    "max": 100000,
                    "default": 1024,
                    "step": 1
                }),
                "aspect": ("FLOAT", {
                    "min": -1.0,
                    "max": 20.0,
                    "default": 1.0,
                    "step": 0.01
                }),
                "original_res_w": ("INT", {
                    "min": -1,
                    "max": 100000,
                    "default": 1024,
                    "step": 1
                }),
                "original_res_h": ("INT", {
                    "min": -1,
                    "max": 100000,
                    "default": 1024,
                    "step": 1
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
                
            },
            "optional":{
                "verbose": (["disabled", "basic", "full"],),
                "fit_aspect_to_bucket": (["disabled", "enabled"],),
                "strict_bucketing": (["SDXL Report", "Comfy", "disabled"],),
                "extra_args": ("STRING", {
                    "multiline": True,
                    "default": ""
                    })

            }
        }

    FUNCTION = "get_sizes_unparsed"

    def get_sizes_unparsed(self, gen_size_w, gen_size_h, native_res, aspect, original_res_w, original_res_h, crop_extra = 0.0, downscale_effect = 1.0, verbose = "disabled", fit_aspect_to_bucket = "disabled", strict_bucketing = "SDXL Report", extra_args = ""):
        original_res = None
        if gen_size_w > 0 and gen_size_h > 0:
            # if the gen sizes are too far below the native resolution to be appropriate for generation
            if (gen_size_w)*(gen_size_h) < 0.9*native_res**2:
                native_res = str(native_res)
            else:
                native_res = f"{gen_size_w}x{gen_size_h}"
            if aspect == -1: aspect = gen_size_w/gen_size_h
        else:
            native_res = str(native_res)

        if aspect != -1:
            if original_res_h == -1 and original_res_w == -1:
                if gen_size_w > 0 and gen_size_h > 0:
                    original_res = f"{gen_size_w}x{gen_size_h}"
                else:
                    original_res = "1.0"
            elif original_res_w == -1:
                original_res = f"{int(aspect * original_res_h)}x{original_res_h}"
            elif original_res_h == -1:
                original_res = f"{original_res_w}x{int(original_res_w / aspect)}"
            else:
                original_res = f"{original_res_w}x{original_res_h}"
        else:
            if original_res_h == -1 and original_res_w == -1:
                    original_res = "1.0"
            elif original_res_w == -1:
                original_res = f"{original_res_h}x{original_res_h}"
            elif original_res_h == -1:
                original_res = f"{original_res_w}x{original_res_w}"
            else:
                original_res = f"{original_res_w}x{original_res_h}"

            aspect = 1.0 if original_res_h == -1 or original_res_w == -1 else original_res_w/original_res_h


        return self.get_sizes(native_res, str(aspect), original_res, crop_extra, downscale_effect, verbose, fit_aspect_to_bucket, strict_bucketing, extra_args)



# The following functions are for converting image dimensions into string inputs for the main node. This might sometimes be desirable for 
class get_aspect_from_ints:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", {
                    "default": 0,
                    "max": 100000,
                    "min": 0,
                    "step": 1
                }),
                "height": ("INT", {
                    "default": 0,
                    "max": 100000,
                    "min": 0,
                    "step": 1
                }),
                
            }
        }

    RETURN_TYPES = ("STRING",)   
    RETURN_NAMES = ("input_str",)

    FUNCTION = "to_string"

    CATEGORY = "sizing/input conversions"

    def to_string(self, width, height):
        return (f"{width}x{height}", )

class get_aspect_from_image():

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", )
                
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT")   
    RETURN_NAMES = ("input_str", "int_width", "int_height")

    FUNCTION = "get_dimensions"

    CATEGORY = "sizing/input conversions"

    def get_dimensions(self, image):
        width, height = image.shape[2], image.shape[1]
        return (f"{width}x{height}", width, height)






# in case this gets installed as just the .py file into the custom nodes folder, I've added these to this file as well.
NODE_CLASS_MAPPINGS = {
    "sizing_node": sizing_node,
    "sizing_node_basic": sizing_node_basic,
    "sizing_node_unparsed": sizing_node_unparsed,
    "get_aspect_from_ints": get_aspect_from_ints,
    "get_aspect_from_image": get_aspect_from_image

}
NODE_DISPLAY_NAME_MAPPINGS = {
    "sizing_node": "sizing for SDXL (advanced)",
    "sizing_node_basic": "sizing for SDXL",
    "sizing_node_unparsed": "sizing for SDXL (int/float inputs)",
    "get_aspect_from_ints": "width, height -> \'WIDTHxHEIGHT\'",
    "get_aspect_from_image": "IMAGE -> \'WIDTHxHEIGHT\'"
}