import hashlib
import uuid
from flask import current_app
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
from PIL import Image
import logging

logger = logging.getLogger('resources_logger')


def generate_hash_from_filename(fname):
    fname = str(uuid.uuid4()) + str(fname)
    return hashlib.md5(fname.encode("utf-8")).hexdigest()


def get_path(fname):
    hashed = generate_hash_from_filename(fname)
    path_info = (fname, hashed[:2], hashed[2:4], hashed[4:6], hashed,)
    return path_info


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_date_br():
    now = datetime.now()
    diff = timedelta(hours=-3)
    tz = timezone(diff)
    sp_now = now.astimezone(tz)
    return sp_now.strftime('%Y-%m-%d')


rlbp_values = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 6, 6: 5, 7: 6, 8: 7, 9: 1, 10: 2, 11: 10, 12: 8, 13: 10, 14: 9, 15: 10,
               16: 11, 17: 1, 18: 2, 19: 3, 20: 4, 21: 58, 22: 5, 23: 6, 24: 12, 25: 12, 26: 12, 27: 15, 28: 13, 29: 13,
               30: 14, 31: 15, 32: 16, 33: 1, 34: 2, 35: 3, 36: 4, 37: 58, 38: 5, 39: 6, 40: 7, 41: 58, 42: 58, 43: 58,
               44: 8, 45: 58, 46: 9, 47: 10, 48: 17, 49: 17, 50: 17, 51: 58, 52: 17, 53: 58, 54: 20, 55: 21, 56: 18,
               57: 18, 58: 20, 59: 21, 60: 19, 61: 21, 62: 20, 63: 21, 64: 22, 65: 1, 66: 2, 67: 3, 68: 4, 69: 58,
               70: 5, 71: 6, 72: 7, 73: 58, 74: 58, 75: 58, 76: 58, 77: 58, 78: 58, 79: 10, 80: 11, 81: 58, 82: 58,
               83: 58, 84: 58, 85: 58, 86: 58, 87: 58, 88: 25, 89: 58, 90: 58, 91: 58, 92: 26, 93: 58, 94: 27, 95: 15,
               96: 23, 97: 23, 98: 23, 99: 44, 100: 23, 101: 58, 102: 58, 103: 45, 104: 23, 105: 58, 106: 58, 107: 58,
               108: 26, 109: 58, 110: 27, 111: 28, 112: 24, 113: 24, 114: 24, 115: 49, 116: 58, 117: 58, 118: 27,
               119: 28, 120: 25, 121: 25, 122: 27, 123: 28, 124: 26, 125: 26, 126: 27, 127: 28, 128: 29, 129: 30,
               130: 29, 131: 31, 132: 29, 133: 32, 134: 5, 135: 32, 136: 7, 137: 30, 138: 58, 139: 31, 140: 8, 141: 33,
               142: 33, 143: 33, 144: 11, 145: 30, 146: 58, 147: 31, 148: 58, 149: 58, 150: 58, 151: 32, 152: 12,
               153: 58, 154: 58, 155: 34, 156: 13, 157: 34, 158: 14, 159: 34, 160: 16, 161: 30, 162: 58, 163: 31,
               164: 58, 165: 58, 166: 58, 167: 32, 168: 58, 169: 58, 170: 58, 171: 58, 172: 58, 173: 58, 174: 58,
               175: 33, 176: 17, 177: 48, 178: 58, 179: 58, 180: 58, 181: 58, 182: 58, 183: 35, 184: 18, 185: 52,
               186: 58, 187: 35, 188: 19, 189: 35, 190: 35, 191: 35, 192: 36, 193: 37, 194: 36, 195: 38, 196: 36,
               197: 37, 198: 39, 199: 39, 200: 36, 201: 37, 202: 58, 203: 38, 204: 58, 205: 40, 206: 40, 207: 40,
               208: 36, 209: 37, 210: 58, 211: 38, 212: 58, 213: 58, 214: 58, 215: 39, 216: 51, 217: 52, 218: 58,
               219: 41, 220: 54, 221: 41, 222: 41, 223: 41, 224: 42, 225: 43, 226: 43, 227: 44, 228: 42, 229: 43,
               230: 45, 231: 45, 232: 42, 233: 43, 234: 58, 235: 44, 236: 54, 237: 46, 238: 46, 239: 46, 240: 47,
               241: 48, 242: 47, 243: 49, 244: 47, 245: 48, 246: 50, 247: 50, 248: 51, 249: 52, 250: 51, 251: 53,
               252: 54, 253: 55, 254: 56, 255: 57}

