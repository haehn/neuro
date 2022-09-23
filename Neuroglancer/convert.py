import os
import sys
import shutil
import tempfile
import json
import mahotas


########################################################################################################################
"""COMMAND LINE ARGUMENTS FOR INPUT AND OUTPUT"""

INPUTFOLDER = sys.argv[1]
OUTFOLDER = sys.argv[2]


########################################################################################################################
""" CREATING TEMP FOLDER """

only_images = tempfile.TemporaryDirectory()
only_images_path = only_images.name
print("Path of Temporary folder one is {}".format(only_images_path))


########################################################################################################################

"""PATH HERE SPECIFIES THE INPUT PATH OF THE TIF STACK"""

path = INPUTFOLDER
# print(sorted(os.listdir(path)))
images = [f for f in sorted(os.listdir(path)) if '.tif' in f.lower()]

for image in images:
    new_path = only_images_path + "/" + image
    shutil.copy(path + "/" + image, new_path)
    print("Image has been copied to the location: {}".format(new_path))
print("All the .TIF images have been copied to the temporary folder {}".format(only_images_path))

########################################################################################################################

"""ANOTHER TEMP FOLDER FOR .TIF TO JPEG CONVERSION"""
jpeg = tempfile.TemporaryDirectory()
jpeg_path = jpeg.name
print("Path of Temporary folder two is {}".format(jpeg_path))

########################################################################################################################

"""CONVERTING IMAGES USING IMAGE MAGICK"""


images = [f for f in sorted(os.listdir(only_images_path)) if '.tif' in f.lower()]

for i in images:
    img_input_path = only_images_path + "/" + i
    img_output_path = jpeg_path + "/" + i.replace("tif", "jpeg")

    # BASH COMMAMD FOR IMAGEMAGICK, -quiet is used to hide tif tag warning

    os.system("convert -quiet {} {}".format(img_input_path, img_output_path))
    #print("The converted image has been saved to {}".format(img_output_path))

########################################################################################################################

"""EXTRACTING DATA FROM THE INFO FILE"""

images = [f for f in sorted(os.listdir(path)) if '.info' in f.lower()]
# print(images)

with open(path + "/" + images[0]) as f:
    lines = f.readlines()
    da = [i for i in lines if "pixelsize" in i.lower()]
    la = [i for i in lines if "tif" in i.lower()]
    ofs = [i for i in lines if "offset" in i.lower()]
    offset = ofs[0].split()
    offset_a = offset[1]
    offset_b = offset[2]
    offset_c = 0
    #offset_c = offset[3] IF THE INFO FILE HAS 3RD VALUE
    #print(offset_a, offset_b)
    #print(ofs)
    pixel_size = da[0].split()
    pixel_x = pixel_size[1]
    pixel_y = pixel_size[2]
    # print(la)
    z_axis = la[0].split()
    z_value = float(z_axis[1])
    f.close()
# print(z_axis, pixel_x, pixel_y)

with open(path + "/" + images[1]) as f:
    lines = f.readlines()
    la = [i for i in lines if "tif" in i.lower()]
    z_axis = la[0].split()
    z_value_2 = float(z_axis[1])
    volume_data = int(z_value_2 - z_value)
    f.close()
# print(volume_data)

########################################################################################################################


########################################################################################################################

"""GENERATING JSON INFO FILE, USING MAHOTAS TO GET DIMENSIONS, CHANNELS"""

counter = [f for f in sorted(os.listdir(jpeg_path)) if '.jpeg' in f.lower()]

slices = len(counter)
image = mahotas.imread(jpeg_path + "/" + counter[0])
height = image.shape[0]
width = image.shape[1]

if image.ndim == 2:
    channels = 1  # grayscale

if image.ndim == 3:
    channels = image.shape[-1]

# JSON FILE
array_out = {
    "type": "image",
    "data_type": str(image.dtype),
    "num_channels": channels,
    "scales": [
        {
            "chunk_sizes": [],
            "encoding": "jpeg",
            "key": "full",
            "resolution": [int(pixel_x), int(pixel_y), volume_data],
            "size": [width, height, slices],
            "voxel_offset": [int(offset_a), int(offset_b), int(offset_c)]
        }
    ]

}

json_temp_folder = tempfile.TemporaryDirectory()
json_path = json_temp_folder.name
with open('{}/data.json'.format(json_path), 'w') as f:
    json.dump(array_out, f)





########################################################################################################################

"""RUNNING NEUROGLANCER SCRIPTS"""

#os.system("rm -r OUTFOLDER")
#os.system("mkdir OUTFOLDER")
os.system("generate-scales-info {}/data.json {}".format(json_path, OUTFOLDER))
os.system("slices-to-precomputed --input-orientation RPS {} {}".format(jpeg_path, OUTFOLDER))
os.system("compute-scales --flat {}".format(OUTFOLDER))

