## Automatic Sizing for SDXL
![example of the node in use](example.jpg)

This is a little node I wrote for myself for [ComfyUI](https://github.com/comfyanonymous/ComfyUI). Just save this as a .py file in your comfyUI custom nodes folder.  
edit: Actually, just save this repository as a folder in your custom nodes folder. Since that's what git cloning was gonna do anyway. Had to figure that one out. Writing code is *not* my day job, or even something I'm remotely competent at.

Don't fuss about the downscale thing, it's optional.

### What it does, for the layman

After rereading the paragraphs that follow I realize I might not have been really clear about what makes this useful. So SDXL takes six new inputs for its prompt conditioning, or three * two dimensions (width and height), plus there's the two you already had—the width and height you generate at. These are all a bit funny to figure out yourself. You could look through the list of bucketed resolutions for training, but they're basically just a series of resolutions where the width and height are multiples of 64, they multiply together to something close to 1024², and their aspect ratio is between 1:4 and 4:1. Instead of memorizing these, you can just input "1024" and any aspect ratio you like in this widget and you'll get the closest one that fits that description. (You can exceed 4:1, however, if you really want to...)

And then there's the cropping. I don't know exactly how StabilityAI did their cropping, but I know that if you have an original image dimension and a training dimension after scaling, the amount cropped from one dimension will be rigidly determined by the difference between the scaled image and the training dimensions. And I checked their documentation to be sure that they get this number 1. after scaling to the training dimensions, and 2. from the left edge and the top edge only, so that seemed like enough to figure out what these numbers should be. So this widget figures that out and gives it as your crop_w and crop_h outputs. Optionally you can add more cropping, if that's something you want.

So with three inputs, one of which doesn't change much (_native_res_), you can get all your relevant sizing numbers: width, height, crop_w, crop_h, target_width, target_height, and the width and height of your empty latent generator. I think that's simpler.

If you're not sure what these conditioning inputs do they're explained here (with the exception of target_width/target_height):  
https://github.com/Stability-AI/generative-models/blob/main/assets/sdxl_report.pdf

 ### The old Readme.md

This node takes native resolution, aspect ratio, and original resolution. It uses these to calculate and output the generation dimensions in an appropriate bucketed resolution with 64-multiples for each side (which double as the target_height/\_width), the resolution for the **width** and **height** conditioning inputs (representing a hypothetical "original" image in the training data), and the **crop_w** and **crop_h** conditioning inputs, which are determined by the difference between the model resolution and the upscaled/downscaled training image along that dimension (and divided by two). The downscale output can optionally be connected to an "upscale by" node to automatically downscale gens to match the "original size" set in this node. (Most don't like downscaling, this was for my own use.) Set to 0.0 or just don't connect the output to anything if you don't want downscaling.

**crop_extra** just adds a fraction of the image size to the crop inputs. Leave at 0.0 unless you want to experiment with SDXL's ability to reproduce cropped images.

The input fields accept different kinds of string inputs to produce different results:

**"native_res"**  
- "1000x10" - returns 100, the square root of 10 * 1000 (as an int).  
- "100" - returns 100  
- "100.0" - returns 100

(this should generally be left at 1024 for SDXL.)  

**"aspect"**  
these are all correct ways of getting a 1:2 aspect ratio:
- "2:4"  
- "1x2"  
- "0.5"  
- "1 by 2"

you can also enter -1 to get the aspect from the original resolution, if it is given as two dimensions.

**"original_res"**  
- "600" - returns 600 on the long side, and the short side is calculated to match the aspect ratio.  
- "600x600" - returns 600 by 600, and crop_w and crop_h are calculated accordingly if this doesn't match the aspect ratio of the image resolution.  
- "2.0" - returns dimensions double those of the generation. So if you're generating at 1024x1024, this will return 2048x2048.


### The other inputs?

*downscale_effect* determines how much to adjust the "downscale" output to match the 'original resolution' (minus cropping). At 1.0 it matches it exactly, at 0.5 it's midway between that and your gen size, etc.

*verbose* enables reporting on the outputs in the console so you can see what it's doing. Full gives a fuller explanation, basic just gives the outputs.

*fit_aspect_to_bucket* adjusts your aspect ratio after determining the bucketed resolution to match that resolution so that crop_w and crop_h should end up either 0 or very nearly 0.


### Postscript

If any of this is flat-out wrong, if I've misread the docs or just typed something in wrong or terribly misused Python in some basic way, please let me know. I've used this a bit with a little 'verbose' node to tell me what numbers I'm putting into my prompt encoder node, so I'm pretty sure it's working for what I'm doing at least, but it might be broken in some way I haven't tested, or I might be missing something when I look at the numbers.

Also, thanks to the anon who informed me straight away that this didn't work when I uploaded it and made me figure out the whole \_\_init\_\_.py thing (only to then write a better, fuller one himself). 