ulbp_values = {0: 0, 1: 1, 2: 2, 3: 9, 4: 3, 5: 58, 6: 10, 7: 17, 8: 8, 9: 16, 10: 58, 11: 24, 12: 58, 13: 58, 14: 58,
               15: 32, 16: 4, 17: 58, 18: 58, 19: 58, 20: 11, 21: 58, 22: 18, 23: 25, 24: 58, 25: 58, 26: 58, 27: 58,
               28: 58, 29: 58, 30: 58, 31: 40, 32: 7, 33: 58, 34: 58, 35: 58, 36: 58, 37: 58, 38: 58, 39: 58, 40: 15,
               41: 23, 42: 58, 43: 31, 44: 58, 45: 58, 46: 58, 47: 39, 48: 58, 49: 58, 50: 58, 51: 58, 52: 58, 53: 58,
               54: 58, 55: 58, 56: 58, 57: 58, 58: 58, 59: 58, 60: 58, 61: 58, 62: 58, 63: 47, 64: 6, 65: 58, 66: 58,
               67: 58, 68: 58, 69: 58, 70: 58, 71: 58, 72: 58, 73: 58, 74: 58, 75: 58, 76: 58, 77: 58, 78: 58, 79: 58,
               80: 58, 81: 58, 82: 58, 83: 58, 84: 58, 85: 58, 86: 58, 87: 58, 88: 58, 89: 58, 90: 58, 91: 58, 92: 58,
               93: 58, 94: 58, 95: 58, 96: 14, 97: 58, 98: 58, 99: 58, 100: 58, 101: 58, 102: 58, 103: 58, 104: 22,
               105: 30, 106: 58, 107: 38, 108: 58, 109: 58, 110: 58, 111: 46, 112: 58, 113: 58, 114: 58, 115: 58,
               116: 58, 117: 58, 118: 58, 119: 58, 120: 58, 121: 58, 122: 58, 123: 58, 124: 58, 125: 58, 126: 58,
               127: 54, 128: 5, 129: 58, 130: 58, 131: 58, 132: 58, 133: 58, 134: 58, 135: 58, 136: 58, 137: 58,
               138: 58, 139: 58, 140: 58, 141: 58, 142: 58, 143: 58, 144: 12, 145: 58, 146: 58, 147: 58, 148: 19,
               149: 58, 150: 26, 151: 33, 152: 58, 153: 58, 154: 58, 155: 58, 156: 58, 157: 58, 158: 58, 159: 48,
               160: 58, 161: 58, 162: 58, 163: 58, 164: 58, 165: 58, 166: 58, 167: 58, 168: 58, 169: 58, 170: 58,
               171: 58, 172: 58, 173: 58, 174: 58, 175: 58, 176: 58, 177: 58, 178: 58, 179: 58, 180: 58, 181: 58,
               182: 58, 183: 58, 184: 58, 185: 58, 186: 58, 187: 58, 188: 58, 189: 58, 190: 58, 191: 55, 192: 13,
               193: 58, 194: 58, 195: 58, 196: 58, 197: 58, 198: 58, 199: 58, 200: 58, 201: 58, 202: 58, 203: 58,
               204: 58, 205: 58, 206: 58, 207: 58, 208: 20, 209: 58, 210: 58, 211: 58, 212: 27, 213: 58, 214: 58,
               215: 41, 216: 58, 217: 58, 218: 58, 219: 58, 220: 58, 221: 58, 222: 58, 223: 56, 224: 21, 225: 58,
               226: 58, 227: 58, 228: 58, 229: 58, 230: 58, 231: 58, 232: 29, 233: 37, 234: 58, 235: 45, 236: 58,
               237: 58, 238: 58, 239: 53, 240: 28, 241: 34, 242: 58, 243: 58, 244: 35, 245: 58, 246: 42, 247: 49,
               248: 36, 249: 44, 250: 58, 251: 52, 252: 43, 253: 51, 254: 50, 255: 57}


def getLbpValue(TM, i, j, lbp_type):
    ret = 0
    if TM[i - 1, j - 1][0] > TM[i, j][0]:
        ret += 1
    if TM[i - 1, j][0] > TM[i, j][0]:
        ret += 2
    if TM[i - 1, j + 1][0] > TM[i, j][0]:
        ret += 4

    if TM[i, j - 1][0] > TM[i, j][0]:
        ret += 8
    if TM[i, j + 1][0] > TM[i, j][0]:
        ret += 16

    if TM[i + 1, j - 1][0] > TM[i, j][0]:
        ret += 32
    if TM[i + 1, j][0] > TM[i, j][0]:
        ret += 64
    if TM[i + 1, j + 1][0] > TM[i, j][0]:
        ret += 128

    if lbp_type == 1:
        return ulbp_values[ret]
    elif lbp_type == 2:
        return rlbp_values[ret]
    else:
        return ret


# generate the histogram of the TM. If normalize=True, it normalizes the histogram;
# if lbp_type=1, returns Uniform LPB, if lpb_type=2, returns Robust LBP, if lpb_type=0, return Normal LBP
def doLbpMatrix(TM, normalize, lbp_type):
    x = 59 if lbp_type else 256  # if selected robust or uniform, the histogram has 59 positions. Normal LBP has 256 positions
    hist = [0] * x

    w, h = TM.size
    pix = TM.load()

    for i in range(2, w - 2):
        for j in range(2, h - 2):
            v = getLbpValue(pix, i, j, lbp_type)
            hist[v] += 1

    if normalize:
        maxv = float(max(hist))
        for i in range(len(hist)):
            hist[i] = (hist[i] / maxv) * 1.0;

    return hist


def rlbp(TM, normalize):
    return doLbpMatrix(TM, normalize, 2)


def ulbp(TM, normalize):
    return doLbpMatrix(TM, normalize, 1)


def lbp(TM, normalize):
    return doLbpMatrix(TM, normalize, 0)


def get_wav_info(wav_file):
    rate, data = wavfile.read(wav_file)
    return rate, data


def write_scikit(hist, filename):
    if hist is None:
        return
    f = open(filename, "w+")

    text = str(0) + " "  # define always as incorrect
    for i in range(len(hist)):
        text += str(i + 1) + ":" + str(hist[i]) + " "

    text += "\n"
    f.write(text)
    f.close()


# function generate_spectrogram
# parameters wd = word(string), w = audio path
# create the files wd+'.png' & wd+'_gray.png' in path ./../spectrograms/
def generate_spectrogram(wd, w):
    logger.info("ML API -> Generating spectrogram...")
    rate, data = get_wav_info(w)
    nfft = 256  # Length of the windowing segments
    fs = 256  # Sampling frequency
    pxx, freqs, bins, im = plt.specgram(data, nfft, fs)
    plt.axis('off')

    wd_path = './project/server/spectrograms/' + wd + '/'
    wd_img_path = './project/server/spectrograms/' + wd + '.png'

    if not os.path.exists(wd_path):
        logger.info('ML API -> Creating directory structure')
        os.makedirs(wd_path)

    try:
        logger.info('ML API -> Saving spectrogram')
        plt.savefig(wd_img_path, dpi=100, frameon='false', aspect='normal',
                    bbox_inches='tight', pad_inches=0)
    except Exception as e:
        logger.error("ML API -> {}".format(e))
    else:
        logger.info('ML API -> Converting to b&w')
        img = Image.open(wd_img_path).convert('LA')
        img.save('./project/server/spectrograms/' + wd + '_gray.png')


def generate_testing_file(wd):
    logger.info('ML API -> Loading b&w')
    img = Image.open('./project/server/spectrograms/' + wd + '_gray.png')
    pix = img.load()

    filename = './project/server/main/testing.scikit'
    logger.info('ML API -> Writing lbp')
    hist = lbp(img, True)  # generate the lbp histogram
    write_scikit(hist, filename)
